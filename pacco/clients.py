from __future__ import annotations

import io
import os
import re
import shutil
from pathlib import Path
from typing import List, Optional

import requests
from bs4 import BeautifulSoup


class ClientAbstract:
    pass


class FileBasedClientAbstract(ClientAbstract):
    """
    An interface for file-based client functionality.
    Each client shall have it's own context of current directory and it must not change throughout the lifetime.
    """
    def ls(self) -> List[str]:
        """
        List down the list of files and directories in it's directory

        Returns:
            list of files and directories as list of string
        """
        raise NotImplementedError()

    def rmdir(self, name: str) -> None:
        """
        Remove a directory recursively. The ``name`` directory must be inside
        this current directory.

        Args:
            name: the name of directory to be deleted
        """
        raise NotImplementedError()

    def mkdir(self, name: str) -> None:
        """
        Create a new directory under the current directory

        Args:
            name: The name of the directory ot be created
        """
        raise NotImplementedError()

    def dispatch_subdir(self, name: str) -> FileBasedClientAbstract:
        """
        Create and return new instance whose context is the join of this current directory with ``name``.

        Args:
            name: the directory name as namespace to the new client
        Return:
            the newly instantiated client
        """
        raise NotImplementedError()

    def download_dir(self, download_path: str) -> None:
        """
        Fetch the file content of this current directory (shall be used only by package binary), and put it
        into the ``download_path``.

        Args:
            download_path: the location destination of the downloaded directory
        """
        raise NotImplementedError()

    def upload_dir(self, dir_path: str) -> None:
        """
        Upload the ``dir_path`` to this current directory by first removing all the content then placing the uploaded
        file.

        Args:
            dir_path: the directory to be uploaded
        """
        raise NotImplementedError()


class LocalClient(FileBasedClientAbstract):
    """
    An implementation of ``FileBasedClientAbstract``, using ``homepath/.pacco`` as the file storage.
    """
    def __init__(self, path: Optional[str] = "", clean: Optional[bool] = False) -> None:
        if path:
            self.__root_dir = path
        else:
            self.__root_dir = os.path.join(str(Path.home()), '.pacco')
            os.makedirs(self.__root_dir, exist_ok=True)
        self.__bin_dir = os.path.join(self.__root_dir, 'bin')

        if clean:
            self.rmdir(self.__root_dir)
            os.makedirs(self.__root_dir)

    def ls(self) -> List[str]:
        return os.listdir(self.__root_dir)

    def rmdir(self, name: str) -> None:
        shutil.rmtree(os.path.join(self.__root_dir, name))

    def mkdir(self, name: str) -> None:
        os.makedirs(os.path.join(self.__root_dir, name))

    def dispatch_subdir(self, name: str) -> LocalClient:
        return LocalClient(os.path.join(self.__root_dir, name))

    def download_dir(self, download_path: str) -> None:
        shutil.copytree(self.__bin_dir, download_path)

    def upload_dir(self, dir_path: str) -> None:
        shutil.rmtree(self.__bin_dir, ignore_errors=True)
        shutil.copytree(dir_path, self.__bin_dir)


class NexusFileClient(FileBasedClientAbstract):
    """
    An implementation of ``FileBasedClientAbstract``, using Nexus site repository as the file storage.
    """
    def __init__(self, url: str, username: str, password: str, clean: Optional[bool] = False) -> None:
        if not re.match(r'https?://(\w+\.)*(\w+)(:\d+)?/(\w+/)*', url):
            raise ValueError("URL not valid, make sure you have trailing slash")
        self.__url = url
        self.__username = username
        self.__password = password
        self.__dummy_stream = io.StringIO(".pacco")

        resp = requests.post(url+".pacco", auth=(self.__username, self.__password), data=self.__dummy_stream)
        if resp.status_code not in [200, 201, 204]:
            raise ConnectionError("Connection seems failed, HTTP status code {}".format(resp.status_code))
        self.__bin_dir = url + 'bin/'

        if clean:
            dir_names = self.ls()
            for dir_name in dir_names:
                self.rmdir(dir_name)

    @staticmethod
    def __validate_status_code(received: int, expected: List[int]) -> None:
        if received not in expected:
            raise ValueError("Receiving http status {}, expecting one of {}".format(received, expected))

    def ls(self) -> List[str]:
        resp = requests.get(self.__url, auth=(self.__username, self.__password))
        NexusFileClient.__validate_status_code(resp.status_code, [200])
        soup = BeautifulSoup(resp.content, 'html.parser')
        content = [str(tr.td.a.text)[:-1] for tr in soup.find_all('tr')[2:]]  # skip table header and parent dir
        return content

    def rmdir(self, name: str) -> None:
        resp = requests.delete(self.__url+name+'/', auth=(self.__username, self.__password))
        NexusFileClient.__validate_status_code(resp.status_code, [200, 204])

    def mkdir(self, name: str) -> None:
        resp = requests.post(self.__url+name+"/.pacco", auth=(self.__username, self.__password),
                             data=self.__dummy_stream)
        NexusFileClient.__validate_status_code(resp.status_code, [200, 201])

    def dispatch_subdir(self, name: str) -> NexusFileClient:
        return NexusFileClient(self.__url+name+'/', self.__username, self.__password)

    def download_dir(self, download_path: str) -> None:
        pass

    def upload_dir(self, dir_path: str) -> None:
        pass
