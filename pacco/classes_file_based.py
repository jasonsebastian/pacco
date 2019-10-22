from __future__ import annotations

import os
import random
import re
import string
from typing import List, Optional, Dict

from pacco.classes_interface import PackageManager, PackageRegistry, PackageBinary
from pacco.clients import FileBasedClientAbstract


class PackageManagerFileBased(PackageManager):
    """
    An implementation of the PackageManager interface

    Examples:
        >>> from pacco.clients import LocalClient, NexusFileClient
        >>> client = LocalClient(clean=True)
        >>> if 'NEXUS_URL' in os.environ: client = NexusFileClient(os.environ['NEXUS_URL'], 'admin', 'admin123', clean=True)
        >>> pm = PackageManagerFileBased(client)
        >>> pm.list_package_registries()
        []
        >>> pm.add_package_registry('openssl', ['os', 'compiler', 'version'])
        >>> pm.add_package_registry('boost', ['os', 'target', 'type'])
        >>> pm.add_package_registry('openssl', ['os', 'compiler', 'version'])
        Traceback (most recent call last):
            ...
        FileExistsError: The package registry openssl is already found
        >>> pm.list_package_registries()
        ['boost', 'openssl']
        >>> pm.remove_package_registry('openssl')
        >>> pm.list_package_registries()
        ['boost']
        >>> pm.get_package_registry('boost')
        PR[boost, os, target, type]
    """
    def __init__(self, client: FileBasedClientAbstract):
        if not isinstance(client, FileBasedClientAbstract):
            raise TypeError("Must be using FileBasedClient")
        super(PackageManagerFileBased, self).__init__(client)

    def list_package_registries(self) -> List[str]:
        return sorted(self.client.ls())

    def remove_package_registry(self, name: str) -> None:
        self.client.rmdir(name)

    def add_package_registry(self, name: str, settings_key: List[str]) -> None:
        dirs = self.client.ls()
        if name in dirs:
            raise FileExistsError("The package registry {} is already found".format(name))
        self.client.mkdir(name)
        PackageRegistryFileBased(name, self.client.dispatch_subdir(name), settings_key)
        return

    def get_package_registry(self, name: str) -> PackageRegistryFileBased:
        dirs = self.client.ls()
        if name not in dirs:
            raise FileNotFoundError("The package registry {} is not found".format(name))
        return PackageRegistryFileBased(name, self.client.dispatch_subdir(name))

    def __repr__(self):
        return "PackageManagerObject"


#TODO: assignment seems to be more appropriate than assignments
class PackageRegistryFileBased(PackageRegistry):
    """
    An implementation of the PackageRegistry interface

    Examples:
        >>> from pacco.clients import LocalClient, NexusFileClient
        >>> client = LocalClient(clean=True)
        >>> if 'NEXUS_URL' in os.environ: client = NexusFileClient(os.environ['NEXUS_URL'], 'admin', 'admin123', clean=True)
        >>> pm = PackageManagerFileBased(client)
        >>> pm.add_package_registry('openssl', ['os', 'compiler', 'version'])
        >>> pr = pm.get_package_registry('openssl')
        >>> pr.list_package_binaries()
        []
        >>> pr.add_package_binary({'os':'osx', 'compiler':'clang', 'version':'1.0'})
        >>> pr.add_package_binary({'host_os':'osx', 'compiler':'clang', 'version':'1.0'})
        Traceback (most recent call last):
            ...
        KeyError: "wrong settings key: ['compiler', 'host_os', 'version'] is not ['compiler', 'os', 'version']"
        >>> pr.add_package_binary({'os':'osx', 'compiler':'clang', 'version':'1.0'})
        Traceback (most recent call last):
            ...
        FileExistsError: such binary already exist
        >>> len(pr.list_package_binaries())
        1
        >>> pr.add_package_binary({'os':'linux', 'compiler':'gcc', 'version':'1.0'})
        >>> len(pr.list_package_binaries())
        2
        >>> pr.remove_package_binary({'os':'osx', 'compiler':'clang', 'version':'1.0'})
        >>> len(pr.list_package_binaries())
        1
        >>> pr.get_package_binary({'os':'linux', 'compiler':'gcc', 'version':'1.0'})
        PackageBinaryObject
    """
    __params_prefix = '__params'

    def __init__(self, name: str, client: FileBasedClientAbstract, params: Optional[List[str]] = None):
        if not isinstance(client, FileBasedClientAbstract):
            raise TypeError("Must be using FileBasedClient")
        super(PackageRegistryFileBased, self).__init__(name, client, params)

        remote_params = self.__get_remote_params()
        if params is None and remote_params is None:
            raise FileNotFoundError("you need to declare params if you are adding, if you are getting, this"
                                    "means that the package registry is not properly set, you need to delete and"
                                    "add again")
        elif remote_params is not None:  # ignore the passed params and use the remote one
            self.params = remote_params
        else:
            self.params = params
            self.client.mkdir(self.__serialize_params(self.params))

    def __repr__(self):
        return "PR[{}, {}]".format(self.name, ', '.join(sorted(self.params)))

    def __get_remote_params(self) -> Optional[List[str]]:
        params = None
        dirs = self.client.ls()
        for dir_name in dirs:
            if PackageRegistryFileBased.__params_prefix in dir_name:
                params = dir_name.split('==')[1:]
        return params

    @staticmethod
    def __serialize_params(params: List[str]) -> str:
        params = sorted(params)
        return '=='.join([PackageRegistryFileBased.__params_prefix] + params)

    @staticmethod
    def __serialize_assignments(assignments: Dict[str, str]) -> str:
        sorted_assignments_tuple = sorted(assignments.items(), key=lambda x: x[0])
        zipped_assignments = ['='.join(pair) for pair in sorted_assignments_tuple]
        return '=='.join(zipped_assignments)

    @staticmethod
    def __unserialize_assignments(dir_name: str) -> Dict[str, str]:
        if not re.match(r"((\w+=\w+)==)*(\w+=\w+)", dir_name):
            raise ValueError("Invalid dir_name syntax {}".format(dir_name))
        return {arg.split('=')[0]: arg.split('=')[1] for arg in dir_name.split('==')}

    def __get_serialized_assignments_to_wrapper_mapping(self):
        dir_names = self.client.ls()
        dir_names.remove(self.__serialize_params(self.params))

        mapping = {}
        for dir_name in dir_names:
            sub_dirs = self.client.dispatch_subdir(dir_name).ls()
            if 'bin' in sub_dirs:
                sub_dirs.remove('bin')
            serialized_assignments = sub_dirs[0]
            mapping[serialized_assignments] = dir_name

        return mapping

    def list_package_binaries(self) -> List[Dict[str, str]]:
        return [PackageRegistryFileBased.__unserialize_assignments(serialized_assignments)
                for serialized_assignments in self.__get_serialized_assignments_to_wrapper_mapping()]

    @staticmethod
    def __random_string(length: int) -> str:
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

    def add_package_binary(self, assignments: Dict[str, str]) -> None:
        if set(assignments.keys()) != set(self.params):
            raise KeyError("wrong settings key: {} is not {}".format(sorted(assignments.keys()),
                                                                     sorted(self.params)))

        serialized_assignments = PackageRegistryFileBased.__serialize_assignments(assignments)
        mapping = self.__get_serialized_assignments_to_wrapper_mapping()
        if serialized_assignments in mapping:
            raise FileExistsError("such binary already exist")

        new_random_dir_name = PackageRegistryFileBased.__random_string(10)
        if new_random_dir_name in mapping.values():
            new_random_dir_name = PackageRegistryFileBased.__random_string(10)

        self.client.mkdir(new_random_dir_name)
        self.client.dispatch_subdir(new_random_dir_name).mkdir(serialized_assignments)
        return

    def remove_package_binary(self, assignments: Dict[str, str]):
        self.client.rmdir(self.__get_serialized_assignments_to_wrapper_mapping()[
                              PackageRegistryFileBased.__serialize_assignments(assignments)
                          ])

    def get_package_binary(self, assignments: Dict[str, str]) -> PackageBinaryFileBased:
        serialized_assignments = PackageRegistryFileBased.__serialize_assignments(assignments)
        if set(assignments.keys()) != set(self.params):
            raise KeyError("wrong settings key: {} is not {}".format(sorted(assignments.keys()),
                                                                     sorted(self.params)))
        if serialized_assignments not in self.__get_serialized_assignments_to_wrapper_mapping():
            raise FileNotFoundError("such configuration does not exist")
        return PackageBinaryFileBased(
            self.client.dispatch_subdir(
                self.__get_serialized_assignments_to_wrapper_mapping()[serialized_assignments]
            )
        )


class PackageBinaryFileBased(PackageBinary):
    """
    An implementation of the PackageBinary interface

    Examples:
        >>> from pacco.clients import LocalClient, NexusFileClient
        >>> client = LocalClient(clean=True)
        >>> if 'NEXUS_URL' in os.environ: client = NexusFileClient(os.environ['NEXUS_URL'], 'admin', 'admin123', clean=True)
        >>> pm = PackageManagerFileBased(client)
        >>> pm.add_package_registry('openssl', ['os', 'compiler', 'version'])
        >>> pr = pm.get_package_registry('openssl')
        >>> pr.add_package_binary({'os':'osx', 'compiler':'clang', 'version':'1.0'})
        >>> pb = pr.get_package_binary({'os':'osx', 'compiler':'clang', 'version':'1.0'})
        >>> import os, shutil
        >>> os.makedirs('testfolder', exist_ok=True)
        >>> open('testfolder/testfile', 'w').close()
        >>> pb.upload_content('testfolder')
        >>> __ = shutil.move('testfolder/testfile', 'testfolder/testfile2')
        >>> pb_get = pr.get_package_binary({'os':'osx', 'compiler':'clang', 'version':'1.0'})  # use a new reference
        >>> pb_get.download_content('testfolder')
        >>> sorted(os.listdir('testfolder'))
        ['testfile', 'testfile2']
        >>> shutil.rmtree('testfolder')
    """

    def __init__(self, client: FileBasedClientAbstract):
        if not isinstance(client, FileBasedClientAbstract):
            raise TypeError("Must be using FileBasedClient")
        super(PackageBinaryFileBased, self).__init__(client)

    def __repr__(self):
        return "PackageBinaryObject"

    def download_content(self, download_dir_path: str) -> None:
        self.client.download_dir(download_dir_path)

    def upload_content(self, dir_path: str) -> None:
        self.client.upload_dir(dir_path)
