import time
from .models import Request


# Credit to Felix Eklöf for this middleware
# https://stackoverflow.com/a/63176786/16088113
class SaveRequest:
    def __init__(self, get_response):
        self.get_response = get_response
        self.prefixes = ["/accounts", "/projects"]

    def __call__(self, request):
        _t = time.time()  # Calculated execution time.
        response = self.get_response(request)  # Get response from view function.
        _t = int((time.time() - _t) * 1000)

        # If the url does not start with one of the prefixes
        # Return the response and dont log the request
        if not any(request.path.startswith(prefix) for prefix in self.prefixes):
            return response

        # Create Request instance
        request_log = Request(
            endpoint=request.path,
            method=request.method,
            status=response.status_code,
            address=self.get_client_ip(request),
            exec_time=_t,
        )

        # Assign user to log if it's not an anonymous user
        if not request.user.is_anonymous:
            request_log.user = request.user

        # Save log in db
        request_log.save()
        return response

    # get clients ip address
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            _ip = x_forwarded_for.split(",")[0]
        else:
            _ip = request.META.get("REMOTE_ADDR")
        return _ip
