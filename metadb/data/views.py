from django.conf import settings
from django.core.exceptions import FieldDoesNotExist, ValidationError, PermissionDenied
from rest_framework import status
from rest_framework.response import Response
from rest_framework.pagination import CursorPagination
from accounts.permissions import (
    Admin,
    ApprovedOrAdmin,
    SameSiteAuthorityAsCIDOrAdmin,
)
from internal.models import History
from utils.views import METADBAPIView
from utils.response import METADBResponse
from utils.project import METADBProject
from utils.query import (
    make_keyvalues,
    get_query,
    get_filterset_datas_from_query_params,
    get_filterset_datas_from_keyvalues,
    apply_get_filterset,
    apply_query_filterset,
)
from utils.mutable import mutable
from utils.errors import ProjectDoesNotExist, ScopesDoNotExist
from .filters import METADBFilter
from .serializers import get_serializer


class CreateRecordView(METADBAPIView):
    permission_classes = Admin

    def post(self, request, code, test=False):
        """
        Create an instance for the given project.
        """
        try:
            project = METADBProject(
                code,
                user=request.user,
                action="add",
                fields=list(request.data),
            )
        except ProjectDoesNotExist:
            return METADBResponse.not_found("project")
        except PermissionDenied as e:
            return METADBResponse.forbidden(e.args[0])
        except FieldDoesNotExist as e:
            return METADBResponse.unknown_aspect("fields", e.args[0])

        # Add the user id to the metadata
        request.data["user"] = request.user.id

        # If a site code was not provided, use the user's site code
        if not request.data.get("site"):
            request.data["site"] = request.user.site.code

        # Get the model serializer, and validate the data
        serializer = get_serializer(project.model)(
            data=request.data,
            context={"field_contexts": project.field_contexts},
        )

        # If data is valid, save to the database. Otherwise, return 400
        if serializer.is_valid():
            if not test:
                instance = serializer.save()
                cid = instance.cid

                History.objects.create(
                    record=instance,
                    cid=cid,
                    user=request.user,
                    action="add",
                    changes=str(request.data),
                )
            else:
                cid = None

            return METADBResponse.action_success(
                "add", cid, test=test, status=status.HTTP_201_CREATED
            )
        else:
            return METADBResponse.validation_error(serializer.errors)


class GetRecordView(METADBAPIView):
    permission_classes = ApprovedOrAdmin

    def get(self, request, code, cid):
        """
        Get an instance for the given project.
        """
        # Take out the scope param from the request
        with mutable(request.query_params) as query_params:
            scopes = query_params.getlist("scope")
            if scopes:
                query_params.pop("scope")

        try:
            project = METADBProject(
                code,
                user=request.user,
                action="view",
                scopes=scopes,
            )
        except ProjectDoesNotExist:
            return METADBResponse.not_found("project")
        except ScopesDoNotExist as e:
            return METADBResponse.unknown_aspect("scopes", e.args[0])
        except PermissionDenied as e:
            return METADBResponse.forbidden(e.args[0])
        except FieldDoesNotExist as e:
            return METADBResponse.unknown_aspect("fields", e.args[0])

        # Get the instance
        # If the instance does not exist, return 404
        try:
            instance = (
                project.model.objects.select_related()
                .filter(suppressed=False)
                .get(cid=cid)
            )
        except project.model.DoesNotExist:
            return METADBResponse.not_found("cid")

        # Serialize the result
        serializer = get_serializer(project.model)(
            instance,
            fields=project.fields(),
            context={"field_contexts": project.field_contexts},
        )

        # Return response with data
        return Response(
            {
                "action": "view",
                "record": serializer.data,
            },
            status=status.HTTP_200_OK,
        )


class FilterRecordView(METADBAPIView):
    permission_classes = ApprovedOrAdmin

    def get(self, request, code):
        """
        Filter and return instances for the given project.
        """
        # Prepare paginator
        paginator = CursorPagination()
        paginator.ordering = "created"
        paginator.page_size = settings.CURSOR_PAGINATION_PAGE_SIZE

        # Take out the cursor param and scope params from the request
        with mutable(request.query_params) as query_params:
            cursor = query_params.get(paginator.cursor_query_param)
            if cursor:
                query_params.pop(paginator.cursor_query_param)

            scopes = query_params.getlist("scope")
            if scopes:
                query_params.pop("scope")

        try:
            project = METADBProject(
                code,
                user=request.user,
                action="view",
                fields=[x.partition("__")[0] for x in request.query_params],
                scopes=scopes,
            )
        except ProjectDoesNotExist:
            return METADBResponse.not_found("project")
        except ScopesDoNotExist as e:
            return METADBResponse.unknown_aspect("scopes", e.args[0])
        except PermissionDenied as e:
            return METADBResponse.forbidden(e.args[0])
        except FieldDoesNotExist as e:
            return METADBResponse.unknown_aspect("fields", e.args[0])

        # Turn the request query params into a series of dictionaries, each that will be passed to a filterset
        filterset_datas = get_filterset_datas_from_query_params(request.query_params)

        # View fields
        fields = project.fields()

        # Initial queryset
        qs = project.model.objects.select_related()

        if "suppressed" not in fields:
            qs = qs.filter(suppressed=False)

        for metric in project.model.CustomMeta.metrics:  # type: ignore
            qs = qs.prefetch_related(metric)

        # Apply filtersets
        try:
            qs = apply_get_filterset(
                fs=METADBFilter,  # Filterset to use
                model=project.model,  # Model that the filterset is linked to
                field_contexts=project.field_contexts,
                filterset_datas=filterset_datas,  # User data that determines how to apply the filterset
                qs=qs,  # Initial queryset
            )
        except FieldDoesNotExist as e:
            return METADBResponse.unknown_aspect("fields", e.args[0])
        except ValidationError as e:
            return METADBResponse.validation_error(e.args[0])

        # Add the pagination cursor param back into the request
        if cursor is not None:
            with mutable(request.query_params) as query_params:
                query_params[paginator.cursor_query_param] = cursor

        # Paginate the response
        instances = qs.order_by("id")
        result_page = paginator.paginate_queryset(instances, request)

        # Serialize the results
        serializer = get_serializer(project.model)(
            result_page,
            many=True,
            fields=fields,
            context={"field_contexts": project.field_contexts},
        )

        # Return paginated response
        return Response(
            {
                "action": "view",
                "next": paginator.get_next_link(),
                "previous": paginator.get_previous_link(),
                "records": serializer.data,
            }
        )


class QueryRecordView(METADBAPIView):
    permission_classes = ApprovedOrAdmin

    def post(self, request, code):
        """
        Filter and return instances for the given project.
        """
        # Prepare paginator
        paginator = CursorPagination()
        paginator.ordering = "created"
        paginator.page_size = settings.CURSOR_PAGINATION_PAGE_SIZE

        # Take out the cursor param and scope params from the request
        with mutable(request.query_params) as query_params:
            cursor = query_params.get(paginator.cursor_query_param)
            if cursor:
                query_params.pop(paginator.cursor_query_param)

            scopes = query_params.getlist("scope")
            if scopes:
                query_params.pop("scope")

        # If request data was provided
        # Turn the value of each key-value pair in request.data into a 'KeyValue' object
        # A list of keyvalues is returned by make_keyvalues
        if request.data:
            try:
                keyvalues = make_keyvalues(request.data)
            except Exception:
                return METADBResponse.invalid_query()

        else:
            keyvalues = []

        try:
            project = METADBProject(
                code,
                user=request.user,
                action="view",
                fields=[x.key.split("__")[0] for x in keyvalues],
                scopes=scopes,
            )
        except ProjectDoesNotExist:
            return METADBResponse.not_found("project")
        except ScopesDoNotExist as e:
            return METADBResponse.unknown_aspect("scopes", e.args[0])
        except PermissionDenied as e:
            return METADBResponse.forbidden(e.args[0])
        except FieldDoesNotExist as e:
            return METADBResponse.unknown_aspect("fields", e.args[0])

        # Construct a list of dictionaries from the keyvalues
        # Each of these dictionaries will be passed to a filterset
        # The filterset is being used just to clean and validate the input filters
        # Until we construct the query, it doesn't matter how fields are related in the query (i.e. AND, OR, etc)
        # All that matters is if the individual filters and their values are valid
        filterset_datas = get_filterset_datas_from_keyvalues(keyvalues)

        # Apply filtersets (to validate the data only)
        try:
            apply_query_filterset(
                fs=METADBFilter,  # Filterset to use
                model=project.model,  # Model that the filterset is linked to
                field_contexts=project.field_contexts,
                filterset_datas=filterset_datas,  # User data that determines how to apply the filterset
            )
        except FieldDoesNotExist as e:
            return METADBResponse.unknown_aspect("fields", e.args[0])
        except ValidationError as e:
            return METADBResponse.validation_error(e.args[0])

        # View fields
        fields = project.fields()

        # Initial queryset
        qs = project.model.objects.select_related()

        if "suppressed" not in fields:
            qs = qs.filter(suppressed=False)

        # If request data was provided, then it has now been validated
        # So we form the query (a Q object)
        # Then filter using the Q object
        if request.data:
            try:
                query = get_query(request.data)
            except Exception:
                return METADBResponse.invalid_query()

            qs = qs.filter(query)

        # Add the pagination cursor param back into the request
        if cursor is not None:
            with mutable(request.query_params) as query_params:
                query_params[paginator.cursor_query_param] = cursor

        # Paginate the response
        instances = qs.order_by("id")
        result_page = paginator.paginate_queryset(instances, request)

        # Serialize the results
        serializer = get_serializer(project.model)(
            result_page,
            many=True,
            fields=fields,
            context={"field_contexts": project.field_contexts},
        )

        # Return paginated response
        return Response(
            {
                "action": "view",
                "next": paginator.get_next_link(),
                "previous": paginator.get_previous_link(),
                "records": serializer.data,
            }
        )


class UpdateRecordView(METADBAPIView):
    permission_classes = SameSiteAuthorityAsCIDOrAdmin

    def patch(self, request, code, cid, test=False):
        """
        Update an instance for the given project.
        """
        try:
            project = METADBProject(
                code,
                user=request.user,
                action="change",
                fields=list(request.data),
            )
        except ProjectDoesNotExist:
            return METADBResponse.not_found("project")
        except PermissionDenied as e:
            return METADBResponse.forbidden(e.args[0])
        except FieldDoesNotExist as e:
            return METADBResponse.unknown_aspect("fields", e.args[0])

        # Get the instance to be updated
        # If the instance does not exist, return 404
        try:
            instance = (
                project.model.objects.select_related()
                .filter(suppressed=False)
                .get(cid=cid)
            )
        except project.model.DoesNotExist:
            return METADBResponse.not_found("cid")

        # Get the model serializer, and validate the data
        serializer = get_serializer(project.model)(
            instance=instance,
            data=request.data,
            partial=True,
            context={"field_contexts": project.field_contexts},
        )

        # If data is valid, update existing record in the database. Otherwise, return 400
        if serializer.is_valid():
            if not test:
                instance = serializer.save()

                History.objects.create(
                    record=instance,
                    cid=cid,
                    user=request.user,
                    action="change",
                    changes=str(request.data),
                )

            return METADBResponse.action_success("change", cid, test=test)
        else:
            return METADBResponse.validation_error(serializer.errors)


class SuppressRecordView(METADBAPIView):
    permission_classes = SameSiteAuthorityAsCIDOrAdmin

    def delete(self, request, code, cid, test=False):
        """
        Suppress an instance of the given project.
        """
        try:
            project = METADBProject(
                code,
                user=request.user,
                action="suppress",
            )
        except ProjectDoesNotExist:
            return METADBResponse.not_found("project")
        except PermissionDenied as e:
            return METADBResponse.forbidden(e.args[0])
        except FieldDoesNotExist as e:
            return METADBResponse.unknown_aspect("fields", e.args[0])

        # Get the instance to be suppressed
        # If the instance does not exist, return 404
        try:
            instance = (
                project.model.objects.select_related()
                .filter(suppressed=False)
                .get(cid=cid)
            )
        except project.model.DoesNotExist:
            return METADBResponse.not_found("cid")

        # Suppress the instance
        if not test:
            instance.suppressed = True  # type: ignore
            instance.save(update_fields=["suppressed", "last_modified"])

            History.objects.create(
                record=instance,
                cid=cid,
                user=request.user,
                action="suppress",
            )

        # Return response indicating suppression
        return METADBResponse.action_success("suppress", cid, test=test)


class DeleteRecordView(METADBAPIView):
    permission_classes = Admin

    def delete(self, request, code, cid, test=False):
        """
        Permanently delete an instance of the given project.
        """
        try:
            project = METADBProject(
                code,
                user=request.user,
                action="delete",
            )
        except ProjectDoesNotExist:
            return METADBResponse.not_found("project")
        except PermissionDenied as e:
            return METADBResponse.forbidden(e.args[0])
        except FieldDoesNotExist as e:
            return METADBResponse.unknown_aspect("fields", e.args[0])

        # Get the instance to be deleted
        # If it does not exist, return 404
        try:
            instance = project.model.objects.select_related().get(cid=cid)
        except project.model.DoesNotExist:
            return METADBResponse.not_found("cid")

        # Delete the instance
        if not test:
            instance.delete()

            History.objects.create(
                record=None,
                cid=cid,
                user=request.user,
                action="delete",
            )

        # Return response indicating deletion
        return METADBResponse.action_success("delete", cid, test=test)
