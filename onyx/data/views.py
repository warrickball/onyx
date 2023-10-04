from django.core.exceptions import FieldDoesNotExist, ValidationError
from rest_framework import status, exceptions
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.pagination import CursorPagination
from rest_framework.views import APIView
from rest_framework.viewsets import ViewSetMixin
from accounts.permissions import Approved, ProjectApproved, ProjectAdmin
from .models import Project, Choice
from .filters import OnyxFilter
from .serializers import ModelSerializerMap, SerializerNode
from .exceptions import CIDNotFound
from .utils import (
    mutable,
    prefetch_nested,
    assign_fields_info,
    resolve_fields,
    validate_fields,
    get_fields,
    flatten_fields,
    unflatten_fields,
    include_exclude_fields,
    init_project_queryset,
)
from django_query_tools.server import (
    make_atoms,
    validate_atoms,
    make_query,
    QueryException,
)


class ProjectAPIView(APIView):
    """
    `APIView` with some additional initial setup for working with a specific project.
    """

    def initial(self, request: Request, *args, **kwargs):
        super().initial(request, *args, **kwargs)

        # Get the project
        self.project = Project.objects.get(code__iexact=kwargs["code"])

        # Get the project's model
        model = self.project.content_type.model_class()
        assert model is not None
        self.model = model

        # Get the model's serializer
        serializer_cls = ModelSerializerMap.get(self.model)
        self.serializer_cls = serializer_cls

        # Take out any special params from the request
        with mutable(request.query_params) as query_params:
            # Used for cursor pagination
            self.cursor = query_params.get("cursor")
            if self.cursor:
                query_params.pop("cursor")

            # Used for including fields in output of get/filter/query
            self.include = query_params.getlist("include")
            if self.include:
                query_params.pop("include")

            # Used for excluding fields in output of get/filter/query
            self.exclude = query_params.getlist("exclude")
            if self.exclude:
                query_params.pop("exclude")

            # Used for specifying scopes of fields in get/filter/query
            self.scopes = query_params.getlist("scope")
            if self.scopes:
                query_params.pop("scope")


class ProjectsView(APIView):
    def get_permissions(self):
        permission_classes = Approved

        return [permission() for permission in permission_classes]

    def get(self, request: Request) -> Response:
        """
        List all projects that the user has allowed actions on.
        """

        projects = {}

        # Filter user groups to determine all distinct (code, action) pairs
        # Create list of available actions for each project
        for project_action in (
            request.user.groups.filter(projectgroup__isnull=False)
            .values("projectgroup__project__code", "projectgroup__action")
            .distinct()
        ):
            projects.setdefault(
                project_action["projectgroup__project__code"], []
            ).append(project_action["projectgroup__action"])

        return Response(projects)


class FieldsView(ProjectAPIView):
    def get_permissions(self):
        permission_classes = ProjectApproved
        self.action = "view"

        return [permission() for permission in permission_classes]

    def get(self, request: Request, code: str) -> Response:
        """
        List all fields for a given project.
        """

        # Get all viewable fields within requested scope
        fields = get_fields(
            code=self.project.code,
            action=self.action,
            scopes=self.scopes,
        )

        # Determine field info for each field
        fields_info, _ = resolve_fields(
            code=self.project.code,
            model=self.model,
            fields=fields,
        )

        # Unflatten list of fields into nested dict
        fields_dict = unflatten_fields(fields)

        # Assign field information into nested structure
        field_types = assign_fields_info(
            fields_dict=fields_dict,
            fields_info=fields_info,
        )

        return Response(field_types)


class ChoicesView(ProjectAPIView):
    def get_permissions(self):
        permission_classes = ProjectApproved
        self.action = "view"

        return [permission() for permission in permission_classes]

    def get(self, request: Request, code: str, field: str) -> Response:
        """
        List all choices for a given field.
        """

        # Validate the field
        validate_fields(
            user=request.user,
            code=self.project.code,
            app_label=self.project.content_type.app_label,
            action=self.action,
            fields=[field],
        )

        # Determine field info for the field
        fields_info, _ = resolve_fields(
            code=self.project.code,
            model=self.model,
            fields=[field],
        )

        # Obtain choices for the field
        choices = Choice.objects.filter(
            project_id=self.project.code,
            field=fields_info[field].field_name,
            is_active=True,
        ).values_list(
            "choice",
            flat=True,
        )

        return Response(choices)


class ProjectRecordsViewSet(ViewSetMixin, ProjectAPIView):
    def get_permissions(self):
        if self.request.method == "POST":
            if self.action == "list":
                permission_classes = ProjectApproved
                self.action = "view"
            else:
                permission_classes = ProjectAdmin
                self.action = "add"

        elif self.request.method == "GET":
            permission_classes = ProjectApproved
            self.action = "view"

        elif self.request.method == "PATCH":
            permission_classes = ProjectAdmin
            self.action = "change"

        elif self.request.method == "DELETE":
            permission_classes = ProjectAdmin
            self.action = "delete"

        else:
            raise exceptions.MethodNotAllowed(self.request.method)

        return [permission() for permission in permission_classes]

    def create(self, request: Request, code: str, test: bool = False) -> Response:
        """
        Create an instance for the given project `code`.
        """

        # Validate the fields
        validate_fields(
            user=request.user,
            code=self.project.code,
            app_label=self.project.content_type.app_label,
            action=self.action,
            fields=flatten_fields(request.data),
        )

        # Validate the data
        node = SerializerNode(
            self.serializer_cls,
            data=request.data,
            context={
                "project": self.project.code,
                "request": self.request,
            },
        )

        if not node.is_valid():
            raise exceptions.ValidationError(node.errors)

        # Create the instance
        if not test:
            instance = node.save()
            cid = instance.cid
        else:
            cid = None

        # Return response indicating creation
        return Response({"cid": cid}, status=status.HTTP_201_CREATED)

    def retrieve(self, request: Request, code: str, cid: str) -> Response:
        """
        Use the `cid` to retrieve an instance for the given project `code`.
        """

        # Validate the fields
        validate_fields(
            user=request.user,
            code=self.project.code,
            app_label=self.project.content_type.app_label,
            action=self.action,
            fields=list(self.include) + list(self.exclude),
        )

        # Get all viewable fields within requested scope
        fields = get_fields(
            code=self.project.code,
            action=self.action,
            scopes=self.scopes,
        )

        # Initial queryset
        qs = init_project_queryset(
            model=self.model,
            user=request.user,
            fields=fields,
        )

        # Apply include/exclude rules to the fields
        # Unflatten list of fields into nested fields_dict
        fields_dict = unflatten_fields(
            include_exclude_fields(
                fields=fields,
                include=self.include,
                exclude=self.exclude,
            )
        )

        # Get the instance
        # If the instance does not exist, return 404
        try:
            instance = qs.get(cid=cid)
        except self.model.DoesNotExist:
            raise CIDNotFound

        # Serialize the result
        serializer = self.serializer_cls(
            instance,
            fields=fields_dict,
        )

        # Return response with data
        return Response(serializer.data)

    def list(self, request: Request, code: str) -> Response:
        """
        Filter and list instances for the given project `code`.
        """

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

        # Prepare paginator
        self.paginator = CursorPagination()
        self.paginator.ordering = "created"

        # If a query was provided
        # Turn the value of each key-value pair in query into a 'QueryAtom' object
        # A list of QueryAtoms is returned by make_atoms
        if query:
            try:
                # The value is turned into a str for the filterset form.
                # This is what the filterset is built to handle; it attempts to decode these strs and returns errors if it fails.
                # If we don't turn these values into strs, the filterset can crash
                # e.g. If you pass a list, it assumes it is as a str, and tries to split by a comma
                atoms = make_atoms(query, to_str=True)  # type: ignore
            except QueryException as e:
                raise exceptions.ValidationError({"detail": e.args[0]})
        else:
            atoms = []

        fields_info, unknown = resolve_fields(
            code=self.project.code,
            model=self.model,
            fields=[x.key for x in atoms],
        )

        # Validate the fields
        validate_fields(
            user=request.user,
            code=self.project.code,
            app_label=self.project.content_type.app_label,
            action=self.action,
            fields=[field_info.field_path for _, field_info in fields_info.items()]
            + list(self.include)
            + list(self.exclude),
            unknown=unknown,
        )

        # Validate and clean the provided key-value pairs
        # This is done by first building a FilterSet
        # And then checking the underlying form is valid
        try:
            validate_atoms(
                atoms,
                filterset=OnyxFilter,
                filterset_args=[fields_info],
                filterset_model=self.model,
            )
        except FieldDoesNotExist as e:
            raise exceptions.ValidationError(
                {field: ["This field has an invalid lookup."] for field in e.args[0]}
            )
        except ValidationError as e:
            raise exceptions.ValidationError(e.args[0])

        # Get all viewable fields within requested scope
        fields = get_fields(
            code=self.project.code,
            action=self.action,
            scopes=self.scopes,
        )

        # Initial queryset
        qs = init_project_queryset(
            model=self.model,
            user=request.user,
            fields=fields,
        )

        # Apply include/exclude rules to the fields
        # Unflatten list of fields into nested fields_dict
        fields_dict = unflatten_fields(
            include_exclude_fields(
                fields=fields,
                include=self.include,
                exclude=self.exclude,
            )
        )

        # Prefetch any nested fields within scope
        qs = prefetch_nested(qs=qs, fields_dict=fields_dict)

        # If data was provided, then it has now been validated
        # So we form the Q object, and filter the queryset with it
        if query:
            try:
                q_object = make_query(query)  # type: ignore
            except QueryException as e:
                raise exceptions.ValidationError({"detail": e.args[0]})

            # A queryset is not guaranteed to return unique objects
            # Especially as a result of complex nested queries
            # So a call to distinct is necessary.
            # This (should) not affect the cursor pagination
            # as removing duplicates is not changing any order in the result set
            # TODO: Tests will be needed to confirm all of this
            qs = qs.filter(q_object).distinct()

        # Add the pagination cursor param back into the request
        if self.cursor:
            with mutable(request.query_params) as query_params:
                query_params[self.paginator.cursor_query_param] = self.cursor

        # Paginate the response
        instances = qs.order_by("id")
        result_page = self.paginator.paginate_queryset(instances, request)

        # Serialize the results
        serializer = self.serializer_cls(
            result_page,
            many=True,
            fields=fields_dict,
        )

        # Return paginated response
        return Response(serializer.data)

    def partial_update(
        self, request: Request, code: str, cid: str, test: bool = False
    ) -> Response:
        """
        Use the `cid` to update an instance for the given project `code`.
        """

        # Validate the fields
        validate_fields(
            user=request.user,
            code=self.project.code,
            app_label=self.project.content_type.app_label,
            action=self.action,
            fields=flatten_fields(request.data),
        )

        # Initial queryset
        qs = init_project_queryset(
            model=self.model,
            user=request.user,
        )

        # Get the instance to be updated
        # If the instance does not exist, return 404
        try:
            instance = qs.get(cid=cid)
        except self.model.DoesNotExist:
            raise CIDNotFound

        # Validate the data
        node = SerializerNode(
            self.serializer_cls,
            data=request.data,
            context={
                "project": self.project.code,
                "request": self.request,
            },
        )

        if not node.is_valid(instance=instance):
            raise exceptions.ValidationError(node.errors)

        # Update the instance
        if not test:
            instance = node.save()

        # Return response indicating update
        return Response({"cid": cid})

    def destroy(self, request: Request, code: str, cid: str) -> Response:
        """
        Use the `cid` to permanently delete an instance of the given project `code`.
        """
        # Initial queryset
        qs = init_project_queryset(
            model=self.model,
            user=request.user,
        )

        # Get the instance to be deleted
        # If the instance does not exist, return 404
        try:
            instance = qs.get(cid=cid)
        except self.model.DoesNotExist:
            raise CIDNotFound

        # Delete the instance
        instance.delete()

        # Return response indicating deletion
        return Response({"cid": cid})
