import argparse
import inspect
import re
from typing import Callable, Dict

from pacco.cli.output_stream import OutputStream
from pacco.remote_manager import RemoteManager, ALLOWED_REMOTE_TYPES


class CommandManager:
    def __init__(self):
        self.__out = OutputStream()
        self.__rm = RemoteManager()

    def run(self, *args):
        """
        Entry point for executing commands, dispatcher to class methods.
        """
        if not args:
            self.__show_help()
            return
        command = args[0]
        remaining_args = args[1:]
        commands = self.__get_commands()
        if command not in commands:
            if command in ["-h", "--help"]:
                self.__show_help()
                return
            self.__out.writeln("'pacco {}' is an invalid command. See 'pacco --help'.".format(command), error=True)
            return
        method = commands[command]
        method(*remaining_args)

    def __get_commands(self) -> Dict[str, Callable]:
        result = {}
        for method_name, method in inspect.getmembers(self, predicate=inspect.ismethod):
            if not method_name.startswith('_') and method_name not in ["run"]:
                result[method_name] = method
        return result

    def __show_help(self):
        commands = self.__get_commands()
        max_len = max((len("pacco {}".format(c)) for c in commands)) + 1
        fmt = '  %-{}s'.format(max_len)
        for name in commands:
            appended_name = "pacco {}".format(name)
            print(fmt % appended_name, end="")
            if commands[name].__doc__:
                docstring_lines = commands[name].__doc__.split('\n')
                data = []
                for line in docstring_lines:
                    line = line.strip()
                    data.append(line)
                self.__out.writeln(' '.join(data))
            else:
                self.__out.writeln("")  # Empty docs
        self.__out.writeln("")
        self.__out.writeln("Pacco commands. Type 'pacco <command> -h' for help")

    def download(self, *args: str):
        """
        Download binary by specifying registry, path and settings.
        """
        parser = argparse.ArgumentParser(prog="pacco download")
        parser.add_argument("registry", help="which registry to download")
        parser.add_argument("path", help="path to download registry")
        parser.add_argument("settings", nargs="+", help="settings for the specified registry")
        parsed_args = parser.parse_args(args)
        self.__pacco.download(parsed_args.registry, parsed_args.path, *parsed_args.settings)

    def remote(self, *args: str):
        Remote(self.__out, self.__rm).run(*args)

    def registry(self, *args: str):
        Registry(self.__out, self.__rm).run(*args)


class Remote:
    def __init__(self, output: OutputStream, remote_manager: RemoteManager):
        self.__out = output
        self.__rm = remote_manager

    def run(self, *args):
        """
        Entry point for executing commands, dispatcher to class methods.
        """
        if not args:
            self.__show_help()
            return
        command = args[0]
        remaining_args = args[1:]
        commands = self.__get_commands()
        if command not in commands:
            if command in ["-h", "--help"]:
                self.__show_help()
                return
            self.__out.writeln("'pacco remote {}' is an invalid command. See 'pacco remote --help'.".format(command),
                               error=True)
            return
        method = commands[command]
        method(*remaining_args)

    def __get_commands(self) -> Dict[str, Callable]:
        result = {}
        for method_name, method in inspect.getmembers(self, predicate=inspect.ismethod):
            if not method_name.startswith('_') and method_name not in ["run"]:
                result[method_name] = method
        return result

    def __show_help(self):
        commands = self.__get_commands()
        max_len = max((len("pacco remote {}".format(c)) for c in commands)) + 1
        fmt = '  %-{}s'.format(max_len)
        for name in commands:
            appended_name = "pacco remote {}".format(name)
            print(fmt % appended_name, end="")
            if commands[name].__doc__:
                docstring_lines = commands[name].__doc__.split('\n')
                data = []
                for line in docstring_lines:
                    line = line.strip()
                    data.append(line)
                self.__out.writeln(' '.join(data))
            else:
                self.__out.writeln("")  # Empty docs
        self.__out.writeln("")
        self.__out.writeln("Pacco remote commands. Type 'pacco remote <command> -h' for help")

    def list(self, *args):
        """
        List existing remotes.
        """
        parser = argparse.ArgumentParser(prog="pacco remote list")
        parser.parse_args(args)
        remotes = self.__rm.list_remote()
        if not remotes:
            self.__out.writeln("No registered remotes")
        else:
            self.__out.writeln(remotes)

    def add(self, *args):
        """
        Add a remote.
        """
        parser = argparse.ArgumentParser(prog="pacco remote add")
        parser.add_argument("name", help="remote name")
        parser.add_argument("type", help="remote type", choices=ALLOWED_REMOTE_TYPES)
        parsed_args = parser.parse_args(args)
        if parsed_args.type == "local":
            path = input("Path (if empty, ~/.pacco/ will be used): ")
            self.__rm.add_remote(parsed_args.name, {
                "remote_type": "local",
                "path": path
            })
        elif parsed_args.type == "nexus_site":
            url = input("URL: ")
            username = input("Username: ")
            from getpass import getpass
            password = getpass()
            self.__rm.add_remote(parsed_args.name, {
                "remote_type": "nexus_site",
                "url": url,
                "username": username,
                "password": password
            })

    def remove(self, *args):
        """
        Remove a remote.
        """
        parser = argparse.ArgumentParser(prog="pacco remote remove")
        parser.add_argument("name", help="remote name")
        parsed_args = parser.parse_args(args)
        self.__rm.delete_remote(parsed_args.name)

    def set_default(self, *args):
        """
        Set default remote(s).
        """
        parser = argparse.ArgumentParser(prog="pacco remote set_default")
        parser.add_argument("name", nargs="*", help="remote name")
        parsed_args = parser.parse_args(args)
        self.__rm.set_default(parsed_args.name)

    def print_default(self, *args):
        """
        Print default remote(s).
        """
        parser = argparse.ArgumentParser(prog="pacco remote print_default")
        parser.parse_args(args)
        default_remotes = self.__rm.get_default()
        self.__out.writeln(default_remotes)


class Registry:
    def __init__(self, output: OutputStream, remote_manager: RemoteManager):
        self.__out = output
        self.__rm = remote_manager

    def run(self, *args):
        """
        Entry point for executing commands, dispatcher to class methods.
        """
        if not args:
            self.__show_help()
            return
        command = args[0]
        remaining_args = args[1:]
        commands = self.__get_commands()
        if command not in commands:
            if command in ["-h", "--help"]:
                self.__show_help()
                return
            self.__out.writeln(
                "'pacco registry {}' is an invalid command. See 'pacco registry --help'.".format(command),
                error=True)
            return
        method = commands[command]
        method(*remaining_args)

    def __get_commands(self) -> Dict[str, Callable]:
        result = {}
        for method_name, method in inspect.getmembers(self, predicate=inspect.ismethod):
            if not method_name.startswith('_') and method_name not in ["run"]:
                result[method_name] = method
        return result

    def __show_help(self):
        commands = self.__get_commands()
        max_len = max((len("pacco registry {}".format(c)) for c in commands)) + 1
        fmt = '  %-{}s'.format(max_len)
        for name in commands:
            appended_name = "pacco registry {}".format(name)
            print(fmt % appended_name, end="")
            if commands[name].__doc__:
                docstring_lines = commands[name].__doc__.split('\n')
                data = []
                for line in docstring_lines:
                    line = line.strip()
                    data.append(line)
                self.__out.writeln(' '.join(data))
            else:
                self.__out.writeln("")  # Empty docs
        self.__out.writeln("")
        self.__out.writeln("Pacco registry commands. Type 'pacco registry <command> -h' for help")

    def list(self, *args):
        """
        List registries of a remote.
        """
        parser = argparse.ArgumentParser(prog="pacco registry list")
        parser.add_argument("remote", help="remote name")
        parsed_args = parser.parse_args(args)
        pm = self.__rm.get_remote(parsed_args.remote)
        self.__out.writeln(pm.list_package_registries())

    def add(self, *args):
        """
        Add registry to remote.
        """
        parser = argparse.ArgumentParser(prog="pacco registry add")
        parser.add_argument("remote", help="remote name")
        parser.add_argument("name", help="registry name")
        parser.add_argument("settings", help="settings key (e.g. os,version,obfuscation)")
        parsed_args = parser.parse_args(args)
        if not re.match(r"([(\w)-.]+,)*([(\w)-.]+),?", parsed_args.settings):
            raise ValueError("Settings must be in the form of ([(\\w)-.]+,)*([(\\w)-.]+),?")
        pm = self.__rm.get_remote(parsed_args.remote)
        pm.add_package_registry(parsed_args.name, parsed_args.settings.split(","))

    def delete(self, *args):
        """
        Delete a registry from a specific remote.
        """
        parser = argparse.ArgumentParser(prog="pacco registry delete")
        parser.add_argument("remote", help="remote name")
        parser.add_argument("name", help="registry name")
        parsed_args = parser.parse_args(args)
        pm = self.__rm.get_remote(parsed_args.remote)
        pm.delete_package_registry(parsed_args.name)

    def binaries(self, *args):
        """
        List binaries of a registry from a specific remote.
        """
        parser = argparse.ArgumentParser(prog="pacco registry delete")
        parser.add_argument("remote", help="remote name")
        parser.add_argument("name", help="registry name")
        parsed_args = parser.parse_args(args)
        pm = self.__rm.get_remote(parsed_args.remote)
        pr = pm.get_package_registry(parsed_args.name)
        self.__out.writeln(pr.list_package_binaries())


def main(args):
    CommandManager().run(*args)
