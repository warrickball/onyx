from django.conf import settings
from django.forms.models import model_to_dict
from rest_framework import status
from rest_framework.response import Response
from rest_framework.pagination import CursorPagination
from accounts.permissions import (
    Admin,
    ApprovedOrAdmin,
    SameSiteAuthorityAsCIDOrAdmin,
)
from utils.views import METADBAPIView
from utils.response import METADBAPIResponse
from utils.project import (
    get_project_and_model,
    init_queryset,
)
from utils.permissions import (
    get_fields_from_permissions,
    check_permissions,
    not_authorised_response,
)
from utils.query import (
    make_keyvalues,
    get_query,
    get_filterset_datas_from_query_params,
    get_filterset_datas_from_keyvalues,
    apply_get_filterset,
    apply_query_filterset,
)
from utils.fieldcontext import get_field_contexts
from utils.mutable import mutable
from .filters import METADBFilter
from .serializers import get_serializer
from internal.models import History


# TODO: Not using view fields on create means out of scope (e.g. mpxpha) fields get stamped away (e.g. on mpx)
class CreateRecordView(METADBAPIView):
    permission_classes = Admin

    def post(self, request, project_code, test=False):
        """
        Create an instance for the given project.
        """
        # Get the project. If it does not exist, return 404
        project, model = get_project_and_model(project_code)
        if not project or not model:
            return Response(
                {project_code.lower(): [METADBAPIResponse.NOT_FOUND]},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Fields that will be created
        create_fields = list(request.data)

        # (Parent) model and contenttype for each field in the model
        field_contexts = get_field_contexts(model)

        # Check user has permission to create the instance
        required, unknown = check_permissions(
            project=project,
            user=request.user,
            action="add",
            user_fields=create_fields,
            field_contexts=field_contexts,
        )

        # Handle required permissions
        if required:
            return not_authorised_response(
                project=project,
                user=request.user,
                required=required,
            )

        # If unknown fields were provided, return 400
        if unknown:
            return Response(
                unknown,
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Get fields that can be viewed
        view_fields = get_fields_from_permissions(project.view_group.permissions.all())

        # If a site code was not provided, use the user's site code
        if not request.data.get("site"):
            request.data["site"] = request.user.site.code

        # Get the model serializer, and validate the data
        serializer = get_serializer(model)(
            data=request.data,
            fields=view_fields,
            context={"field_contexts": field_contexts, "request": request},
        )

        # If data is valid, save to the database. Otherwise, return 400
        if serializer.is_valid():
            if not test:
                instance = serializer.save()

                History.objects.create(
                    record=instance,
                    cid=instance.cid,
                    user=request.user,
                    action="add",
                    changes=str(request.data),
                )

            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED,
            )
        else:
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )


class GetRecordView(METADBAPIView):
    permission_classes = ApprovedOrAdmin

    def get(self, request, project_code):
        """
        Filter and return instances for the given project.
        """
        # Get the project. If it does not exist, return 404
        project, model = get_project_and_model(project_code)
        if not project or not model:
            return Response(
                {project_code.lower(): [METADBAPIResponse.NOT_FOUND]},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Prepare paginator
        paginator = CursorPagination()
        paginator.ordering = "created"
        paginator.page_size = settings.CURSOR_PAGINATION_PAGE_SIZE

        # Take out the cursor param from the request
        with mutable(request.query_params) as query_params:
            cursor = query_params.get(paginator.cursor_query_param)
            if cursor:
                query_params.pop(paginator.cursor_query_param)

        # Fields that will be filtered on
        filter_fields = [x.split("__")[0] for x in request.query_params]

        # (Parent) model and contenttype for each field in the model
        field_contexts = get_field_contexts(model)

        # Check user has permission to filter the instances
        required, unknown = check_permissions(
            project=project,
            user=request.user,
            action="view",
            user_fields=filter_fields,
            field_contexts=field_contexts,
        )

        # Handle required permissions
        if required:
            return not_authorised_response(
                project=project,
                user=request.user,
                required=required,
            )

        # If unknown fields were provided, return 400
        if unknown:
            return Response(
                unknown,
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Get fields that can be viewed
        view_fields = get_fields_from_permissions(project.view_group.permissions.all())

        # Turn the request query params into a series of dictionaries, each that will be passed to a filterset
        filterset_datas = get_filterset_datas_from_query_params(request.query_params)

        # Initial queryset
        qs = init_queryset(model, view_fields)

        # Apply filtersets
        qs = apply_get_filterset(
            fs=METADBFilter,  # Filterset to use
            model=model,  # Model that the filterset is linked to
            field_contexts=field_contexts,
            view_fields=view_fields,  # Fields that the filterset can build filters for
            filterset_datas=filterset_datas,  # User data that determines how to apply the filterset
            qs=qs,  # Initial queryset
        )

        # If a response was returned, something went wrong
        # So this is returned to the user
        if isinstance(qs, Response):
            return qs

        # Add the pagination cursor param back into the request
        if cursor is not None:
            with mutable(request.query_params) as query_params:
                query_params[paginator.cursor_query_param] = cursor

        # Paginate the response
        instances = qs.order_by("id")
        result_page = paginator.paginate_queryset(instances, request)

        # Serialize the results
        serializer = get_serializer(model)(
            result_page,
            many=True,
            fields=view_fields,
            context={"field_contexts": field_contexts},
        )

        # Return paginated response
        self.API_RESPONSE.next = paginator.get_next_link()  # type: ignore
        self.API_RESPONSE.previous = paginator.get_previous_link()  # type: ignore
        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )


class QueryRecordView(METADBAPIView):
    permission_classes = ApprovedOrAdmin

    def post(self, request, project_code):
        """
        Filter and return instances for the given project.
        """
        # Get the project. If it does not exist, return 404
        project, model = get_project_and_model(project_code)
        if not project or not model:
            return Response(
                {project_code.lower(): [METADBAPIResponse.NOT_FOUND]},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Prepare paginator
        paginator = CursorPagination()
        paginator.ordering = "created"
        paginator.page_size = settings.CURSOR_PAGINATION_PAGE_SIZE

        # Take out the cursor param from the request
        with mutable(request.query_params) as query_params:
            cursor = query_params.get(paginator.cursor_query_param)
            if cursor:
                query_params.pop(paginator.cursor_query_param)

        # If request data was provided
        # Turn the value of each key-value pair in request.data into a 'KeyValue' object
        # A list of keyvalues is returned by make_keyvalues
        if request.data:
            try:
                keyvalues = make_keyvalues(request.data)
            except Exception:
                return Response(
                    {"detail": "invalid query"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            keyvalues = []

        # Fields that will be filtered on
        filter_fields = [x.key.split("__")[0] for x in keyvalues]

        # (Parent) model and contenttype for each field in the model
        field_contexts = get_field_contexts(model)

        # Check user has permission to filter the instances
        required, unknown = check_permissions(
            project=project,
            user=request.user,
            action="view",
            user_fields=filter_fields,
            field_contexts=field_contexts,
        )

        # Handle required permissions
        if required:
            return not_authorised_response(
                project=project,
                user=request.user,
                required=required,
            )

        # If unknown fields were provided, return 400
        if unknown:
            return Response(
                unknown,
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Get fields that can be viewed
        view_fields = get_fields_from_permissions(project.view_group.permissions.all())

        # Construct a list of dictionaries from the keyvalues
        # Each of these dictionaries will be passed to a filterset
        # The filterset is being used just to clean and validate the input filters
        # Until we construct the query, it doesn't matter how fields are related in the query (i.e. AND, OR, etc)
        # All that matters is if the individual filters and their values are valid
        filterset_datas = get_filterset_datas_from_keyvalues(keyvalues)

        # Apply filtersets (to validate the data only)
        validation = apply_query_filterset(
            fs=METADBFilter,  # Filterset to use
            model=model,  # Model that the filterset is linked to
            field_contexts=field_contexts,
            view_fields=view_fields,  # Fields that the filterset can build filters for
            filterset_datas=filterset_datas,  # User data that determines how to apply the filterset
        )

        # If a response was returned, something went wrong
        # So this is returned to the user
        if isinstance(validation, Response):
            return validation

        # Initial queryset
        qs = init_queryset(model, view_fields)

        # If request data was provided, then it has now been validated
        # So we form the query (a Q object)
        # Then filter using the Q object
        if request.data:
            try:
                query = get_query(request.data)
            except Exception:
                return Response(
                    {"detail": "invalid query"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            qs = qs.filter(query)

        # Add the pagination cursor param back into the request
        if cursor is not None:
            with mutable(request.query_params) as query_params:
                query_params[paginator.cursor_query_param] = cursor

        # Paginate the response
        instances = qs.order_by("id")
        result_page = paginator.paginate_queryset(instances, request)

        # Serialize the results
        serializer = get_serializer(model)(
            result_page,
            many=True,
            fields=view_fields,
            context={"field_contexts": field_contexts},
        )

        # Return paginated response
        self.API_RESPONSE.next = paginator.get_next_link()  # type: ignore
        self.API_RESPONSE.previous = paginator.get_previous_link()  # type: ignore
        return Response(serializer.data, status=status.HTTP_200_OK)


class UpdateRecordView(METADBAPIView):
    permission_classes = SameSiteAuthorityAsCIDOrAdmin

    def patch(self, request, project_code, cid, test=False):
        """
        Update an instance for the given project.
        """
        # Get the project. If it does not exist, return 404
        project, model = get_project_and_model(project_code)
        if not project or not model:
            return Response(
                {project_code.lower(): [METADBAPIResponse.NOT_FOUND]},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Get fields that can be viewed
        view_fields = get_fields_from_permissions(project.view_group.permissions.all())

        # Get the instance to be updated
        # If the instance does not exist, return 404
        try:
            instance = init_queryset(model, view_fields).get(cid=cid)
        except model.DoesNotExist:
            return Response(
                {cid: [METADBAPIResponse.NOT_FOUND]}, status=status.HTTP_404_NOT_FOUND
            )

        # Fields that will be updated
        update_fields = list(request.data)

        # (Parent) model and contenttype for each field in the model
        field_contexts = get_field_contexts(model)

        # Check user has permission to update the instance
        required, unknown = check_permissions(
            project=project,
            user=request.user,
            action="change",
            user_fields=update_fields,
            field_contexts=field_contexts,
        )

        # Handle required permissions
        if required:
            return not_authorised_response(
                project=project,
                user=request.user,
                required=required,
            )

        # If unknown fields were provided, return 400
        if unknown:
            return Response(
                unknown,
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Get the model serializer, and validate the data
        serializer = get_serializer(model)(
            instance=instance,
            data=request.data,
            partial=True,
            fields=view_fields,
            context={"field_contexts": field_contexts},
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

            return Response(
                serializer.data,
                status=status.HTTP_200_OK,
            )
        else:
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )


class SuppressRecordView(METADBAPIView):
    permission_classes = SameSiteAuthorityAsCIDOrAdmin

    def delete(self, request, project_code, cid, test=False):
        """
        Suppress an instance of the given project.
        """
        # Get the project. If it does not exist, return 404
        project, model = get_project_and_model(project_code)
        if not project or not model:
            return Response(
                {project_code.lower(): [METADBAPIResponse.NOT_FOUND]},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Get fields that can be viewed
        view_fields = get_fields_from_permissions(project.view_group.permissions.all())

        # Get the instance to be suppressed
        # If the instance does not exist, return 404
        try:
            instance = init_queryset(model, view_fields).get(cid=cid)
        except model.DoesNotExist:
            return Response(
                {cid: [METADBAPIResponse.NOT_FOUND]},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Fields that will be suppressed
        fields = get_serializer(model).Meta.fields
        suppress_fields = [
            x
            for x, y in model_to_dict(instance).items()
            if x in fields and y is not None
        ]

        # (Parent) model and contenttype for each field in the model
        field_contexts = get_field_contexts(model)

        # Check user has permission to suppress the instance
        required, unknown = check_permissions(
            project=project,
            user=request.user,
            action="suppress",
            user_fields=suppress_fields,
            field_contexts=field_contexts,
        )

        # Handle required permissions
        if required:
            return not_authorised_response(
                project=project,
                user=request.user,
                required=required,
            )

        # If unknown fields were provided, return 400
        if unknown:
            return Response(
                unknown,
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Suppress and save
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
        return Response(
            {"cid": cid},  # type: ignore
            status=status.HTTP_200_OK,
        )


class DeleteRecordView(METADBAPIView):
    permission_classes = Admin

    def delete(self, request, project_code, cid, test=False):
        """
        Permanently delete an instance of the given project.
        """
        # Get the project. If it does not exist, return 404
        project, model = get_project_and_model(project_code)
        if not project or not model:
            return Response(
                {project_code.lower(): [METADBAPIResponse.NOT_FOUND]},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Get fields that can be viewed
        view_fields = get_fields_from_permissions(project.view_group.permissions.all())

        # Get the instance to be deleted
        # If it does not exist, return 404
        try:
            instance = init_queryset(model, view_fields).get(cid=cid)
        except model.DoesNotExist:
            return Response(
                {cid: [METADBAPIResponse.NOT_FOUND]},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Fields that will be deleted
        delete_fields = [
            x
            for x, y in model_to_dict(instance).items()
            if x in get_serializer(model).Meta.fields and y is not None
        ]

        # (Parent) model and contenttype for each field in the model
        field_contexts = get_field_contexts(model)

        # Check user has permission to delete the instance
        required, unknown = check_permissions(
            project=project,
            user=request.user,
            action="delete",
            user_fields=delete_fields,
            field_contexts=field_contexts,
        )

        # Handle required permissions
        if required:
            return not_authorised_response(
                project=project,
                user=request.user,
                required=required,
            )

        # If unknown fields were provided, return 400
        if unknown:
            return Response(
                unknown,
                status=status.HTTP_400_BAD_REQUEST,
            )

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
        return Response(
            {"cid": cid},
            status=status.HTTP_200_OK,
        )
