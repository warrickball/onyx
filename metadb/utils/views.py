from rest_framework.views import APIView
from rest_framework.generics import CreateAPIView, ListAPIView


class METADBAPIMixin:
    def parse_permissions(self, perm, request, view):
        """
        It's recursion time
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
                    message = {"All are required": messages}
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
                    message = {"At least one is required": messages}
                else:
                    message = messages[0]

        # A permission
        else:
            permission = perm()
            has_permission = permission.has_permission(request, view)
            message = permission.message

        return has_permission, message


# https://stackoverflow.com/a/40253614 # to ease your mind
class METADBAPIView(METADBAPIMixin, APIView):
    def get_permission_classes(self):
        return self.permission_classes

    def check_permissions(self, request):
        has_permission, message = self.parse_permissions(
            self.get_permission_classes(), request, self
        )

        if not has_permission:
            # if request.authenticators and not request.successful_authenticator:
            #     raise exceptions.PermissionDenied(detail=message, code=401)
            # else:
            #     raise exceptions.PermissionDenied(detail=message, code=403)

            self.permission_denied(
                request,
                message=message,
            )


class METADBCreateAPIView(METADBAPIMixin, CreateAPIView):
    def get_permission_classes(self):
        return self.permission_classes

    def check_permissions(self, request):
        has_permission, message = self.parse_permissions(
            self.get_permission_classes(), request, self
        )

        if not has_permission:
            # if request.authenticators and not request.successful_authenticator:
            #     raise exceptions.PermissionDenied(detail=message, code=401)
            # else:
            #     raise exceptions.PermissionDenied(detail=message, code=403)

            self.permission_denied(
                request,
                message=message,
            )


class METADBListAPIView(METADBAPIMixin, ListAPIView):
    def get_permission_classes(self):
        return self.permission_classes

    def check_permissions(self, request):
        has_permission, message = self.parse_permissions(
            self.get_permission_classes(), request, self
        )

        if not has_permission:
            # if request.authenticators and not request.successful_authenticator:
            #     raise exceptions.PermissionDenied(detail=message, code=401)
            # else:
            #     raise exceptions.PermissionDenied(detail=message, code=403)

            self.permission_denied(
                request,
                message=message,
            )
