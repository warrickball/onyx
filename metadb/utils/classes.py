class KeyValue:
    """
    Class for representing a single key-value pair.
    """

    def __init__(self, key, value):
        self.key = key
        self.value = value


class METADBAPIResponse:
    NOT_FOUND = "Not found."  # Generic 404 message
    UNKNOWN_FIELD = "This field is unknown."
    NON_ACCEPTED_FIELD = "This field cannot be accepted."
    INTERNAL_SERVER_ERROR = (
        "Congratulations. The server imploded because of your actions!"  # hehehe
    )

    def __init__(self):
        self.next = None
        self.previous = None
        self.errors = {}
        self.warnings = {}
        self.results = []

    @property
    def data(self):
        return {
            "next": self.next,
            "previous": self.previous,
            "errors": self.errors,
            "warnings": self.warnings,
            "results": self.results,
        }
