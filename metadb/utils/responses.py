class METADBAPIResponse:
    NOT_FOUND = "Not found."  # Generic 404 message
    UNKNOWN_FIELD = "This field is unknown."
    NON_ACCEPTED_FIELD = "This field cannot be accepted."
    INTERNAL_SERVER_ERROR = (
        "Congratulations. The server imploded because of your actions!"  # hehehe
    )

    def __init__(self):
        self.errors = {}
        self.warnings = {}
        self.results = []
        self.next = None
        self.previous = None

    @property
    def data(self):
        return {
            "next": self.next,
            "previous": self.previous,
            "errors": self.errors,
            "warnings": self.warnings,
            "results": self.results,
        }
