from termcolor import colored


def send_invitation(invitation_link: str, recipients):
    print(
        colored(
            f"send_invitation was called with {invitation_link} and {recipients}",
            "yellow",
        )
    )
    return "Success"
