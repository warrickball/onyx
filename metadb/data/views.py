from rest_framework import status
from rest_framework.response import Response
from rest_framework.pagination import CursorPagination
from django.conf import settings
from django.db.models import Q
from django.contrib.contenttypes.models import ContentType
from logging.handlers import RotatingFileHandler
import logging
import traceback
import operator
import functools

from .filters import METADBFilter
from .models import Project
from .serializers import get_serializer
from accounts.permissions import (
    Admin,
    ApprovedOrAdmin,
    SameSiteAuthorityAsCIDOrAdmin,
)
from utils.views import METADBAPIView
from utils.responses import METADBAPIResponse
from utils.functions import init_pathogen_queryset
from utils.contextmanagers import mutable


# TODO: Move elsewhere
logger = logging.getLogger("Rotating Log")
logger.setLevel(logging.ERROR)
handler = RotatingFileHandler(
    settings.INTERNAL_SERVER_ERROR_LOG_FILE,
    maxBytes=settings.INTERNAL_SERVER_ERROR_LOG_FILE_MAX_BYTES,
    backupCount=settings.INTERNAL_SERVER_ERROR_LOG_FILE_NUM_BACKUPS,
)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)


def get_project_model(project):
    """
    Returns the model for the given `project`, returning `None` if it doesn't exist.
    """
    if Project.objects.filter(code=project.lower()).exists():
        try:
            model = ContentType.objects.get(
                app_label="data", model=project.lower()
            ).model_class()

            return model

        except ContentType.DoesNotExist:
            pass

    return None


def check_permissions(user, model, action, user_fields):
    required = []
    unknown = []
    model_fields = {}
    models = [model] + model._meta.get_parent_list()

    for m in models:
        m_name = m._meta.model_name
        m_app_label = m._meta.app_label
        m_permission = f"{m_app_label}.{action}_{m_name}"

        if not user.has_perm(m_permission):
            required.append(m_permission)

        for f in m._meta.get_fields(include_parents=False):
            model_fields[f.name] = m

    for user_field in user_fields:
        if user_field not in model_fields:
            unknown.append(user_field)
            continue
        else:
            field_model = model_fields[user_field]
            field_model_name = field_model._meta.model_name
            field_model_app_label = field_model._meta.app_label
            field_permission = (
                f"{field_model_app_label}.{action}_{field_model_name}__{user_field}"
            )

            if not user.has_perm(field_permission):
                required.append(field_permission)

    if required:
        has_permission = False
    else:
        has_permission = True

    return has_permission, required, unknown


class ProjectView(METADBAPIView):
    permission_classes = ApprovedOrAdmin

    def get(self, request):
        """
        Get a list of `projects`.
        """
        # Check user has permissions to view the model
        authorised, required, _ = check_permissions(
            user=request.user,
            model=Project,
            action="view",
            user_fields=[],
        )

        # If not authorised, return 403
        if not authorised:
            return Response(
                {"denied_permissions": required},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Return a response containing a list of projects
        projects = Project.objects.all().values_list("code", flat=True)
        return Response({"projects": projects}, status=status.HTTP_200_OK)


class CreateProjectItemView(METADBAPIView):
    permission_classes = Admin

    def post(self, request, project):
        """
        Use `request.data` to save an instance for the model specified by `project`.
        """
        # Get the project model
        project_model = get_project_model(project)

        # If the project model does not exist, return 404
        if not project_model:
            return Response(
                {project: METADBAPIResponse.NOT_FOUND},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Check user has permissions to add both the model and the model fields that they want
        authorised, required, unknown = check_permissions(
            user=request.user,
            model=project_model,
            action="add",
            user_fields=list(request.data.keys()),
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

        # Get the model serializer, and validate the data
        serializer = get_serializer(project_model)(data=request.data)

        # If data is valid, save to the database. Otherwise, return 400
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GetProjectItemView(METADBAPIView):
    permission_classes = ApprovedOrAdmin

    def get(self, request, project):
        """
        Use `request.query_params` to filter data for the model specified by `project`.
        """
        try:
            # Get the corresponding model. The base class Pathogen is accepted when getting data
            pathogen_model = get_project_model(project)

            # If pathogen model does not exist, return error
            if pathogen_model is None:
                return Response(
                    {project: METADBAPIResponse.NOT_FOUND},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # Initialise the paginator
            paginator = CursorPagination()
            paginator.ordering = "created"
            paginator.page_size = settings.CURSOR_PAGINATION_PAGE_SIZE

            # Remove cursor, distinct and group parameters from the query params
            with mutable(request.query_params) as query_params:
                cursor = query_params.get(paginator.cursor_query_param)
                if cursor:
                    query_params.pop(paginator.cursor_query_param)

                distinct = query_params.get("distinct")
                if distinct:
                    query_params.pop("distinct")

                group = query_params.get("group")
                if group:
                    query_params.pop("group")

            # Get user serializer
            serializer = get_serializer(pathogen_model, request.user, group=group)

            # If the serializer returned a string, this is an indication something went wrong regarding the group
            # The error string is returned along with the name of the group
            if isinstance(serializer, str):
                return Response({group: serializer}, status=status.HTTP_400_BAD_REQUEST)

            data = {}
            num_filtersets = 0
            for field in request.query_params:
                values = list(set(request.query_params.getlist(field)))
                data[field] = values
                if len(values) > num_filtersets:
                    num_filtersets = len(values)

            filterset_datas = [{} for _ in range(num_filtersets)]
            for field, values in data.items():
                for i, value in enumerate(values):
                    filterset_datas[i][field] = value

            errors = {}

            # Initial queryset
            qs = init_pathogen_queryset(pathogen_model, user=request.user)

            for i, filterset_data in enumerate(filterset_datas):
                # Generate filterset of current queryset
                filterset = METADBFilter(
                    pathogen_model,
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

                    for field in filterset.base_filters:
                        if field not in serializer.Meta.fields:
                            errors[field] = [METADBAPIResponse.NON_ACCEPTED_FIELD]

                if not filterset.is_valid():
                    # Append any filterset errors to the errors dict
                    for field, msg in filterset.errors.items():
                        errors[field] = msg

            # Check the distinct field is a known field
            if distinct and (distinct not in pathogen_model.FILTER_FIELDS):
                errors[distinct] = [METADBAPIResponse.UNKNOWN_FIELD]

            # Return any errors that cropped up during filtering
            if errors:
                return Response(errors, status=status.HTTP_400_BAD_REQUEST)

            # If a parameter was provided for getting distinct results, apply it
            if distinct:
                qs = qs.distinct(distinct)

                # Serialize the results
                serialized = serializer(qs, many=True)

                return Response(serialized.data, status=status.HTTP_200_OK)
            else:
                # Non-distinct results have the potential to be quite large
                # So pagination (splitting the data into multiple pages) is used

                # Add the pagination cursor param back into the request
                if cursor is not None:
                    with mutable(request.query_params) as query_params:
                        query_params[paginator.cursor_query_param] = cursor

                # Paginate the response
                instances = qs.order_by("id")

                result_page = paginator.paginate_queryset(instances, request)

                # Serialize the results
                serialized = serializer(result_page, many=True)

                self.API_RESPONSE.next = paginator.get_next_link()  # type: ignore
                self.API_RESPONSE.previous = paginator.get_previous_link()  # type: ignore
                return Response(serialized.data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(str(e))
            logger.error(traceback.format_exc())
            return Response(
                {"detail": METADBAPIResponse.INTERNAL_SERVER_ERROR},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class QField:
    def __init__(self, key, value):
        self.key = key
        self.value = value


def make_qfields(data):
    key, value = next(iter(data.items()))

    if key in ["&", "|", "^", "~"]:
        for k_v in value:
            make_qfields(k_v)
    else:
        data[key] = QField(key, value)


def get_qfields_flat(data):
    """
    Traverses the provided `data`, that specifies an arbitrarily complex query, and returns a list of all `(key, value)` fields.
    """
    key, value = next(iter(data.items()))

    # AND of multiple key-value pairs
    if key == "&":
        k_v_objects = [get_qfields_flat(k_v) for k_v in value]
        return functools.reduce(operator.add, k_v_objects)

    # OR of multiple key-value pairs
    elif key == "|":
        k_v_objects = [get_qfields_flat(k_v) for k_v in value]
        return functools.reduce(operator.add, k_v_objects)

    # XOR of multiple key-value pairs
    elif key == "^":
        k_v_objects = [get_qfields_flat(k_v) for k_v in value]
        return functools.reduce(operator.add, k_v_objects)

    # NOT of a single key-value pair
    elif key == "~":
        k_v_object = [get_qfields_flat(k_v) for k_v in value][0]
        return k_v_object

    # Base case: a key-value pair we want to filter on
    else:
        return [(key, value)]


def get_query(data):
    """
    Traverses the provided `data`, that specifies an arbitrarily complex query, and forms the corresponding Q object.

    Also returns a flattened list of all `(key, value)` tuples used to form the Q object.
    """
    key, value = next(iter(data.items()))

    # AND of multiple key-value pairs
    if key == "&":
        q_objects = [get_query(k_v) for k_v in value]
        return functools.reduce(operator.and_, q_objects)

    # OR of multiple key-value pairs
    elif key == "|":
        q_objects = [get_query(k_v) for k_v in value]
        return functools.reduce(operator.or_, q_objects)

    # XOR of multiple key-value pairs
    elif key == "^":
        q_objects = [get_query(k_v) for k_v in value]
        return functools.reduce(operator.xor, q_objects)

    # NOT of a single key-value pair
    elif key == "~":
        q_object = [get_query(k_v) for k_v in value][0]
        return ~q_object

    # Base case: a key-value pair we want to filter on
    else:
        q = Q(
            **{value.key: value.value}
        )  # value is a QField (hopefully with clean data)
        return q


class QueryProjectItemView(METADBAPIView):
    permission_classes = ApprovedOrAdmin

    def post(self, request, project):
        try:
            # Get the corresponding model. The base class Pathogen is accepted when getting data
            pathogen_model = get_project_model(project)

            # If pathogen model does not exist, return error
            if pathogen_model is None:
                return Response(
                    {project: METADBAPIResponse.NOT_FOUND},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # Remove the group parameter from the request
            with mutable(request.query_params) as query_params:
                group = query_params.get("group")
                if group:
                    query_params.pop("group")

            # Turn the value of each key-value pair in request.data into a 'QField' object
            make_qfields(request.data)

            # Get flattened list of qfields
            qfields = get_qfields_flat(request.data)

            # Get user serializer
            serializer = get_serializer(pathogen_model, request.user, group=group)

            # If the serializer returned a string, this is an indication something went wrong regarding the group
            # The error string is returned along with the name of the group
            if isinstance(serializer, str):
                return Response({group: serializer}, status=status.HTTP_400_BAD_REQUEST)

            # Convert the key-value pairs into a structure that resembles the get request's query_params
            request_structured_data = {}
            for field, value in qfields:
                request_structured_data.setdefault(field, []).append(value)

            # Validate this structure using the filterset
            # This ensures the key-value pairs for this nested query go through the same validation as a standard get request
            data = {}
            num_filtersets = 0
            for field, values in request_structured_data.items():
                data[field] = values
                if len(values) > num_filtersets:
                    num_filtersets = len(values)

            filterset_datas = [{} for _ in range(num_filtersets)]
            for field, values in data.items():
                for i, value in enumerate(values):
                    filterset_datas[i][field] = value

            errors = {}

            for i, filterset_data in enumerate(filterset_datas):
                # Slightly cursed, but it works
                filterset = METADBFilter(
                    pathogen_model,
                    data={k: v.value for k, v in filterset_data.items()},
                    queryset=pathogen_model.objects.none(),
                )

                # On first pass, append any unknown fields to error dict
                if i == 0:
                    # Don't need to do more than i == 0, as here we have all the fields
                    for field in filterset_data:
                        if field not in filterset.filters:
                            errors[field] = [METADBAPIResponse.UNKNOWN_FIELD]

                    for field in filterset.base_filters:
                        if field not in serializer.Meta.fields:
                            errors[field] = [METADBAPIResponse.NON_ACCEPTED_FIELD]

                if errors or not filterset.is_valid():
                    # Append any filterset errors to the errors dict
                    for field, msg in filterset.errors.items():
                        errors[field] = msg

                else:
                    # Add clean value to the qfields
                    for k, qfield in filterset_data.items():
                        qfield.value = filterset.form.cleaned_data[k]

                    # Need to swap out provided aliases for actual field names
                    for field, field_data in pathogen_model.FILTER_FIELDS.items():
                        if field_data.get("alias"):
                            for k, v in filterset_data.items():
                                if k.startswith(
                                    field_data["alias"]
                                ) and not k.startswith(field):
                                    v.key = field + v.key.removeprefix(
                                        field_data["alias"]
                                    )

            if errors:
                return Response(errors, status=status.HTTP_400_BAD_REQUEST)

            # The data has been validated (to the best of my knowledge)
            # Form the query (a Q object)
            query = get_query(request.data)

            # Form the queryset, then filter by the Q object
            qs = init_pathogen_queryset(pathogen_model, user=request.user).filter(query)

            # Serialize the results
            serializer = serializer(qs, many=True)

            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(str(e))
            logger.error(traceback.format_exc())
            return Response(
                {"detail": METADBAPIResponse.INTERNAL_SERVER_ERROR},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class UpdateProjectItemView(METADBAPIView):
    permission_classes = SameSiteAuthorityAsCIDOrAdmin

    def patch(self, request, project, cid):
        """
        Use `request.data` and a `cid` to update an instance for the model specified by `project`.
        """
        # Get the project model
        project_model = get_project_model(project)

        # If the project model does not exist, return 404
        if not project_model:
            return Response(
                {project: METADBAPIResponse.NOT_FOUND},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Check user has permissions to change both the model and the model fields that they want
        authorised, required, unknown = check_permissions(
            user=request.user,
            model=project_model,
            action="change",
            user_fields=list(request.data.keys()),
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
            instance = project_model.objects.filter(suppressed=False).get(cid=cid)
        except project_model.DoesNotExist:
            return Response(
                {cid: METADBAPIResponse.NOT_FOUND}, status=status.HTTP_404_NOT_FOUND
            )

        # Get the model serializer, and validate the data
        serializer = get_serializer(project_model)(
            instance=instance, data=request.data, partial=True
        )

        # If data is valid, update existing record in the database. Otherwise, return 400
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SuppressProjectItemView(METADBAPIView):
    permission_classes = SameSiteAuthorityAsCIDOrAdmin

    def delete(self, request, project, cid):
        """
        Use the provided `project` and `cid` to suppress a record.
        """
        # Get the project model
        project_model = get_project_model(project)

        # If the project model does not exist, return 404
        if not project_model:
            return Response(
                {project: METADBAPIResponse.NOT_FOUND},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Check user has permissions to suppress instances of the model
        authorised, required, _ = check_permissions(
            user=request.user,
            model=project_model,
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
            instance = project_model.objects.filter(suppressed=False).get(cid=cid)
        except project_model.DoesNotExist:
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


class DeleteProjectItemView(METADBAPIView):
    permission_classes = Admin

    def delete(self, request, project, cid):
        """
        Use the provided `project` and `cid` to permanently delete a record.
        """
        # Get the project model
        project_model = get_project_model(project)

        # If the project model does not exist, return 404
        if not project_model:
            return Response(
                {project: METADBAPIResponse.NOT_FOUND},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Check user has permissions to delete instances of the model
        authorised, required, _ = check_permissions(
            user=request.user,
            model=project_model,
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
            project_model.objects.get(cid=cid).delete()
        except project_model.DoesNotExist:
            return Response(
                {cid: METADBAPIResponse.NOT_FOUND}, status=status.HTTP_404_NOT_FOUND
            )

        # Return response indicating deletion
        return Response({"cid": cid}, status=status.HTTP_200_OK)
