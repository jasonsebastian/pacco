import argparse
import inspect
from typing import Callable, Dict

from pacco.cli.pacco_api import PaccoAPI
from pacco.remote_manager import RemoteManager, ALLOWED_REMOTE_TYPES


class CommandManager:
    def __init__(self, pacco_api):
        self.__pacco = pacco_api
        self.__out = pacco_api.out

    def run(self, *args):
        """
        Entry point for executing commands, dispatcher to class methods.
        """
        try:
            command = args[0]
            remaining_args = args[1:]
            commands = self.__get_commands()
            method = commands[command]
            method(remaining_args)
        except KeyError as exc:
            if command in ["-h", "--help"]:
                self.__show_help()
                return
            if command == "remote":
                Remote(self.__pacco).run(*remaining_args)
                return
            self.__out.writeln("{} is not a pacco command. See 'pacco --help'.".format(str(exc)), error=True)
        except IndexError:  # commands specified
            self.__show_help()

    def __get_commands(self) -> Dict[str, Callable]:
        result = {}
        for method_name, method in inspect.getmembers(self, predicate=inspect.ismethod):
            if not method_name.startswith('_') and method_name not in ["run", "remote"]:
                result[method_name] = method
        return result

    def __show_help(self):
        commands = self.__get_commands()
        max_len = max((len("pacco {}".format(c)) for c in commands)) + 1
        fmt = '  %-{}s'.format(max_len)
        for name in commands:
            appended_name = "pacco {}".format(name)
            print(fmt % appended_name, end="")
            docstring_lines = commands[name].__doc__.split('\n')
            data = []
            for line in docstring_lines:
                line = line.strip()
                data.append(line)
            self.__out.writeln(' '.join(data))
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
        args = parser.parse_args(*args)
        self.__pacco.download(args.registry, args.path, *args.settings)


class Remote:

    def __init__(self, pacco_api):
        self.__pacco = pacco_api
        self.__out = pacco_api.out
        self.__rm = RemoteManager()

    def run(self, *args):
        """
        Entry point for executing commands, dispatcher to class methods.
        """
        try:
            command = args[0]
            commands = self.__get_commands()
            method = commands[command]
            remaining_args = args[1:]
            method(remaining_args)
        except KeyError as exc:
            if command in ["-h", "--help"]:
                self.__show_help()
                return
            self.__out.writeln("pacco remote {} is not a pacco command. See 'pacco remote --help'.".format(str(exc)),
                               error=True)
        except IndexError:  # commands specified
            self.__show_help()

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
            docstring_lines = commands[name].__doc__.split('\n')
            data = []
            for line in docstring_lines:
                line = line.strip()
                data.append(line)
            self.__out.writeln(' '.join(data))
        self.__out.writeln("")
        self.__out.writeln("Pacco remote commands. Type 'pacco remote <command> -h' for help")

    def list(self, *args):
        """
        List existing remotes.
        """
        parser = argparse.ArgumentParser(prog="pacco remote list")
        parser.parse_args(*args)
        remotes = self.__rm.list_remote()
        if not remotes:
            self.__out.writeln("No registered remotes")
        else:
            self.__out.writeln(remotes)

    def add(self, *args):
        """
        Add remote.
        """
        parser = argparse.ArgumentParser(prog="pacco remote add")
        parser.add_argument("name", help="remote name")
        parser.add_argument("type", help="remote type", choices=ALLOWED_REMOTE_TYPES)
        args = parser.parse_args(*args)
        if args.type == "local":
            path = input("Path (if empty, ~/.pacco/ will be used): ")
            self.__rm.add_remote(args.name, {
                "remote_type": "local",
                "path": path
            })
        elif args.type == "nexus_site":
            url = input("URL: ")
            username = input("Username: ")
            from getpass import getpass
            password = getpass()
            self.__rm.add_remote(args.name, {
                "remote_type": "nexus_site",
                "url": url,
                "username": username,
                "password": password
            })


def main(args):
    pacco_api = PaccoAPI()
    CommandManager(pacco_api).run(*args)
