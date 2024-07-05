import requests


class LtiException(Exception):
    pass


class OIDCException(Exception):
    pass


class LtiServiceException(LtiException):
    def __init__(self, response: requests.Response):
        msg = f"HTTP response [{response.url}]: {str(response.status_code)} - {response.text}"
        super().__init__(msg)
        self.response = response


class LtiJWTException(LtiException):
    """
        An error stemming from the JWT body of the message launch.
    """


class LtiMessageValidationException(LtiException):
    """
        An error encountered while validating an LTI launch message.
    """
    pass


class LtiKeyException(LtiException):
    """
        An error to do with keys for the OAuth process.
    """
    pass

