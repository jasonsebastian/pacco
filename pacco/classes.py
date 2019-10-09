import json
from typing import Dict, List, Any, Optional

ALLOWED_STRINGS_FILE_NAME = "allowed_settings.txt"


class Client:
    def if_file_exists(self, *path: str) -> bool:
        return True

    def get_file_content(self, *path: str) -> bytes:
        return b'hello world!'


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

        if self.allowed_settings is None:
            self.allowed_settings = self.__get_allowed_settings_from_remote()

    def declare_package(self):
        pass

    def __get_allowed_settings_from_remote(self) -> Dict[str, List[str]]:
        if self.client.if_file_exists(self.name, ALLOWED_STRINGS_FILE_NAME):
            allowed_settings = json.loads(self.client.get_file_content())
            return PackageRegistry.__enforce_type_allowed_settings(allowed_settings)
        else:
            raise ValueError("allowed_settings is not defined and not found in remote")

    @staticmethod
    def __enforce_type_allowed_settings(__settings: Any) -> Dict[str, List[str]]:
        return {str(key): [str(value) for value in values] for key, values in __settings.items()}


