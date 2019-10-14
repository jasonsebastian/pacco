"""
    This module shall contain the representation of object
    ``PackageRegistry`` represent a package collection and client pair.
    ``BinaryPackage`` represent a binary based on the setting in a ``PackageRegistry``.
    ``BinaryPackage`` shall not know which ``PackageRegistry`` it is in. To make this happen, we change the working
    directory of client to be inside the ``PackageRegistry``.

    The dependency graph of the modules related composed of
    ``PackageRegistry ---> Client``
    ``BinaryRegistry ---> Client``
    ``PackageRegistry ---> BinaryRegistry``
"""

import hashlib
import json
import logging
from typing import Dict, List, Any, Optional

from pacco.clients import LocalClient

ALLOWED_STRINGS_FILE_NAME = "allowed_settings.txt"


class PackageRegistry:
    """
        An instantiation of this class represents the existence of the package collection
        ``self.name`` in the client ``self.client``.

        There is two way to instantiate the PackageRegistry, with or without ``allowed_settings``
        If it is with ``allowed_settings``, it will take the ``allowed_settings`` as the setting, and will try to
        set up a new package if it's not set up, or if the package already exist, will check if the settings is equal
        else it will raise warning and use the existing ``allowed_settings`` version.

        Thus, only use the ``allowed_settings`` options when creating new package registry.

    """
    def __init__(self, name: str, client:LocalClient, allowed_settings: Optional[Dict[str, List[str]]] = None) -> None:
        """
            Attributes:
                name: the name of the package
                allowed_settings: the list of allowed values for all settings option
            Args:
                name: the name of the package
                client: the client object as the cursor to remote repository
                allowed_settings: the list of allowed values for all settings option
        """
        self.name = name
        self.__client = client
        self.allowed_settings = allowed_settings
        self.__allowed_settings_file_path = [self.name, ALLOWED_STRINGS_FILE_NAME]
        self.__dir_path = [self.name]

        if self.allowed_settings is None:
            self.allowed_settings = self.__get_allowed_settings_from_remote()
        elif self.__client.if_file_exists(self.__allowed_settings_file_path):
            logging.warning("ALLOWED_SETTINGS already exist, will use the existing from remote")
        else:
            self.__declare_package()

    def __del__(self) -> None:
        """
            Delete a package from the remote repository.
        """
        if not self.__client.if_file_exists(self.__allowed_settings_file_path):
            logging.warning("Intended to delete package {} but it is not declared".format(self.name))
        else:
            self.__client.rm_dir(self.__dir_path)

    def __declare_package(self) -> None:
        allowed_settings = json.dumps(self.allowed_settings)
        self.__client.write_file(allowed_settings, self.__allowed_settings_file_path)
        logging.info("Package {} declared".format(self.name))

    def __get_allowed_settings_from_remote(self) -> Dict[str, List[str]]:
        if self.__client.if_file_exists(self.__allowed_settings_file_path):
            allowed_settings = json.loads(self.__client.get_file_content(self.__allowed_settings_file_path))
            return PackageRegistry.__enforce_type_allowed_settings(allowed_settings)
        else:
            raise FileNotFoundError("allowed_settings is not defined and not found in remote")

    @staticmethod
    def __enforce_type_allowed_settings(__settings: Any) -> Dict[str, List[str]]:
        return {str(key): [str(value) for value in values] for key, values in __settings.items()}


class BinaryPackage:
    def __init__(self, client:LocalClient, settings: Optional[Dict[str, str]] = None) -> None:
        self.client = client
        self.settings = settings
        self.settings_sha = BinaryPackage.__make_sha_from_settings(self.settings)

        self.__settings_file_path = [self.settings_sha, self.settings_sha]
        self.__dir_path = [self.settings_sha]

    def delete_settings(self, setting: str):
        pass

    def add_settings(self, setting: str, default_value: Optional[str] = ""):
        pass

    def upload_file(self, file_path: str):
        pass

    def upload_directory(self, dir_path: str):
        pass

    @staticmethod
    def __make_sha_from_settings(settings: Dict[str, str]) -> str:
        jsonyfied = json.dumps(settings, sort_keys=True)
        return str(hashlib.sha256(jsonyfied).digest())

    @staticmethod
    def __enforce_type_settings(__settings: Any) -> Dict[str, str]:
        return {str(key): str(value) for key, value in __settings.items()}
