from rest_framework import renderers, status


class OnyxJSONRenderer(renderers.JSONRenderer):
    def render(self, data, accepted_media_type=None, renderer_context=None):
        """
        Render `data` into JSON, returning a bytestring.
        """
        render_data = {}
        if renderer_context:
            status_code = renderer_context["response"].status_code

            if status.is_client_error(status_code):
                render_data["status"] = "fail"
                render_data["messages"] = data
            elif status.is_server_error(status_code):
                render_data["status"] = "error"
                render_data["messages"] = data
            else:
                render_data["status"] = "success"
                render_data["data"] = data

        return super().render(
            render_data,
            accepted_media_type=accepted_media_type,
            renderer_context=renderer_context,
        )
