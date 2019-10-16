import argparse
import inspect

from pacco.pacco_api import Pacco


class Command:
    def __init__(self, pacco_api):
        self._pacco = pacco_api

    def run(self, *args):
        """HIDDEN
        Entry point for executing commands, dispatcher to class methods.
        """
        command_name = args[0][0]
        commands = self._get_commands()
        method = commands[command_name]
        remaining_args = args[0][1:]
        method(remaining_args)

    def _get_commands(self):
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

    def download(self, *args):
        """
        Download binary by specifying registry.
        """
        parser = argparse.ArgumentParser(prog="pacco download")
        parser.add_argument("registry", help="which registry to download")
        parser.add_argument("-s", "--settings", nargs="*", help="settings for the specified registry")
        args = parser.parse_args(*args)
        self._pacco.download(args.registry, *args.settings)


def main(args):
    pacco_api = Pacco()
    command = Command(pacco_api)
    command.run(args)
