class Error(Exception):
    """Base class for other exceptions"""
    pass

class ValidationError(Error):
    """
    Data error where its not possible to proceed
    """

    def __init__(self, message):
        self.message = message

class OrderError(Error):
    """
    Data error where its not possible to proceed
    """

    def __init__(self, message):
        self.message = message