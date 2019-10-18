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
        >>> open(os.path.join(str(Path.home()), ".pacco_config"), "w").close()
        >>> os.remove(os.path.join(str(Path.home()), ".pacco_config"))
        >>> rm = RemoteManager()
        >>> rm.add_remote('local_test', {'remote_type':'local'})
        >>> rm.list_remote()
        ['local_test']
        >>> rm.add_remote('local_test_2', {'remote_type':'local', 'path': 'storage'})
        >>> sorted(rm.list_remote())
        ['local_test', 'local_test_2']
        >>> rm.set_default(['local_test_2', 'local_test'])
        >>> rm.get_default()
        ['local_test_2', 'local_test']
        >>> rm.delete_remote('local_test')
        Traceback (most recent call last):
        ...
        ValueError: The remote local_test is still in default remote, remove it first
        >>> rm.set_default(['local_test_2'])
        >>> rm.delete_remote('local_test')
        >>> del rm  # auto save
        >>> other_rm = RemoteManager()
        >>> other_rm.list_remote()
        ['local_test_2']
        >>> nexus_remote = other_rm.get_remote('local_test_2')
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
        with open(self.__pacco_config, "w") as f:
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

    def default_download(self, package_name: str, settings_value: Dict[str, str], dir_path: str) -> None:
        """
        Examples:
            >>> import os
            >>> __ = os.system("rm -f ~/.pacco_config")
            >>> __ = os.system('rm -rf download_folder download_folder2 local3 pacco_storage tempfolder ~/.pacco')
            >>> rm = RemoteManager()
            >>> rm.add_remote('local', {'remote_type': 'local'})
            >>> pm = rm.get_remote('local').package_manager
            >>> pm.add_package_registry('openssl', ['os'])
            PR[openssl, os]
            >>> pr = pm.get_package_registry('openssl')
            >>> pr.add_package_binary({'os': 'osx'})
            PackageBinaryObject
            >>> pb = pr.get_package_binary({'os': 'osx'})
            >>> os.makedirs('tempfolder')
            >>> open("tempfolder/testfile", "w").close()
            >>> pb.upload_content('tempfolder')
            >>> rm.add_remote('local2', {'remote_type': 'local', 'path': 'pacco_storage'})
            >>> pm2 = rm.get_remote('local2').package_manager
            >>> pm2.add_package_registry('openssl', ['os'])
            PR[openssl, os]
            >>> rm.add_remote('local3', {'remote_type': 'local', 'path': 'local3'})
            >>> rm.set_default(['local2', 'local3', 'local'])
            >>> rm.default_download('openssl', {'os': 'osx'}, 'download_folder')
            >>> os.listdir('download_folder')
            ['testfile']
            >>> rm.set_default(['local', 'local3'])
            >>> rm.default_download('openssl', {'os': 'osx'}, 'download_folder2')
            >>> os.listdir('download_folder2')
            ['testfile']
            >>> rm.set_default(['local3'])
            >>> rm.default_download('openssl', {'os': 'osx'}, 'download_folder3')
            Traceback (most recent call last):
            ...
            FileNotFoundError: Such binary does not exist in any remotes in the default remote list
            >>> __ = os.system('rm -rf download_folder download_folder2 local3 pacco_storage tempfolder ~/.pacco')
        """
        for remote_name in self.default_remotes:
            remote = self.get_remote(remote_name)
            if package_name in remote.package_manager.list_package_registries():
                pr = remote.package_manager.get_package_registry(package_name)
                try:
                    pb = pr.get_package_binary(settings_value)
                except (KeyError, FileNotFoundError):
                    continue
                else:
                    pb.download_content(dir_path)
                    return
        raise FileNotFoundError("Such binary does not exist in any remotes in the default remote list")
