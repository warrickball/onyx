from rest_framework import status
from rest_framework.response import Response
from rest_framework.pagination import CursorPagination
from django.conf import settings
from accounts.permissions import (
    Admin,
    ApprovedOrAdmin,
    SameSiteAuthorityAsCIDOrAdmin,
)
from utils.views import METADBAPIView
from utils.classes import METADBAPIResponse
from utils.functions import (
    make_keyvalues,
    get_query,
    check_permissions,
    get_view_permissions_and_fields,
    get_project_and_model,
)
from utils.contextmanagers import mutable
from internal.models import Project
from .filters import METADBFilter
from .serializers import get_serializer


class CreateRecordView(METADBAPIView):
    permission_classes = Admin

    def post(self, request, project_code):
        """
        Create an instance for the given project.
        """
        # Get the project. If it does not exist, return 404
        project, model = get_project_and_model(project_code)
        if not project or not model:
            return Response(
                {project_code: METADBAPIResponse.NOT_FOUND},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Get required view permissions and their corresponding fieldnames
        view_permissions, view_fields = get_view_permissions_and_fields(project)

        # Check user has permissions to add both the model and the model fields that they want
        authorised, required, unknown = check_permissions(
            user=request.user,
            model=model,
            default_permissions=view_permissions,
            action="add",
            user_fields=list(request.data),
        )

        # If not authorised, return 403
        if not authorised:
            return Response(
                {"denied_permissions": required},
                status=status.HTTP_403_FORBIDDEN,
            )

        # If unknown fields were provided, return 400
        if unknown:
            return Response(
                {"unknown_fields": [unknown]}, status=status.HTTP_400_BAD_REQUEST
            )

        # If a site code was not provided, use the user's site code
        if not request.data.get("site"):
            request.data["site"] = request.user.site.code

        # Get the model serializer, and validate the data
        serializer = get_serializer(model)(data=request.data, fields=view_fields)

        # If data is valid, save to the database. Otherwise, return 400
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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
                {project_code: METADBAPIResponse.NOT_FOUND},
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

        # Get required view permissions and their corresponding fieldnames
        view_permissions, view_fields = get_view_permissions_and_fields(project)

        # Check user has permissions to view both the model and the model fields that they want
        authorised, required, unknown = check_permissions(
            user=request.user,
            model=model,
            default_permissions=view_permissions,
            action="view",
            user_fields=[x.split("__")[0] for x in request.query_params],
        )

        # If not authorised, return 403
        if not authorised:
            return Response(
                {"denied_permissions": required},
                status=status.HTTP_403_FORBIDDEN,
            )

        # If unknown fields were provided, return 400
        if unknown:
            return Response(
                {"unknown_fields": [unknown]}, status=status.HTTP_400_BAD_REQUEST
            )

        # Turn the request query params into a series of dictionaries, each that will be passed to a filterset
        filterset_datas = []
        for field in request.query_params:
            values = list(set(request.query_params.getlist(field)))

            for i, value in enumerate(values):
                if len(filterset_datas) == i:
                    filterset_datas.append({})

                filterset_datas[i][field] = value

        # Dictionary of filterset errors
        errors = {}

        # Initial queryset
        qs = model.objects.filter(suppressed=False)

        # A filterset can only take a a query with one of each field at a time
        # So given that the get view only AND's fields together, we can represent this
        # as a series of filtersets ANDed together
        for i, filterset_data in enumerate(filterset_datas):
            # Generate filterset of current queryset
            filterset = METADBFilter(
                model,
                data=filterset_data,
                queryset=qs,
            )
            # Retrieve the resulting filtered queryset
            qs = filterset.qs

            # On first pass, append any unknown fields to error dict
            if i == 0:
                # Don't need to do more than i == 0, as here we have all the fields
                for field in filterset_data:
                    if field not in filterset.filters:
                        errors[field] = [METADBAPIResponse.UNKNOWN_FIELD]

                # for field in filterset.base_filters:
                #     if field not in serializer.Meta.fields:
                #         errors[field] = [METADBAPIResponse.NON_ACCEPTED_FIELD]

            if not filterset.is_valid():
                # Append any filterset errors to the errors dict
                for field, msg in filterset.errors.items():
                    errors[field] = msg

        # Return any errors that cropped up during filtering
        if errors:
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)

        # Add the pagination cursor param back into the request
        if cursor is not None:
            with mutable(request.query_params) as query_params:
                query_params[paginator.cursor_query_param] = cursor

        # Paginate the response
        instances = qs.order_by("id")
        result_page = paginator.paginate_queryset(instances, request)

        # Serialize the results
        serializer = get_serializer(model)(result_page, many=True, fields=view_fields)

        # Return paginated response
        self.API_RESPONSE.next = paginator.get_next_link()  # type: ignore
        self.API_RESPONSE.previous = paginator.get_previous_link()  # type: ignore
        return Response(serializer.data, status=status.HTTP_200_OK)


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
                {project_code: METADBAPIResponse.NOT_FOUND},
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

        if request.data:
            # Turn the value of each key-value pair in request.data into a 'KeyValue' object
            # Returns a list of the keyvalues
            try:
                keyvalues = make_keyvalues(request.data)
            except Exception:
                return Response(
                    {"detail": "invalid query"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            keyvalues = []

        # Get required view permissions and their corresponding fieldnames
        view_permissions, view_fields = get_view_permissions_and_fields(project)

        # Check user has permissions to view both the model and the model fields that they want
        authorised, required, unknown = check_permissions(
            user=request.user,
            model=model,
            default_permissions=view_permissions,
            action="view",
            user_fields=[x.key.split("__")[0] for x in keyvalues],
        )

        # If not authorised, return 403
        if not authorised:
            return Response(
                {"denied_permissions": required},
                status=status.HTTP_403_FORBIDDEN,
            )

        # If unknown fields were provided, return 400
        if unknown:
            return Response(
                {"unknown_fields": [unknown]}, status=status.HTTP_400_BAD_REQUEST
            )

        # Construct a list of dictionaries from the keyvalues
        # Each of these dictionaries will be passed to a filterset
        # The filterset is being used just to clean and validate the input filters
        # Until we construct the query, it doesn't matter how fields are related in the query (i.e. AND, OR, etc)
        # All that matters is if the individual filters and their values are valid
        filterset_datas = [{}]
        for keyvalue in keyvalues:
            # Place the keyvalue in the first dictionary where the key is not present
            # If we reach the end with no placement, create a new dictionary and add it in there
            for filterset_data in filterset_datas:
                if keyvalue.key not in filterset_data:
                    filterset_data[keyvalue.key] = keyvalue
                    break
            else:
                filterset_datas.append({keyvalue.key: keyvalue})

        # Dictionary of filterset errors
        errors = {}

        # Use a filterset, applied to each dict in filterset_datas, to validate the data
        for i, filterset_data in enumerate(filterset_datas):
            # Slightly cursed, but it works
            filterset = METADBFilter(
                model,
                data={k: v.value for k, v in filterset_data.items()},
                queryset=model.objects.none(),
            )

            # On first pass, append any unknown fields to error dict
            # Don't need to do more than i == 0, as here we have all the fields
            if i == 0:
                # Don't need to do more than i == 0, as here we have all the fields
                for field in filterset_data:
                    if field not in filterset.filters:
                        errors[field] = [METADBAPIResponse.UNKNOWN_FIELD]

                # for field in filterset.base_filters:
                #     if field not in serializer.Meta.fields:
                #         errors[field] = [METADBAPIResponse.NON_ACCEPTED_FIELD]

            # Append any filterset errors to the errors dict
            if not filterset.is_valid():
                for field, msg in filterset.errors.items():
                    errors[field] = msg
            else:
                # Add the cleaned values to the KeyValue objects
                for k, keyvalue in filterset_data.items():
                    keyvalue.value = filterset.form.cleaned_data[k]

                # Need to swap out provided aliases for actual field names
                for field, field_data in model.FILTER_FIELDS.items():  # type: ignore
                    if field_data.get("alias"):
                        for k, v in filterset_data.items():
                            if k.startswith(field_data["alias"]) and not k.startswith(
                                field
                            ):
                                v.key = field + v.key.removeprefix(field_data["alias"])

        # Return any errors that cropped up during validation
        if errors:
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)

        # Initial queryset
        qs = model.objects.filter(suppressed=False)

        if request.data:
            # The data has been validated so we form the query (a Q object)
            try:
                query = get_query(request.data)
            except Exception:
                return Response(
                    {"detail": "invalid query"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Then filter using the Q object
            qs = qs.filter(query)

        # Add the pagination cursor param back into the request
        if cursor is not None:
            with mutable(request.query_params) as query_params:
                query_params[paginator.cursor_query_param] = cursor

        # Paginate the response
        instances = qs.order_by("id")
        result_page = paginator.paginate_queryset(instances, request)

        # Serialize the results
        serializer = get_serializer(model)(result_page, many=True, fields=view_fields)

        # Return paginated response
        self.API_RESPONSE.next = paginator.get_next_link()  # type: ignore
        self.API_RESPONSE.previous = paginator.get_previous_link()  # type: ignore
        return Response(serializer.data, status=status.HTTP_200_OK)


class UpdateRecordView(METADBAPIView):
    permission_classes = SameSiteAuthorityAsCIDOrAdmin

    def patch(self, request, project_code, cid):
        """
        Update an instance for the given project.
        """
        # Get the project. If it does not exist, return 404
        project, model = get_project_and_model(project_code)
        if not project or not model:
            return Response(
                {project_code: METADBAPIResponse.NOT_FOUND},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Get required view permissions and their corresponding fieldnames
        view_permissions, view_fields = get_view_permissions_and_fields(project)

        # Check user has permissions to change both the model and the model fields that they want
        authorised, required, unknown = check_permissions(
            user=request.user,
            model=model,
            default_permissions=view_permissions,
            action="change",
            user_fields=list(request.data),
        )

        # If not authorised, return 403
        if not authorised:
            return Response(
                {"denied_permissions": required},
                status=status.HTTP_403_FORBIDDEN,
            )

        # If unknown fields were provided, return 400
        if unknown:
            return Response(
                {"unknown_fields": [unknown]}, status=status.HTTP_400_BAD_REQUEST
            )

        # Get the instance to be updated
        # If the instance does not exist, return 404
        try:
            instance = model.objects.filter(suppressed=False).get(cid=cid)
        except model.DoesNotExist:
            return Response(
                {cid: METADBAPIResponse.NOT_FOUND}, status=status.HTTP_404_NOT_FOUND
            )

        # Get the model serializer, and validate the data
        serializer = get_serializer(model)(
            instance=instance, data=request.data, partial=True, fields=view_fields
        )

        # If data is valid, update existing record in the database. Otherwise, return 400
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SuppressRecordView(METADBAPIView):
    permission_classes = SameSiteAuthorityAsCIDOrAdmin

    def delete(self, request, project_code, cid):
        """
        Suppress an instance of the given project.
        """
        # Get the project. If it does not exist, return 404
        project, model = get_project_and_model(project_code)
        if not project or not model:
            return Response(
                {project_code: METADBAPIResponse.NOT_FOUND},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Get required view permissions and their corresponding fieldnames
        view_permissions, _ = get_view_permissions_and_fields(project)

        # Check user has permissions to suppress instances of the model
        authorised, required, _ = check_permissions(
            user=request.user,
            model=model,
            default_permissions=view_permissions,
            action="suppress",
            user_fields=[],
        )

        # If not authorised, return 403
        if not authorised:
            return Response(
                {"denied_permissions": required},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Get the instance to be suppressed
        # If the instance does not exist, return 404
        try:
            instance = model.objects.filter(suppressed=False).get(cid=cid)
        except model.DoesNotExist:
            return Response(
                {cid: METADBAPIResponse.NOT_FOUND}, status=status.HTTP_404_NOT_FOUND
            )

        # Suppress and save
        instance.suppressed = True  # type: ignore
        instance.save(update_fields=["suppressed", "last_modified"])

        # Return response indicating suppression
        return Response(
            {"cid": cid},  # type: ignore
            status=status.HTTP_200_OK,
        )


class DeleteRecordView(METADBAPIView):
    permission_classes = Admin

    def delete(self, request, project_code, cid):
        """
        Permanently delete an instance of the given project.
        """
        # Get the project. If it does not exist, return 404
        project, model = get_project_and_model(project_code)
        if not project or not model:
            return Response(
                {project_code: METADBAPIResponse.NOT_FOUND},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Get required view permissions and their corresponding fieldnames
        view_permissions, _ = get_view_permissions_and_fields(project)

        # Check user has permissions to delete instances of the model
        authorised, required, _ = check_permissions(
            user=request.user,
            model=model,
            default_permissions=view_permissions,
            action="delete",
            user_fields=[],
        )

        # If not authorised, return 403
        if not authorised:
            return Response(
                {"denied_permissions": required},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Attempt to delete the instance
        # If the instance does not exist, return 404
        try:
            model.objects.get(cid=cid).delete()
        except model.DoesNotExist:
            return Response(
                {cid: METADBAPIResponse.NOT_FOUND}, status=status.HTTP_404_NOT_FOUND
            )

        # Return response indicating deletion
        return Response({"cid": cid}, status=status.HTTP_200_OK)
