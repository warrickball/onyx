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
        self.results = []

    @property
    def data(self):
        d = {
            "errors": self.errors,
            "results": self.results,
        }
        if self.next:
            d["next"] = self.next

        if self.previous:
            d["previous"] = self.previous

        return d
