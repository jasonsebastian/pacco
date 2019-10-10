import json
import logging
from typing import Dict, List, Any, Optional, Tuple

ALLOWED_STRINGS_FILE_NAME = "allowed_settings.txt"


class Client:
    """
    The client shall act like git as in only index files and not directory.
    """
    def if_file_exists(self, file_path: List[str]) -> bool:
        return True

    def get_file_content(self, file_path: List[str]) -> str:
        return 'hello world!'

    def write_file(self, content: str, file_path: List[str]) -> None:
        return

    def lsr_dir(self, dir_path: List[str]) -> List[Tuple[bool, str]]:
        return []

    def rm_dir(self, dir_path: List[str]) -> None:
        """
        rm_dir here means remove recursively all files within the directory
        """
        return


class PackageRegistry(object):
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
        self.__allowed_string_file_path = [self.name, ALLOWED_STRINGS_FILE_NAME]
        self.__dir_path = [self.name]

        if self.allowed_settings is None:
            self.allowed_settings = self.__get_allowed_settings_from_remote()

    def declare_package(self):
        if self.client.if_file_exists(self.__allowed_string_file_path):
            raise FileExistsError("the package is already declared")
        else:
            allowed_settings = json.dumps(self.allowed_settings)
            self.client.write_file(allowed_settings, self.__allowed_string_file_path)
            logging.info("Package {} declared".format(self.name))

    def delete_package(self, force: Optional[bool] = False):
        if not self.client.if_file_exists(self.__allowed_string_file_path):
            logging.warning("Intended to delete package {} but it is not declared".format(self.name))
        elif self.client.lsr_dir(self.__dir_path) and not force:
            raise FileExistsError("The package {} is not empty yet".format(self.name))
        else:
            self.client.rm_dir(self.__dir_path)

    def __get_allowed_settings_from_remote(self) -> Dict[str, List[str]]:
        if self.client.if_file_exists(self.__allowed_string_file_path):
            allowed_settings = json.loads(self.client.get_file_content(self.__allowed_string_file_path))
            return PackageRegistry.__enforce_type_allowed_settings(allowed_settings)
        else:
            raise FileNotFoundError("allowed_settings is not defined and not found in remote")

    @staticmethod
    def __enforce_type_allowed_settings(__settings: Any) -> Dict[str, List[str]]:
        return {str(key): [str(value) for value in values] for key, values in __settings.items()}
