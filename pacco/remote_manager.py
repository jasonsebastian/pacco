from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List

import yaml

from pacco.remote import LocalRemote, NexusSiteRemote, Remote

ALLOWED_REMOTE_TYPES = [
    'local',
    'nexus_site',
]

DEFAULT_REMOTE_NAME = 'default'


class RemoteManager:
    """
    Function to manage .pacco_config file as the storage for remote lists

    Example:
        >>> os.remove(os.path.join(str(Path.home()), ".pacco_config"))
        >>> rm = RemoteManager()
        >>> rm.add_remote('local_test', {'remote_type':'local'})
        >>> rm.list_remote()
        ['local_test']
        >>> rm.add_remote('nexus', {'remote_type': 'nexus_site', 'url': 'http://localhost:8081/nexus/content/sites/pacco/', 'username': 'admin', 'password': 'admin123'})
        >>> sorted(rm.list_remote())
        ['local_test', 'nexus']
        >>> rm.set_default(['nexus', 'local_test'])
        >>> rm.get_default()
        ['nexus', 'local_test']
        >>> rm.delete_remote('local_test')
        Traceback (most recent call last):
        ...
        ValueError: The remote local_test is still in default remote, remove it first
        >>> rm.set_default(['nexus'])
        >>> rm.delete_remote('local_test')
        >>> del rm  # auto save
        >>> other_rm = RemoteManager()
        >>> other_rm.list_remote()
        ['nexus']
        >>> nexus_remote = other_rm.get_remote('nexus')
        >>> pm = nexus_remote.package_manager
        >>> pm
        PackageManagerObject
    """
    def __init__(self):
        self.__pacco_config = os.path.join(str(Path.home()), '.pacco_config')
        if not os.path.exists(self.__pacco_config):
            self.remotes = {}
            self.default_remotes = []

        else:
            with open(self.__pacco_config, "r") as f:
                pacco_config = yaml.load(f, Loader=yaml.Loader)

            remotes_serialized = pacco_config['remotes']
            default_remotes = pacco_config['default']

            remotes = {name: RemoteManager.__instantiate_remote(name, remotes_serialized[name])
                       for name in remotes_serialized}

            self.remotes = remotes
            self.default_remotes = default_remotes

    def __del__(self):
        self.save()

    def save(self):
        serialized_remotes = {name: self.remotes[name].serialize() for name in self.remotes}
        with open(self.__pacco_config, "x") as f:
            yaml.dump({'remotes': serialized_remotes, 'default': self.default_remotes}, stream=f)

    @staticmethod
    def __instantiate_remote(name: str, serialized):
        if serialized['remote_type'] == 'local':
            return LocalRemote.create(name, serialized)
        elif serialized['remote_type'] == 'nexus_site':
            return NexusSiteRemote.create(name, serialized)
        else:
            raise ValueError("The remote_type {} is not supported, currently only supports [{}]".format(
                serialized['remote_type'], ", ".join(['local', 'nexus_site'])
            ))

    def get_remote(self, name: str) -> Remote:
        if name not in self.remotes:
            raise KeyError("The remote named {} is not found".format(name))
        return self.remotes[name]

    def list_remote(self) -> List[str]:
        return list(self.remotes.keys())

    def add_remote(self, name: str, configuration: Dict[str, str]) -> None:
        if name in self.list_remote():
            raise NameError("The remote with name {} already exists".format(name))
        self.remotes[name] = RemoteManager.__instantiate_remote(name, configuration)

    def delete_remote(self, name: str) -> None:
        if name in self.default_remotes:
            raise ValueError("The remote {} is still in default remote, remove it first".format(name))
        del self.remotes[name]

    def get_default(self) -> List[str]:
        return list(self.default_remotes)

    def set_default(self, remotes: List[str]) -> None:
        for remote in remotes:
            if remote not in self.remotes:
                raise KeyError("Remote {} not exists".format(remote))
        self.default_remotes = remotes
