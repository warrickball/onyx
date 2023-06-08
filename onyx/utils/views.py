from rest_framework.views import APIView
from rest_framework.generics import CreateAPIView, ListAPIView


# https://stackoverflow.com/a/40253614 # to ease your mind
class OnyxAPIMixin:
    def get_permission_classes(self):
        return self.permission_classes  # type: ignore

    def check_permissions(self, request):
        has_permission, message = self.parse_permissions(
            self.get_permission_classes(), request, self
        )

        if not has_permission:
            self.permission_denied(  # type: ignore
                request,
                message=message,
            )

    def parse_permissions_old(self, perm, request, view):
        """
        It's recursion time (old version)
        """
        has_permission = None
        message = None

        # AND of permissions
        if isinstance(perm, list):
            perms = []
            for p in perm:
                has_p, msg = self.parse_permissions(p, request, view)
                perms.append((has_p, msg))

            messages = []
            for has_p, msg in perms:
                if has_p:
                    pass
                else:
                    messages.append(msg)
            if messages:
                has_permission = False
                if len(messages) > 1:
                    message = {"requires_all": messages}
                else:
                    message = messages[0]
            else:
                has_permission = True

        # OR of permissions
        elif isinstance(perm, tuple):
            perms = []
            for p in perm:
                has_p, msg = self.parse_permissions(p, request, view)
                perms.append((has_p, msg))

            messages = []
            for has_p, msg in perms:
                if has_p:
                    has_permission = True
                    break
                else:
                    messages.append(msg)
            else:
                has_permission = False
                if len(messages) > 1:
                    message = {"requires_any": messages}
                else:
                    message = messages[0]

        # A permission
        else:
            permission = perm()
            has_permission = permission.has_permission(request, view)
            message = permission.message

        return has_permission, message

    def parse_permissions(self, perm, request, view):
        """
        It's recursion time... again
        """
        # The old parse_permissions function (above) returned EVERY possible combination of permissions needed to allow a user access to an endpoint.
        # I was now thinking its probably best to return these requirements on a need-to-know basis.
        # So now, the view does a depth-first evaluation of permissions, and only returns the 'nearest' permission they require.

        # AND of permissions
        if isinstance(perm, list):
            for p in perm:
                has_p, msg = self.parse_permissions(p, request, view)

                if not has_p:
                    return False, msg

            return True, None

        # OR of permissions
        elif isinstance(perm, tuple):
            # By checking the OR in reverse, any message returned on permission fail will be the 'lowest' requirement
            # This is because in the perm combinations defined in permissions.py, more basic required perms are put to the left in a tuple
            # For example, if a user fails to satisfy: (IsAuthenticated, IsAdmin)
            # Which represents IsAuthenticated OR IsAdmin
            # Then they will see a message for needing to be Authenticated
            for p in reversed(perm):
                has_p, msg = self.parse_permissions(p, request, view)

                if has_p:
                    return True, None

            return False, msg  # type: ignore

        # A permission
        else:
            permission = perm()
            has_permission = permission.has_permission(request, view)
            message = permission.message
            return has_permission, message


class OnyxAPIView(OnyxAPIMixin, APIView):
    pass


class OnyxCreateAPIView(OnyxAPIMixin, CreateAPIView):
    pass


class OnyxListAPIView(OnyxAPIMixin, ListAPIView):
    pass
