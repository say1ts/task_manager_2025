class AuthError(Exception):
    pass


class UserAlreadyExistsError(AuthError):
    def __init__(self, email: str):
        super().__init__(f"User with email {email} already exists.")


class InvalidCredentialsError(AuthError):
    def __init__(self):
        super().__init__("Invalid email or password.")
