from __future__ import annotations

import os
import shutil
from typing import List, Tuple, Type


class ClientAbstract:
    def ls(self) -> List[str]:
        raise NotImplementedError()

    def rmdir(self, name: str) -> List[str]:
        raise NotImplementedError()

    def dispatch_subdir(self, name: str) -> Type[ClientAbstract]:
        raise NotImplementedError()

    def download_dir(self, download_path: str) -> None:
        raise NotImplementedError()

    def upload_dir(self, dir_path: str) -> None:
        raise NotImplementedError()


class LocalClient(ClientAbstract):
    def __init__(self, dir_name: str) -> None:
        self.__dir_name = dir_name
        self.__root_dir = os.getcwd()
        os.chdir(os.path.join(self.__root_dir, self.__dir_name))

    def ls(self) -> List[str]:
        return os.listdir(os.getcwd())

    def rmdir(self, name: str) -> List[str]:
        shutil.rmdir(os.path.join(self.__root_dir, name))

    def dispatch_subdir(self, name: str) -> Type[ClientAbstract]:
        os.chdir(os.path.join(self.__root_dir, self.))


    def download_dir(self, download_path: str) -> None:
        raise NotImplementedError()

    def upload_dir(self, dir_path: str) -> None:
        raise NotImplementedError()