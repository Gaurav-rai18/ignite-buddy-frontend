class DeviceError(Exception):
    """The operation cannot be done (message is shown to the user)."""


class Ambiguity(Exception):
    def __init__(self, question, options):
        super().__init__(question)
        self.question, self.options = question, options


class Declined(Exception):
    """The user said no in a confirmation dialog on this computer."""
