import hashlib
import json
import logging
from typing import Dict, List, Any, Optional

from pacco.nexus_interfaces import Client

ALLOWED_STRINGS_FILE_NAME = "allowed_settings.txt"


class PackageRegistry:
    """
        A PackageRegistry instance represent a package collection and client pair.
        This class shall depend on ``Client`` but not the other way around.

        An instantiation of this class represents the existence or the intend to make exist of the package collection
        ``self.name`` in the client ``self.client``.
    """
    def __init__(self, name: str, client: Client, allowed_settings: Optional[Dict[str, List[str]]] = None) -> None:
        self.name = name
        self.client = client
        self.allowed_settings = allowed_settings
        self.__allowed_settings_file_path = [self.name, ALLOWED_STRINGS_FILE_NAME]
        self.__dir_path = [self.name]

        if self.allowed_settings is None:
            self.allowed_settings = self.__get_allowed_settings_from_remote()

    def declare_package(self):
        if self.client.if_file_exists(self.__allowed_settings_file_path):
            raise FileExistsError("the package is already declared")
        else:
            allowed_settings = json.dumps(self.allowed_settings)
            self.client.write_file(allowed_settings, self.__allowed_settings_file_path)
            logging.info("Package {} declared".format(self.name))

    def delete_package(self, force: Optional[bool] = False):
        if not self.client.if_file_exists(self.__allowed_settings_file_path):
            logging.warning("Intended to delete package {} but it is not declared".format(self.name))
        elif self.client.lsr_dir(self.__dir_path) and not force:
            raise FileExistsError("The package {} is not empty yet".format(self.name))
        else:
            self.client.rm_dir(self.__dir_path)

    def rename_settings(self, mapping: Dict[str, str]):
        pass

    def delete_settings(self, setting: str):
        pass

    def add_settings(self, setting: str, default_value: Optional[str] = ""):
        pass

    def __get_allowed_settings_from_remote(self) -> Dict[str, List[str]]:
        if self.client.if_file_exists(self.__allowed_settings_file_path):
            allowed_settings = json.loads(self.client.get_file_content(self.__allowed_settings_file_path))
            return PackageRegistry.__enforce_type_allowed_settings(allowed_settings)
        else:
            raise FileNotFoundError("allowed_settings is not defined and not found in remote")

    @staticmethod
    def __enforce_type_allowed_settings(__settings: Any) -> Dict[str, List[str]]:
        return {str(key): [str(value) for value in values] for key, values in __settings.items()}


class BinaryPackage:
    def __init__(self, client: Client, settings: Optional[Dict[str, str]] = None) -> None:
        self.client = client
        self.settings = settings
        self.settings_sha = BinaryPackage.__make_sha_from_settings(self.settings)

        self.__settings_file_path = [self.settings_sha, self.settings_sha]
        self.__dir_path = [self.settings_sha]

    def rename_settings(self, mapping: Dict[str, str]):
        pass

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
