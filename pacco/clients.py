from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import List, Tuple, Type, Optional


class ClientAbstract:
    def ls(self) -> List[str]:
        raise NotImplementedError()

    def rmdir(self, name: str) -> None:
        raise NotImplementedError()

    def dispatch_subdir(self, name: str) -> Type[ClientAbstract]:
        raise NotImplementedError()

    def download_dir(self, download_path: str) -> None:
        raise NotImplementedError()

    def upload_dir(self, dir_path: str) -> None:
        raise NotImplementedError()


class LocalClient(ClientAbstract):
    def __init__(self, path: Optional[str] = "") -> None:
        if path:
            self.__root_dir = path
        else:
            self.__root_dir = os.path.join(str(Path.home()), '.pacco')

    def ls(self) -> List[str]:
        return os.listdir(self.__root_dir)

    def rmdir(self, name: str) -> None:
        shutil.rmtree(os.path.join(self.__root_dir, name))

    def dispatch_subdir(self, name: str) -> LocalClient:
        return LocalClient(os.path.join(self.__root_dir, name))

    def download_dir(self, download_path: str) -> None:
        shutil.copy(self.__root_dir, download_path)

    def upload_dir(self, dir_path: str) -> None:
        shutil.copy(dir_path, self.__root_dir)
