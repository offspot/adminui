from adminui.constants import ADMIN_PASSWORD, ADMIN_USERNAME


class RequiresLoginException(Exception):
    pass

def are_valid_credentials(username: str, password: str) -> bool:
    return username == ADMIN_USERNAME and password == ADMIN_PASSWORD

