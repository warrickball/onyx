from rest_framework import status
from rest_framework.response import Response
from rest_framework.pagination import CursorPagination
from django.conf import settings
from django.db.models import Q
from logging.handlers import RotatingFileHandler
import logging
import traceback
import inspect
import operator
import functools

from . import models
from .filters import METADBFilter
from .models import Pathogen
from .serializers import get_serializer
from accounts.permissions import (
    Admin,
    ApprovedOrAdmin,
    SameSiteAuthorityAsUnsuppressedCIDOrAdmin,
)
from utils.views import METADBAPIView
from utils.responses import METADBAPIResponse


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


def get_pathogen_model(pathogen_code, accept_base=False):
    """
    Returns the model for the given `pathogen_code`, returning `None` if it doesn't exist.
    """
    members = inspect.getmembers(models, inspect.isclass)

    for name, model in members:
        # Find model with matching name (case insensitive)
        if pathogen_code.upper() == name.upper():
            # Confirm whether the model inherits from the Pathogen class
            # If accept_base=True, we can also get the Pathogen class itself
            if Pathogen in model.__bases__ or (accept_base and model == Pathogen):
                return model

    return None


def enforce_field_set(data, user_fields, accepted_fields, rejected_fields):
    """
    Check `data` for unknown fields, or known fields which cannot be accepted.
    """
    rejected = {}
    unknown = {}

    for field in data:
        # Fields that are always rejected in the given scenario
        if field in rejected_fields:
            rejected[field] = [METADBAPIResponse.NON_ACCEPTED_FIELD]

        # Neither accepted or rejected, must be unknown
        elif field not in accepted_fields:
            unknown[field] = [METADBAPIResponse.UNKNOWN_FIELD]

        # By this stage, the field must be acceptable for the given scenario
        # But it may not be acceptable for this particular user
        elif field not in user_fields:
            rejected[field] = [METADBAPIResponse.NON_ACCEPTED_FIELD]

    return rejected, unknown


class PathogenCodeView(METADBAPIView):
    permission_classes = ApprovedOrAdmin

    def get(self, request):
        """
        Get a list of `pathogen_codes`, that correspond to tables in the database.
        """
        try:
            members = inspect.getmembers(models, inspect.isclass)
            pathogen_codes = []

            # For each model in data.models, check if it inherits from Pathogen
            # If so, add it to the list
            for name, model in members:
                if Pathogen in model.__bases__:
                    pathogen_codes.append(name.upper())

            return Response(
                {"pathogen_codes": pathogen_codes}, status=status.HTTP_200_OK
            )

        except Exception as e:
            logger.error(str(e))
            logger.error(traceback.format_exc())
            return Response(
                {"detail": METADBAPIResponse.INTERNAL_SERVER_ERROR},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class CreateGetPathogenView(METADBAPIView):
    def get_permission_classes(self):
        if self.request.method == "POST":
            # Creating data requires being an admin user
            permission_classes = Admin
        else:
            # Getting data requires being an authenticated, approved user (or an admin)
            permission_classes = ApprovedOrAdmin
        return permission_classes

    def post(self, request, pathogen_code):
        """
        Use `request.data` to save a model instance for the model specified by `pathogen_code`.
        """
        try:
            # Get the corresponding model. The base class Pathogen is NOT accepted when creating data
            pathogen_model = get_pathogen_model(pathogen_code, accept_base=False)

            # If pathogen model does not exist, return error
            if pathogen_model is None:
                return Response(
                    {pathogen_code: METADBAPIResponse.NOT_FOUND},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # If an immutable request body was provided, temporarily set to mutable
            # This is needed for tests to work
            mutable = getattr(request.data, "_mutable", None)
            if mutable is not None:
                mutable = request.data._mutable
                request.data._mutable = True

            # While mutable, remove the group parameter from the request body
            group = request.data.get("group")
            if group:
                request.data.pop("group")

            # Reset request body to immutable
            if mutable is not None:
                request.data._mutable = mutable

            # Get user serializer
            serializer = get_serializer(pathogen_model, request.user, group=group)

            # If the serializer returned a string, this is an indication something went wrong regarding the group
            # The error string is returned along with the name of the group
            if isinstance(serializer, str):
                return Response({group: serializer}, status=status.HTTP_400_BAD_REQUEST)

            # Check the request body contains only model fields allowed for creation
            # Also checking that the request body does not contain any fields outside the user's serializer fields
            rejected, unknown = enforce_field_set(
                data=request.data,
                user_fields=serializer.Meta.fields,
                accepted_fields=pathogen_model.create_fields(),
                rejected_fields=pathogen_model.no_create_fields(),
            )

            # Serializer carries out validation of input request body values
            serialized = serializer(data=request.data)

            # Rejected fields (e.g. CID) are not allowed during creation
            errors = {}
            errors.update(rejected)

            # Unknown fields will show up as a warning
            self.API_RESPONSE.warnings.update(unknown)

            # If data is valid, save to the database. If not valid, return errors
            if serialized.is_valid() and not errors:
                serialized.save()
                return Response(serialized.data, status=status.HTTP_201_CREATED)
            else:
                # Combine serializer errors with current errors
                errors.update(serialized.errors)
                return Response(errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.error(str(e))
            logger.error(traceback.format_exc())
            return Response(
                {"detail": METADBAPIResponse.INTERNAL_SERVER_ERROR},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def get(self, request, pathogen_code):
        """
        Use `request.query_params` to filter data for the model specified by `pathogen_code`.
        """
        try:
            # Get the corresponding model. The base class Pathogen is accepted when getting data
            pathogen_model = get_pathogen_model(pathogen_code, accept_base=True)

            # If pathogen model does not exist, return error
            if pathogen_model is None:
                return Response(
                    {pathogen_code: METADBAPIResponse.NOT_FOUND},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # Initialise the paginator
            paginator = CursorPagination()
            paginator.ordering = "created"
            paginator.page_size = settings.CURSOR_PAGINATION_PAGE_SIZE

            # Set the request query params object to mutable
            _mutable = request.query_params._mutable
            request.query_params._mutable = True

            # While mutable remove cursor, distinct and group parameters from the query params
            # These params are considered separately and are not used for filtering
            cursor = request.query_params.get(paginator.cursor_query_param)
            if cursor:
                request.query_params.pop(paginator.cursor_query_param)

            distinct = request.query_params.get("distinct")
            if distinct:
                request.query_params.pop("distinct")

            group = request.query_params.get("group")
            if group:
                request.query_params.pop("group")

            # Reset query params to immutable
            request.query_params._mutable = _mutable

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
            qs = pathogen_model.objects.filter(suppressed=False)

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
                    _mutable = request.query_params._mutable
                    request.query_params._mutable = True
                    request.query_params[paginator.cursor_query_param] = cursor
                    request.query_params._mutable = _mutable

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


def get_query(data):
    """
    Traverses the provided `data`, that specifies an arbitrarily complex query, and forms the corresponding Q object.

    Also returns a flattened list of all `(key, value)` tuples used to form the Q object.
    """
    key, value = next(iter(data.items()))

    # AND of multiple key-value pairs
    if key == "&":
        q_objects, k_v_objects = zip(*(get_query(k_v) for k_v in value))
        return functools.reduce(operator.and_, q_objects), functools.reduce(
            operator.add, k_v_objects
        )

    # OR of multiple key-value pairs
    elif key == "|":
        q_objects, k_v_objects = zip(*(get_query(k_v) for k_v in value))
        return functools.reduce(operator.or_, q_objects), functools.reduce(
            operator.add, k_v_objects
        )

    # XOR of multiple key-value pairs
    elif key == "^":
        q_objects, k_v_objects = zip(*(get_query(k_v) for k_v in value))
        return functools.reduce(operator.xor, q_objects), functools.reduce(
            operator.add, k_v_objects
        )

    # NOT of a single key-value pair
    elif key == "~":
        q_object, k_v_object = [get_query(k_v) for k_v in value][0]
        return ~q_object, k_v_object

    # Base case: a key-value pair we want to filter on
    else:
        q = Q(**{key: value})
        return q, [(key, value)]


class QueryPathogenView(METADBAPIView):
    permission_classes = ApprovedOrAdmin

    def post(self, request, pathogen_code):
        try:
            # Get the corresponding model. The base class Pathogen is accepted when getting data
            pathogen_model = get_pathogen_model(pathogen_code, accept_base=True)

            # If pathogen model does not exist, return error
            if pathogen_model is None:
                return Response(
                    {pathogen_code: METADBAPIResponse.NOT_FOUND},
                    status=status.HTTP_404_NOT_FOUND,
                )

            _mutable = request.query_params._mutable
            request.query_params._mutable = True

            # Remove the group parameter from the request, as its not a filter parameter
            group = request.query_params.get("group")
            if group:
                request.query_params.pop("group")

            request.query_params._mutable = _mutable

            # Get user serializer
            serializer = get_serializer(pathogen_model, request.user, group=group)

            if isinstance(serializer, str):
                return Response({group: serializer}, status=status.HTTP_400_BAD_REQUEST)

            # Get Q object for the users query, as well as the fields used to form it
            query, fields = get_query(request.data)

            # Convert the key-value pairs used to form the Q object in to a structure that resembles the get request's query_params
            request_structured_data = {}
            for field, value in fields:
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
                    data=filterset_data,
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

                if not filterset.is_valid():
                    # Append any filterset errors to the errors dict
                    for field, msg in filterset.errors.items():
                        errors[field] = msg

            if errors:
                return Response(errors, status=status.HTTP_400_BAD_REQUEST)

            # The data has been validated (to the best of my knowledge)
            # Now form the initial queryset, and filter by the Q object
            qs = pathogen_model.objects.filter(suppressed=False)
            qs = qs.filter(query)

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


class UpdateSuppressPathogenView(METADBAPIView):
    permission_classes = SameSiteAuthorityAsUnsuppressedCIDOrAdmin

    def patch(self, request, pathogen_code, cid):
        """
        Use `request.data` and a `cid` to update an instance for the model specified by `pathogen_code`.
        """
        try:
            # Get the corresponding model. The base class Pathogen is accepted when updating data
            pathogen_model = get_pathogen_model(pathogen_code, accept_base=True)

            # If pathogen model does not exist, return error
            if pathogen_model is None:
                return Response(
                    {pathogen_code: METADBAPIResponse.NOT_FOUND},
                    status=status.HTTP_404_NOT_FOUND,
                )

            try:
                # Get the instance to be updated
                instance = pathogen_model.objects.get(suppressed=False, cid=cid)
            except pathogen_model.DoesNotExist:
                # If cid did not exist, return error
                return Response(
                    {cid: METADBAPIResponse.NOT_FOUND}, status=status.HTTP_404_NOT_FOUND
                )

            mutable = getattr(request.data, "_mutable", None)
            if mutable is not None:
                mutable = request.data._mutable
                request.data._mutable = True

            # Remove the group parameter from the request
            group = request.data.get("group")
            if group:
                request.data.pop("group")

            if mutable is not None:
                request.data._mutable = mutable

            # Get user serializer
            serializer = get_serializer(pathogen_model, request.user, group=group)

            if isinstance(serializer, str):
                return Response({group: serializer}, status=status.HTTP_400_BAD_REQUEST)

            # Check the request data contains only model fields allowed for updating
            rejected, unknown = enforce_field_set(
                data=request.data,
                user_fields=serializer.Meta.fields,
                accepted_fields=pathogen_model.update_fields(),
                rejected_fields=pathogen_model.no_update_fields(),
            )

            # Rejected fields (e.g. CID) are not allowed during updates
            errors = {}
            errors.update(rejected)

            # Unknown fields will be a warning
            self.API_RESPONSE.warnings.update(unknown)

            # Serializer also carries out validation of input data
            serialized = serializer(instance=instance, data=request.data, partial=True)

            # If data is valid, update existing record in the database. If not valid, return errors
            if serialized.is_valid() and not errors:
                if not serialized.validated_data:
                    errors.setdefault("non_field_errors", []).append(
                        "No fields were updated."
                    )
                    return Response(errors, status=status.HTTP_400_BAD_REQUEST)
                serialized.save()
                return Response(serialized.data, status=status.HTTP_200_OK)
            else:
                # Combine serializer errors with current errors
                errors.update(serialized.errors)
                return Response(errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.error(str(e))
            logger.error(traceback.format_exc())
            return Response(
                {"detail": METADBAPIResponse.INTERNAL_SERVER_ERROR},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def delete(self, request, pathogen_code, cid):
        """
        Use the provided `pathogen_code` and `cid` to suppress a record.
        """
        try:
            # Get the corresponding model. The base class Pathogen is accepted when suppressing data
            pathogen_model = get_pathogen_model(pathogen_code, accept_base=True)

            # If pathogen model does not exist, return error
            if pathogen_model is None:
                return Response(
                    {pathogen_code: METADBAPIResponse.NOT_FOUND},
                    status=status.HTTP_404_NOT_FOUND,
                )

            try:
                # Get the instance to be suppressed
                instance = pathogen_model.objects.get(suppressed=False, cid=cid)
            except pathogen_model.DoesNotExist:
                # If cid did not exist, return error
                return Response(
                    {cid: METADBAPIResponse.NOT_FOUND}, status=status.HTTP_404_NOT_FOUND
                )

            # Suppress and save
            instance.suppressed = True
            instance.save(update_fields=["suppressed"])

            # Just to double check
            try:
                # Get the instance to be suppressed
                instance = pathogen_model.objects.get(cid=cid)
            except pathogen_model.DoesNotExist:
                # If cid did not exist, return error
                return Response(
                    {cid: METADBAPIResponse.NOT_FOUND}, status=status.HTTP_404_NOT_FOUND
                )

            # Return the details
            return Response(
                {"cid": cid, "suppressed": instance.suppressed},
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.error(str(e))
            logger.error(traceback.format_exc())
            return Response(
                {"detail": METADBAPIResponse.INTERNAL_SERVER_ERROR},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class DeletePathogenView(METADBAPIView):
    permission_classes = Admin

    def delete(self, request, pathogen_code, cid):
        """
        Use the provided `pathogen_code` and `cid` to permanently delete a record.
        """
        try:
            # Get the corresponding model. The base class Pathogen is accepted when deleting data
            pathogen_model = get_pathogen_model(pathogen_code, accept_base=True)

            # If pathogen model does not exist, return error
            if pathogen_model is None:
                return Response(
                    {pathogen_code: METADBAPIResponse.NOT_FOUND},
                    status=status.HTTP_404_NOT_FOUND,
                )

            try:
                # Attempt to delete object with the provided cid
                pathogen_model.objects.get(cid=cid).delete()
            except pathogen_model.DoesNotExist:
                # If cid did not exist, return error
                return Response(
                    {cid: METADBAPIResponse.NOT_FOUND}, status=status.HTTP_404_NOT_FOUND
                )

            deleted = not pathogen_model.objects.filter(cid=cid).exists()
            return Response({"cid": cid, "deleted": deleted}, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(str(e))
            logger.error(traceback.format_exc())
            return Response(
                {"detail": METADBAPIResponse.INTERNAL_SERVER_ERROR},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
