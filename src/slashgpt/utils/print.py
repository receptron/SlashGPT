from termcolor import colored

from slashgpt.utils.utils import COLOR_DEBUG, COLOR_ERROR, COLOR_INFO, COLOR_WARNING


def print_debug(text: str):
    print(colored(text, COLOR_DEBUG))


def print_error(text: str):
    print(colored(text, COLOR_ERROR))


def print_info(text: str):
    print(colored(text, COLOR_INFO))


def print_warning(text: str):
    print(colored(text, COLOR_WARNING))
