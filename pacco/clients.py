from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import List, Optional


class FileBasedClientAbstract:
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
    def __init__(self, path: Optional[str] = "") -> None:
        if path:
            self.__root_dir = path
        else:
            self.__root_dir = os.path.join(str(Path.home()), '.pacco')

    def ls(self) -> List[str]:
        return os.listdir(self.__root_dir)

    def rmdir(self, name: str) -> None:
        shutil.rmtree(os.path.join(self.__root_dir, name))

    def mkdir(self, name: str) -> None:
        os.makedirs(os.path.join(self.__root_dir, name))

    def dispatch_subdir(self, name: str) -> LocalClient:
        return LocalClient(os.path.join(self.__root_dir, name))

    def download_dir(self, download_path: str) -> None:
        shutil.copy(self.__root_dir, download_path)

    def upload_dir(self, dir_path: str) -> None:
        shutil.rmtree(self.__root_dir)
        os.makedirs(self.__root_dir)
        shutil.copy(dir_path, self.__root_dir)
