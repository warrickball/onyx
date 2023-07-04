from django.conf import settings
from django.core.exceptions import FieldDoesNotExist, ValidationError, PermissionDenied
from rest_framework import status
from rest_framework.response import Response
from rest_framework.pagination import CursorPagination
from rest_framework.views import APIView
from accounts.permissions import Approved, Admin, IsInProjectGroup, IsInScopeGroups
from utils.response import OnyxResponse
from utils.project import OnyxProject
from utils.mutable import mutable
from utils.exceptionhandler import handle_exception
from utils.nested import parse_dunders, prefetch_nested
from .models import Choice
from .filters import OnyxFilter
from .serializers import ModelSerializerMap, SerializerNode
from django_query_tools.server import make_atoms, validate_atoms, make_query


# TODO: Handle request.data = None ISE
class CreateRecordView(APIView):
    permission_classes = Admin + [IsInProjectGroup, IsInScopeGroups]
    action = "add"

    def post(self, request, code, test=False):
        """
        Create an instance for the given project.
        """
        try:
            project = OnyxProject(
                code,
                user=request.user,
                action=self.action,
                fields=parse_dunders(request.data),
            )
        except (PermissionDenied, FieldDoesNotExist) as e:
            return handle_exception(e)

        # Get the model serializer
        serializer_cls = ModelSerializerMap.get(project.model)
        if not serializer_cls:
            return OnyxResponse.not_found("Serializer")

        # Validate the data
        # If data is valid, save to the database. Otherwise, return 400
        node = SerializerNode(
            serializer_cls,
            data=request.data,
            context={"request": self.request},
        )

        if not node.is_valid():
            return OnyxResponse.validation_error(node.errors)

        # Create the instance
        if not test:
            instance = node.save()
            cid = instance.cid
        else:
            cid = None

        # Return response indicating creation
        return OnyxResponse.action_success(
            self.action, cid, test=test, status=status.HTTP_201_CREATED
        )


class GetRecordView(APIView):
    permission_classes = Approved + [IsInProjectGroup, IsInScopeGroups]
    action = "view"

    def get(self, request, code, cid):
        """
        Get an instance for the given project.
        """
        # Take out the scope param from the request
        with mutable(request.query_params) as query_params:
            exclude = query_params.getlist("exclude")
            if exclude:
                query_params.pop("exclude")

            scopes = query_params.getlist("scope")
            if scopes:
                query_params.pop("scope")

        try:
            project = OnyxProject(
                code,
                user=request.user,
                action="view",
                scopes=scopes,
            )
        except (PermissionDenied, FieldDoesNotExist) as e:
            return handle_exception(e)

        # Get the instance
        # If the instance does not exist, return 404
        try:
            instance = (
                project.model.objects.select_related()
                .filter(suppressed=False)
                .get(cid=cid)
            )
        except project.model.DoesNotExist:
            return OnyxResponse.not_found("CID")

        # Get the model serializer
        serializer_cls = ModelSerializerMap.get(project.model)
        if not serializer_cls:
            return OnyxResponse.not_found("Serializer")

        # Serialize the result
        serializer = serializer_cls(
            instance,
            fields=project.view_fields(exclude=exclude),
            read_only=True,
        )

        # Return response with data
        return Response(
            {
                "action": "view",
                "record": serializer.data,
            },
            status=status.HTTP_200_OK,
        )


def filter_query(request, code):
    """
    Handles the logic for both the `filter` and `query` endpoints.
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

        exclude = query_params.getlist("exclude")
        if exclude:
            query_params.pop("exclude")

        scopes = query_params.getlist("scope")
        if scopes:
            query_params.pop("scope")

    # If method == GET, then parameters were provided in the query_params
    # Convert these into the same format as the JSON provided when method == POST
    if request.method == "GET":
        query = [
            {field: value}
            for field in request.query_params
            for value in request.query_params.getlist(field)
        ]
        if query:
            query = {"&": query}
    else:
        query = request.data

    # If a query was provided
    # Turn the value of each key-value pair in query into a 'QueryAtom' object
    # A list of QueryAtoms is returned by make_atoms
    if query:
        try:
            # The value is turned into a str for the filterset form.
            # This is what the filterset is built to handle; it attempts to decode these strs and returns errors if it fails.
            # If we don't turn these values into strs, the filterset can crash
            # e.g. If you pass a list, it assumes it is as a str, and tries to split by a comma
            atoms = make_atoms(query, to_str=True)
        except Exception:
            return OnyxResponse.invalid_query()
    else:
        atoms = []

    try:
        project = OnyxProject(
            code,
            user=request.user,
            action="view",
            fields=[x.key for x in atoms],
            scopes=scopes,
        )
    except (PermissionDenied, FieldDoesNotExist) as e:
        return handle_exception(e)

    # Validate and clean the provided key-value pairs
    # This is done by first building a FilterSet
    # And then checking the underlying form is valid
    try:
        validate_atoms(
            atoms,
            filterset=OnyxFilter,
            filterset_args=[project],
            filterset_model=project.model,
        )
    except (FieldDoesNotExist, ValidationError) as e:
        return handle_exception(e)

    # View fields
    fields = project.view_fields(exclude=exclude)

    # Initial queryset
    qs = project.model.objects.select_related()

    # Ignore suppressed data
    if "suppressed" not in fields:
        qs = qs.filter(suppressed=False)

    # Prefetch any nested fields within scope
    qs = prefetch_nested(qs, fields)

    # If data was provided, then it has now been validated
    # So we form the Q object, and filter the queryset with it
    if query:
        try:
            q_object = make_query(query)
        except Exception:
            return OnyxResponse.invalid_query()

        # A queryset is not guaranteed to return unique objects
        # Especially as a result of complex nested queries
        # So a call to distinct is necessary.
        # This (should) not affect the cursor pagination
        # as removing duplicates is not changing any order in the result set
        # TODO: Tests will be needed to confirm all of this
        qs = qs.filter(q_object).distinct()

    # Add the pagination cursor param back into the request
    if cursor is not None:
        with mutable(request.query_params) as query_params:
            query_params[paginator.cursor_query_param] = cursor

    # Paginate the response
    instances = qs.order_by("id")
    result_page = paginator.paginate_queryset(instances, request)

    # Get the model serializer
    serializer_cls = ModelSerializerMap.get(project.model)
    if not serializer_cls:
        return OnyxResponse.not_found("Serializer")

    # Serialize the results
    serializer = serializer_cls(
        result_page,
        many=True,
        fields=fields,
        read_only=True,
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


class FilterRecordView(APIView):
    permission_classes = Approved + [IsInProjectGroup, IsInScopeGroups]
    action = "view"

    def get(self, request, code):
        """
        Filter and return instances for the given project.
        """
        return filter_query(request, code)


class QueryRecordView(APIView):
    permission_classes = Approved + [IsInProjectGroup, IsInScopeGroups]
    action = "view"

    def post(self, request, code):
        """
        Filter and return instances for the given project.
        """
        return filter_query(request, code)


class UpdateRecordView(APIView):
    permission_classes = Admin + [IsInProjectGroup, IsInScopeGroups]
    action = "change"

    def patch(self, request, code, cid, test=False):
        """
        Update an instance for the given project.
        """
        try:
            project = OnyxProject(
                code,
                user=request.user,
                action="change",
                fields=parse_dunders(
                    request.data
                ),  # TODO: separate identifiers into 'add' permission
            )
        except (PermissionDenied, FieldDoesNotExist) as e:
            return handle_exception(e)

        # Get the instance to be updated
        # If the instance does not exist, return 404
        try:
            instance = (
                project.model.objects.select_related()
                .filter(suppressed=False)
                .get(cid=cid)
            )
        except project.model.DoesNotExist:
            return OnyxResponse.not_found("CID")

        # Get the model serializer
        serializer_cls = ModelSerializerMap.get(project.model)
        if not serializer_cls:
            return OnyxResponse.not_found("Serializer")

        # Validate the data using the serializer
        # If data is valid, update existing record in the database.
        # Otherwise, return 400
        node = SerializerNode(
            serializer_cls,
            data=request.data,
        )

        if not node.is_valid(instance=instance):
            return OnyxResponse.validation_error(node.errors)

        # Update the instance
        if not test:
            instance = node.save()

        # Return response indicating update
        return OnyxResponse.action_success("change", cid, test=test)


class SuppressRecordView(APIView):
    permission_classes = Admin + [IsInProjectGroup, IsInScopeGroups]
    action = "suppress"

    def delete(self, request, code, cid, test=False):
        """
        Suppress an instance of the given project.
        """
        try:
            project = OnyxProject(
                code,
                user=request.user,
                action="suppress",
            )
        except (PermissionDenied, FieldDoesNotExist) as e:
            return handle_exception(e)

        # Get the instance to be suppressed
        # If the instance does not exist, return 404
        try:
            instance = (
                project.model.objects.select_related()
                .filter(suppressed=False)
                .get(cid=cid)
            )
        except project.model.DoesNotExist:
            return OnyxResponse.not_found("CID")

        # Suppress the instance
        if not test:
            instance.suppressed = True  # type: ignore
            instance.save(update_fields=["suppressed", "last_modified"])

        # Return response indicating suppression
        return OnyxResponse.action_success("suppress", cid, test=test)


class DeleteRecordView(APIView):
    permission_classes = Admin + [IsInProjectGroup, IsInScopeGroups]
    action = "delete"

    def delete(self, request, code, cid, test=False):
        """
        Permanently delete an instance of the given project.
        """
        try:
            project = OnyxProject(
                code,
                user=request.user,
                action="delete",
            )
        except (PermissionDenied, FieldDoesNotExist) as e:
            return handle_exception(e)

        # Get the instance to be deleted
        # If it does not exist, return 404
        try:
            instance = project.model.objects.select_related().get(cid=cid)
        except project.model.DoesNotExist:
            return OnyxResponse.not_found("CID")

        # Delete the instance
        if not test:
            instance.delete()

        # Return response indicating deletion
        return OnyxResponse.action_success("delete", cid, test=test)


class ProjectView(APIView):
    pass  # TODO


class ScopesView(APIView):
    pass  # TODO


class FieldsView(APIView):
    pass  # TODO


class ChoicesView(APIView):
    permission_classes = Approved + [IsInProjectGroup, IsInScopeGroups]
    action = "view"

    def get(self, request, code, field):
        """
        List all choices for a given field.
        """

        try:
            project = OnyxProject(
                code,
                user=request.user,
                action="view",
                fields=[field],
            )
        except (PermissionDenied, FieldDoesNotExist) as e:
            return handle_exception(e)

        field = project.fields[field.lower()]

        choices = Choice.objects.filter(
            content_type=field.content_type,
            field=field.field_name,
            is_active=True,
        ).values_list(
            "choice",
            flat=True,
        )

        return Response({"action": "view", "choices": choices})
