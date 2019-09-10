import argparse
import os
import sys
import re

ansi_escape = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')


def read_from_stdin():
    """Reads and sanitizes input from stdin

    Returns:
        A list of strings
    """
    if not sys.stdin.isatty():
        stdin = [t.strip('\n') for t in sys.stdin]
        stdin = [ansi_escape.sub('', t) for t in stdin]
        stdin = [t for t in stdin if t]

        return stdin


class ResolvePathAction(argparse.Action):
    """Action to resolve paths and expand environment variables"""
    def __call__(self, parser, namespace, values, option_string=None):
        if isinstance(values, list):
            fullpath = [os.path.expanduser(v) for v in values]
        else:
            fullpath = os.path.expanduser(values)

        setattr(namespace, self.dest, fullpath)


class Parser(argparse.ArgumentParser):
    """Simple wrapper class to provide help on error"""
    def error(self, message):
        sys.stderr.write(f'{self.prog} error: {message}\n')
        self.print_help()
        sys.exit(1)
