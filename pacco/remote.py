from __future__ import annotations

from typing import Dict, Optional

from pacco.classes_file_based import PackageManagerFileBased
from pacco.clients import LocalClient, NexusFileClient, FileBasedClientAbstract


class Remote:
    def __init__(self, name: str, remote_type: str, client: FileBasedClientAbstract):
        self.name = name
        self.remote_type = remote_type
        self.package_manager = PackageManagerFileBased(client)

    def __str__(self):
        return "[{}, {}]".format(self.name, self.remote_type)

    @staticmethod
    def create(name: str, serialized: Dict[str, str]) -> Remote:
        raise NotImplementedError()

    def serialize(self) -> Dict[str, str]:
        raise NotImplementedError()


class LocalRemote(Remote):
    def __init__(self, name: str, remote_type: str, path: Optional[str] = "", clean: Optional[bool] = False):
        if path:
            self.__path = os.path.abspath(path)
        else:
            self.__path = ""
        client = LocalClient(self.__path, clean)
        super(LocalRemote, self).__init__(name, remote_type, client)

    @staticmethod
    def create(name: str, serialized: Dict[str, str]) -> LocalRemote:
        if 'path' not in serialized:
            serialized['path'] = ""
        return LocalRemote(name, serialized['remote_type'], serialized['path'])

    def serialize(self) -> Dict[str, str]:
        return {'remote_type': 'local', 'path': self.__path}


class NexusSiteRemote(Remote):
    def __init__(self, name: str, remote_type: str, url: str, username: str, password: str,
                 clean: Optional[bool] = False):
        self.__url = url
        self.__username = username
        self.__password = password
        client = NexusFileClient(url, username, password, clean)
        super(NexusSiteRemote, self).__init__(name, remote_type, client)

    @staticmethod
    def create(name: str, serialized: Dict[str, str]) -> NexusSiteRemote:
        return NexusSiteRemote(name, serialized['remote_type'], serialized['url'],
                               serialized['username'], serialized['password'])

    def serialize(self) -> Dict[str, str]:
        return {'remote_type': 'nexus_site', 'url': self.__url,
                'username': self.__username, 'password': self.__password}
