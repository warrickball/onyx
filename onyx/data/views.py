from django.db.models import Count
from rest_framework import status, exceptions
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.pagination import CursorPagination
from rest_framework.views import APIView
from rest_framework.viewsets import ViewSetMixin
from accounts.permissions import Approved, ProjectApproved, ProjectAdmin
from utils.functions import mutable
from .models import Project, Choice, ProjectRecord
from .serializers import ProjectSerializerMap, SerializerNode, SummarySerializer
from .exceptions import CIDNotFound
from .query import make_atoms, validate_atoms, make_query
from .queryset import init_project_queryset, prefetch_nested
from .types import OnyxType
from .fields import (
    FieldHandler,
    generate_fields_spec,
    flatten_fields,
    unflatten_fields,
    include_exclude_fields,
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
        assert issubclass(model, ProjectRecord)
        self.model = model

        # Get the model's serializer
        self.serializer_cls = ProjectSerializerMap.get(self.model)

        self.handler = FieldHandler(
            project=self.project,
            action=self.project_action,  # type: ignore
            user=request.user,
        )

        # Take out any special params from the request
        with mutable(request.query_params) as query_params:
            # Used for cursor pagination
            self.cursor = query_params.get("cursor")
            if self.cursor:
                query_params.pop("cursor")

            # Used for including fields in output of get/filter/query
            self.include = list(query_params.getlist("include"))
            query_params.pop("include", None)

            # Used for excluding fields in output of get/filter/query
            self.exclude = list(query_params.getlist("exclude"))
            query_params.pop("exclude", None)

            # Used for specifying scopes of fields in get/filter/query
            self.scopes = list(query_params.getlist("scope"))
            query_params.pop("scope", None)

            # Used for summary aggregate in filter/query
            self.summarise = list(query_params.getlist("summarise"))
            query_params.pop("summarise", None)


class ProjectsView(APIView):
    def get_permissions(self):
        permission_classes = Approved

        return [permission() for permission in permission_classes]

    def get(self, request: Request) -> Response:
        """
        List all projects that the user has allowed actions on.
        """

        # Filter user groups to determine all (project, action, scope) tuples
        project_groups = [
            {
                "project": project_action_scope["projectgroup__project__code"],
                "action": project_action_scope["projectgroup__action"],
                "scope": project_action_scope["projectgroup__scope"],
            }
            for project_action_scope in request.user.groups.filter(
                projectgroup__isnull=False
            )
            .values(
                "projectgroup__project__code",
                "projectgroup__action",
                "projectgroup__scope",
            )
            .distinct()
        ]

        # Return list of allowed project groups
        return Response(project_groups)


class FieldsView(ProjectAPIView):
    def get_permissions(self):
        permission_classes = ProjectApproved
        self.project_action = "view"

        return [permission() for permission in permission_classes]

    def get(self, request: Request, code: str) -> Response:
        """
        List all fields for a given project.
        """

        # Get all viewable fields within requested scope
        field_names = self.handler.get_fields(self.scopes)

        # Determine OnyxField objects for each field
        onyx_fields = self.handler.resolve_fields(field_names)

        # Unflatten list of fields into nested dict
        fields_dict = unflatten_fields(field_names)

        # Generate field information into a nested structure
        fields_spec = generate_fields_spec(
            fields_dict=fields_dict,
            onyx_fields=onyx_fields,
        )

        # Return response with project fields and version
        return Response({"version": self.model.version(), "fields": fields_spec})


class LookupsView(ProjectAPIView):
    def get_permissions(self):
        permission_classes = ProjectApproved
        self.project_action = "view"

        return [permission() for permission in permission_classes]

    def get(self, request: Request, code: str) -> Response:
        """
        List all lookups for a given project.
        """

        # Get all viewable fields within requested scope
        field_names = self.handler.get_fields(self.scopes)

        # Determine OnyxField objects for each field
        onyx_fields = self.handler.resolve_fields(field_names)

        # Get onyx types
        onyx_types = {onyx_field.onyx_type for _, onyx_field in onyx_fields.items()}

        # Build lookups structure
        lookups = {
            onyx_type.label: onyx_type.lookups
            for onyx_type in OnyxType
            if onyx_type in onyx_types
        }

        # Return response with allowed lookups for each type featured in the project
        return Response(lookups)


class ChoicesView(ProjectAPIView):
    def get_permissions(self):
        permission_classes = ProjectApproved
        self.project_action = "view"

        return [permission() for permission in permission_classes]

    def get(self, request: Request, code: str, field: str) -> Response:
        """
        List all choices for a given field.
        """

        # Determine OnyxField object for the field
        try:
            onyx_field = self.handler.resolve_field(field)
        except exceptions.ValidationError as e:
            raise exceptions.ValidationError({"detail": e.args[0]})

        if onyx_field.onyx_type != OnyxType.CHOICE:
            raise exceptions.ValidationError(
                {"detail": [f"This field is not a '{OnyxType.CHOICE.label}' field."]}
            )

        # Obtain choices for the field
        choices = Choice.objects.filter(
            project_id=self.project.code,
            field=onyx_field.field_name,
            is_active=True,
        ).values_list(
            "choice",
            flat=True,
        )

        # Return choices for the field
        return Response(choices)


class ProjectRecordsViewSet(ViewSetMixin, ProjectAPIView):
    def get_permissions(self):
        if self.request.method == "POST":
            if self.action == "list":
                permission_classes = ProjectApproved
                self.project_action = "view"
            else:
                permission_classes = ProjectAdmin
                self.project_action = "add"

        elif self.request.method == "GET":
            permission_classes = ProjectApproved
            self.project_action = "view"

        elif self.request.method == "PATCH":
            permission_classes = ProjectAdmin
            self.project_action = "change"

        elif self.request.method == "DELETE":
            permission_classes = ProjectAdmin
            self.project_action = "delete"

        else:
            raise exceptions.MethodNotAllowed(self.request.method)

        return [permission() for permission in permission_classes]

    def create(self, request: Request, code: str, test: bool = False) -> Response:
        """
        Create an instance for the given project `code`.
        """

        # Validate the request data fields
        self.handler.resolve_fields(flatten_fields(request.data))

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

        if not test:
            # Create the instance
            instance = node.save()

            # Serialize the result
            serializer = self.serializer_cls(
                instance,
                fields=unflatten_fields(
                    self.serializer_cls.OnyxMeta.action_success_fields,
                ),
            )
            data = serializer.data
        else:
            data = {}

        # Return response indicating creation
        return Response(data, status=status.HTTP_201_CREATED)

    def retrieve(self, request: Request, code: str, cid: str) -> Response:
        """
        Use the `cid` to retrieve an instance for the given project `code`.
        """

        # Validate the include/exclude fields
        self.handler.resolve_fields(self.include + self.exclude)

        # Get all viewable fields within requested scope
        fields = self.handler.get_fields(self.scopes)

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
            # TODO: Don't think its wise to be modifying original request.data
            query = request.data

        # If a query was provided
        # Turn the value of each key-value pair in query into a 'QueryAtom' object
        # A list of QueryAtoms is returned
        if query:
            atoms = make_atoms(query)  # type: ignore
        else:
            atoms = []

        # Validate fields
        field_errors = {}
        onyx_fields = {}
        onyx_fields_extra = {}

        # Determine OnyxField objects for the fields used for filtering
        # Lookups are allowed for these
        for atom in atoms:
            try:
                onyx_fields[atom.key] = self.handler.resolve_field(
                    atom.key, allow_lookup=True
                )
            except exceptions.ValidationError as e:
                field_errors.setdefault(atom.key, []).append(e.args[0])

        # Determine extra OnyxField objects for the include/exclude/summary fields
        # Lookups are not allowed for these
        extra_fields = self.include + self.exclude + self.summarise

        for extra_field in extra_fields:
            try:
                onyx_fields_extra[extra_field] = self.handler.resolve_field(extra_field)
            except exceptions.ValidationError as e:
                field_errors.setdefault(extra_field, []).append(e.args[0])

        if field_errors:
            raise exceptions.ValidationError(field_errors)

        # Validate and clean the provided key-value pairs
        # This is done by first building a FilterSet
        # And then checking the underlying form is valid
        validate_atoms(self.model, atoms, onyx_fields)

        # Get all viewable fields within requested scope
        fields = self.handler.get_fields(self.scopes)

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
            q_object = make_query(query)  # type: ignore

            # A queryset is not guaranteed to return unique objects
            # Especially as a result of complex nested queries
            # So a call to distinct is necessary.
            # This (should) not affect the cursor pagination
            # as removing duplicates is not changing any order in the result set
            # TODO: Tests will be needed to confirm all of this
            qs = qs.filter(q_object).distinct()

        if self.summarise:
            onyx_fields_summary = {
                field_name: onyx_field
                for field_name, onyx_field in onyx_fields_extra.items()
                if field_name in self.summarise
            }

            summary_errors = {}
            for field_name, onyx_field in onyx_fields_summary.items():
                if onyx_field.onyx_type == OnyxType.RELATION:
                    summary_errors.setdefault(field_name, []).append(
                        "Cannot summarise over a relational field."
                    )
            if summary_errors:
                raise exceptions.ValidationError(summary_errors)

            qs_summary_values = qs.values(*self.summarise)
            if qs_summary_values.distinct().count() > 10000:
                raise exceptions.ValidationError(
                    {
                        "detail": "The current summary would return too many distinct values."
                    }
                )

            # Serialize the results
            serializer = SummarySerializer(
                qs_summary_values.annotate(count=Count("*")).order_by(*self.summarise),
                onyx_fields=onyx_fields_summary,
                many=True,
            )
        else:
            # Prepare paginator
            self.paginator = CursorPagination()
            self.paginator.ordering = "created"

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

        # Return response with either filtered set of data, or summarised values
        return Response(serializer.data)

    def partial_update(
        self, request: Request, code: str, cid: str, test: bool = False
    ) -> Response:
        """
        Use the `cid` to update an instance for the given project `code`.
        """

        # Validate the request data fields
        self.handler.resolve_fields(flatten_fields(request.data))

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

        if not test:
            # Update the instance
            instance = node.save()

            # Serialize the result
            serializer = self.serializer_cls(
                instance,
                fields=unflatten_fields(
                    self.serializer_cls.OnyxMeta.action_success_fields,
                ),
            )
            data = serializer.data
        else:
            data = {}

        # Return response indicating update
        return Response(data)

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

        # Serialize the result
        serializer = self.serializer_cls(
            instance,
            fields=unflatten_fields(
                self.serializer_cls.OnyxMeta.action_success_fields,
            ),
        )
        data = serializer.data

        # Return response indicating deletion
        return Response(data)
