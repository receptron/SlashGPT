from termcolor import colored

from lib.utils.utils import COLOR_DEBUG, COLOR_ERROR, COLOR_INFO, COLOR_WARNING


def print_debug(text):
    print(colored(text, COLOR_DEBUG))


def print_error(text):
    print(colored(text, COLOR_ERROR))


def print_info(text):
    print(colored(text, COLOR_INFO))


def print_warning(text):
    print(colored(text, COLOR_WARNING))
