from __future__ import annotations

from typing import Dict, List, Optional

from pacco.clients import FileBasedClientAbstract


class PackageManager:
    def __init__(self, client: FileBasedClientAbstract):
        self.client = client

    def list_package_registries(self) -> Dict[str, PackageRegistry]:
        dir_names = self.client.ls()
        return {dir_name: PackageRegistry(self.client.dispatch_subdir(dir_name)) for dir_name in dir_names}

    def delete_package_registry(self, name: str):
        self.client.rmdir(name)

    def add_package_registry(self, name: str, settings_key: List[str]) -> PackageRegistry:
        dirs = self.client.ls()
        if name in dirs:
            raise FileExistsError("The package registry {} is already found".format(name))
        self.client.mkdir(name)
        return PackageRegistry(self.client.dispatch_subdir(name), settings_key)


class PackageRegistry:
    def __init__(self, client: FileBasedClientAbstract, settings_key: Optional[List[str]] = None):
        self.client = client
        from_remote = self.__get_settings_key()
        if settings_key is None and from_remote is None:
            raise FileNotFoundError("declare settings_key")
        elif from_remote is not None:  # ignore the passed settings_key and use the remote one
            self.settings_key = from_remote
        else:
            self.settings_key = settings_key
            self.client.mkdir(self.__generate_settings_key_dir_name(self.settings_key))

    def __get_settings_key(self) -> Optional[List[str]]:
        settings_key = None
        dirs = self.client.ls()
        for dir_name in dirs:
            if '__settings_key' in dir_name:
                settings_key = dir_name.split('==')[1:]
        return settings_key

    @staticmethod
    def __generate_settings_key_dir_name(settings_key: List[str]) -> str:
        settings_key = sorted(settings_key)
        return '=='.join(['__settings_key']+settings_key)

    @staticmethod
    def __generate_dir_name_from_settings_value(settings_value: Dict[str, str]) -> str:
        sorted_settings_value_pair = sorted(settings_value.items(), key=lambda x: x[0])
        zipped_assignments = ['='.join(pair) for pair in sorted_settings_value_pair]
        return '=='.join(zipped_assignments)

    @staticmethod
    def __parse_settings_value(dir_name: str) -> Dict[str, str]:
        assignments = dir_name.split('==')
        unzipped_assignments = [(setting.split('=')[0], setting.split('=')[1]) for setting in assignments]
        return {key: value for key, value in unzipped_assignments}

    def list_package_binaries(self) -> Dict[Dict[str, str], PackageBinary]:
        dirs = self.client.ls()
        dirs.remove(self.__generate_settings_key_dir_name(self.settings_key))
        return {PackageRegistry.__parse_settings_value(name): PackageBinary(self.client.dispatch_subdir(name))
                for name in dirs}

    def add_package_binary(self, settings_value: Dict[str, str]) -> PackageBinary:
        dir_name = PackageRegistry.__generate_dir_name_from_settings_value(settings_value)
        self.client.mkdir(dir_name)
        return PackageBinary(self.client.dispatch_subdir(dir_name))

    def delete_package_binary(self, settings_value: Dict[str, str]):
        dir_name = PackageRegistry.__generate_dir_name_from_settings_value(settings_value)
        self.client.rmdir(dir_name)


class PackageBinary:
    def __init__(self, client: FileBasedClientAbstract):
        self.client = client

    def download_content(self, download_path: str) -> None:
        self.client.download_dir(download_path)

    def upload_content(self, dir_path: str) -> None:
        self.client.rmdir('')
        self.client.mkdir('')
        self.client.upload_dir(dir_path)
