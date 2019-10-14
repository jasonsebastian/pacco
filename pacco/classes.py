from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from pacco.clients import FileBasedClientAbstract


class PackageManager:
    """
    Represent the existence of the manager in a remote

    Examples:
        >>> from pacco.clients import LocalClient
        >>> LocalClient().rmdir('')  # clean the .pacco directory
        >>> client = LocalClient()
        >>> pm = PackageManager(client)
        >>> pm.list_package_registries()
        []
        >>> pm.add_package_registry('openssl', ['os', 'compiler', 'version'])
        PR[openssl, compiler, os, version]
        >>> pm.add_package_registry('boost', ['os', 'target', 'type'])
        PR[boost, os, target, type]
        >>> pm.add_package_registry('openssl', ['os', 'compiler', 'version'])
        Traceback (most recent call last):
            ...
        FileExistsError: The package registry openssl is already found
        >>> pm.list_package_registries()
        [('boost', PR[boost, os, target, type]), ('openssl', PR[openssl, compiler, os, version])]
        >>> pm.delete_package_registry('openssl')
        >>> pm.list_package_registries()
        [('boost', PR[boost, os, target, type])]
    """
    def __init__(self, client: FileBasedClientAbstract):
        self.client = client

    def list_package_registries(self) -> List[Tuple[str, PackageRegistry]]:
        """
        List package registries in this package manager.

        Returns:
            The list of package registry name and package registry object tuples
        """
        dir_names = self.client.ls()
        return sorted([(dir_name, PackageRegistry(dir_name, self.client.dispatch_subdir(dir_name)))
                       for dir_name in dir_names], key=lambda x: x[0])

    def delete_package_registry(self, name: str) -> None:
        """
        Delete a package registry from the package manager.

        Args:
            name: the name of the package registry to be deleted.
        """
        self.client.rmdir(name)

    def add_package_registry(self, name: str, settings_key: List[str]) -> PackageRegistry:
        """
        Add a new package registry to this package manager.

        Args:
            name: the name of the package. For printing purposes only.
            settings_key: the list of keys for the configuration parameter, e.g. ['os', 'compiler', 'version']
        Returns:
            The package registry object.
        Exception:
            FileExistsError: raised if the package with the same name is found
        """
        dirs = self.client.ls()
        if name in dirs:
            raise FileExistsError("The package registry {} is already found".format(name))
        self.client.mkdir(name)
        return PackageRegistry(name, self.client.dispatch_subdir(name), settings_key)


class PackageRegistry:
    """
    Represent the existence of a package (e.g. openssl) in the package manager
    
    Examples:
        >>> from pacco.clients import LocalClient
        >>> LocalClient().rmdir('')  # clean the .pacco directory
        >>> client = LocalClient()
        >>> pm = PackageManager(client)
        >>> pr = pm.add_package_registry('openssl', ['os', 'compiler', 'version'])
        >>> pr.list_package_binaries()
        []
        >>> pr.add_package_binary({'os':'osx', 'compiler':'clang', 'version':'1.0'})
        ('compiler=clang==os=osx==version=1.0', PackageBinaryObject)
        >>> pr.add_package_binary({'host_os':'osx', 'compiler':'clang', 'version':'1.0'})
        Traceback (most recent call last):
            ...
        KeyError: "wrong settings key: ['compiler', 'host_os', 'version'] is not ['compiler', 'os', 'version']"
        >>> pr.add_package_binary({'os':'osx', 'compiler':'clang', 'version':'1.0'})
        Traceback (most recent call last):
            ...
        FileExistsError: such binary already exist
        >>> pr.list_package_binaries()
        [('compiler=clang==os=osx==version=1.0', PackageBinaryObject)]
        >>> pr.add_package_binary({'os':'linux', 'compiler':'gcc', 'version':'1.0'})
        ('compiler=gcc==os=linux==version=1.0', PackageBinaryObject)
        >>> pr.list_package_binaries()
        [('compiler=clang==os=osx==version=1.0', PackageBinaryObject), \
('compiler=gcc==os=linux==version=1.0', PackageBinaryObject)]
        >>> pr.delete_package_binary({'os':'osx', 'compiler':'clang', 'version':'1.0'})
        >>> pr.list_package_binaries()
        [('compiler=gcc==os=linux==version=1.0', PackageBinaryObject)]
    """
    def __init__(self, name: str, client: FileBasedClientAbstract, settings_key: Optional[List[str]] = None):
        self.name = name
        self.client = client
        from_remote = self.__get_settings_key()
        if settings_key is None and from_remote is None:
            raise FileNotFoundError("declare settings_key")
        elif from_remote is not None:  # ignore the passed settings_key and use the remote one
            self.settings_key = from_remote
        else:
            self.settings_key = settings_key
            self.client.mkdir(self.__generate_settings_key_dir_name(self.settings_key))

    def __repr__(self):
        return "PR[{}, {}]".format(self.name, ', '.join(sorted(self.settings_key)))

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

    def list_package_binaries(self) -> List[Tuple[str, PackageBinary]]:
        """
        List the package binaries registered in this package registry

        Returns:
            list of tuples of the package binary name and object
        """
        dirs = self.client.ls()
        dirs.remove(self.__generate_settings_key_dir_name(self.settings_key))
        return sorted([(name, PackageBinary(self.client.dispatch_subdir(name))) for name in dirs], key=lambda x: x[0])

    def add_package_binary(self, settings_value: Dict[str, str]) -> Tuple[str, PackageBinary]:
        """
        Add a new package binary to this registry. Note that this will only declare the existance of the binary
        by creating a new directory, to upload the binary must be done through the ``PackageBinary`` object itself.

        Args:
            settings_value: the assignment of key value of the settings_key.
        Returns:
            The tuple of the name of the directory name (serialized version of the configuration) and the object
        Exceptions:
            KeyError: raised if the set of keys in the passed ``settings_value`` is different with ``settings_key``
            FileExistsError: raised if a package binary with the same configuration already exist.
        """
        if set(settings_value.keys()) != set(self.settings_key):
            raise KeyError("wrong settings key: {} is not {}".format(sorted(settings_value.keys()),
                                                                     sorted(self.settings_key)))
        dir_name = PackageRegistry.__generate_dir_name_from_settings_value(settings_value)
        if dir_name in self.client.ls():
            raise FileExistsError("such binary already exist")
        self.client.mkdir(dir_name)
        return dir_name, PackageBinary(self.client.dispatch_subdir(dir_name))

    def delete_package_binary(self, settings_value: Dict[str, str]):
        """
        Delete the package binary folder

        Args:
            settings_value: the configuration of the the package binary to be deleted
        """
        dir_name = PackageRegistry.__generate_dir_name_from_settings_value(settings_value)
        self.client.rmdir(dir_name)


class PackageBinary:
    """
        Represent the existence of a package (e.g. openssl) in the package manager

        Examples:
            >>> from pacco.clients import LocalClient
            >>> LocalClient().rmdir('')  # clean the .pacco directory
            >>> client = LocalClient()
            >>> pm = PackageManager(client)
            >>> pr = pm.add_package_registry('openssl', ['os', 'compiler', 'version'])
            >>> name, pb = pr.add_package_binary({'os':'osx', 'compiler':'clang', 'version':'1.0'})
            >>> import os, shutil
            >>> os.makedirs('testfolder', exist_ok=True)
            >>> open('testfolder/testfile', 'w').close()
            >>> pb.upload_content('testfolder')
            >>> shutil.rmtree('testfolder')
            >>> os.listdir('testfolder')
            Traceback (most recent call last):
                ...
            FileNotFoundError: [Errno 2] No such file or directory: 'testfolder'
            >>> pb.download_content('testfolder')
            >>> os.listdir('testfolder')
            ['testfile']
            >>> shutil.rmtree('testfolder')
    """
    def __init__(self, client: FileBasedClientAbstract):
        self.client = client

    def __repr__(self):
        return "PackageBinaryObject"

    def download_content(self, download_dir_path: str) -> None:
        """
        Download content of uploaded binary from the remote to the ``download_dir_path``

        Args:
            download_dir_path: the destination of download
        """
        self.client.download_dir(download_dir_path)

    def upload_content(self, dir_path: str) -> None:
        """
        Remove the previous binary and upload the content of ``dir_path`` to the remote.

        Args:
            dir_path: the path to the directory to be uploaded
        """
        self.client.upload_dir(dir_path)
