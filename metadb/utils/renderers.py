from rest_framework import renderers, status


class METADBJSONRenderer(renderers.JSONRenderer):
    def render(self, data, accepted_media_type=None, renderer_context=None):
        """
        Render `data` into JSON, returning a bytestring.
        """
        if renderer_context:
            status_code = renderer_context["response"].status_code
            api_response = renderer_context.get("api_response")

            if api_response:
                if data:
                    if status.is_client_error(status_code) or status.is_server_error(
                        status_code
                    ):
                        api_response.errors = data

                    else:
                        if isinstance(data, list):
                            api_response.results = data
                        else:
                            api_response.results.append(data)

                data = api_response.data

        return super().render(
            data,
            accepted_media_type=accepted_media_type,
            renderer_context=renderer_context,
        )
