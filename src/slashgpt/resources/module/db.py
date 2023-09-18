from termcolor import colored


def query(sql: str):
    print(colored(f"SQL: {sql}", "yellow"))
