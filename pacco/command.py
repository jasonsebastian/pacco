import argparse
import inspect
from typing import Callable, Dict

from pacco.pacco_api import Pacco


class Command:
    def __init__(self, pacco_api):
        self.__pacco = pacco_api
        self.__out = pacco_api.out

    def run(self, *args):
        """HIDDEN
        Entry point for executing commands, dispatcher to class methods.
        """
        try:
            command = args[0][0]
            commands = self.__get_commands()
            method = commands[command]
            remaining_args = args[0][1:]
            method(remaining_args)
        except KeyError as exc:
            if command in ["-h", "--help"]:
                self.__show_help()
                return
            self.__out.writeln("{} is not a pacco command. See 'pacco --help'.".format(str(exc)), error=True)
        except IndexError:  # commands specified
            self.__show_help()

    def __get_commands(self) -> Dict[str, Callable]:
        """
        Derive the available commands from this class.

        Returns:
             list of available commands
        """
        result = {}
        for m in inspect.getmembers(self, predicate=inspect.ismethod):
            method_name = m[0]
            if not method_name.startswith('_'):
                method = m[1]
                if method.__doc__ and not method.__doc__.startswith('HIDDEN'):
                    result[method_name] = method
        return result

    def __show_help(self):
        commands = self.__get_commands()
        max_len = max((len(c) for c in commands)) + 1
        fmt = '  %-{}s'.format(max_len)
        for name in commands:
            print(fmt % name, end="")
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


def main(args):
    pacco_api = Pacco()
    command = Command(pacco_api)
    command.run(args)
