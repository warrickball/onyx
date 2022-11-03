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
from accounts.permissions import (
    IsAuthenticated,
    IsActiveUser,
    IsActiveSite,
    IsSiteApproved,
    IsAdminApproved,
    IsSiteAuthority,
    IsAdminUser,
    IsSameSiteAsUnsuppressedCID,
)
from utils.views import METADBAPIView
from utils.responses import METADBAPIResponse


logger = logging.getLogger("Rotating Log")
logger.setLevel(logging.ERROR)
handler = RotatingFileHandler(
    settings.LOG_FILE,
    maxBytes=settings.LOG_FILE_MAX_BYTES,
    backupCount=settings.LOG_FILE_NUM_BACKUPS,
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


def enforce_optional_value_groups(data, groups):
    """
    For each group in `groups`, verify that at least one field in the group is contained in `data`.
    """
    errors = {"required_fields": []}
    # A group is a list of field names where at least one of them is required
    for group in groups:
        for field in group:
            if field in data:
                break
        else:
            # If you're reading this I'm sorry
            # I couldn't help but try a for-else
            # I just found out it can be done, so I did it :)
            errors["required_fields"].append(
                {"At least one of the following fields is required.": group}
            )

    if errors["required_fields"]:
        return errors
    else:
        return {}


def enforce_field_set(data, accepted_fields, rejected_fields):
    """
    Check `data` for unknown fields, or known fields which cannot be accepted.
    """
    rejected = {}
    unknown = {}

    for field in data:
        if field in rejected_fields:
            rejected[field] = [METADBAPIResponse.NON_ACCEPTED_FIELD]
        elif field not in accepted_fields:
            unknown[field] = [METADBAPIResponse.UNKNOWN_FIELD]

    return rejected, unknown


class PathogenCodeView(METADBAPIView):
    permission_classes = [
        IsAuthenticated,
        IsActiveSite,
        IsActiveUser,
        ([IsSiteApproved, IsAdminApproved], IsAdminUser),
    ]

    def get(self, request):
        """
        Get a list of `pathogen_codes`, that correspond to tables in the database.
        """
        try:
            members = inspect.getmembers(models, inspect.isclass)
            pathogen_codes = []

            # For each model in data.models
            for name, model in members:
                # If the model inherits from Pathogen, add it to the list
                if Pathogen in model.__bases__:
                    pathogen_codes.append(name.upper())

            return Response(
                {"pathogen_codes": pathogen_codes}, status=status.HTTP_200_OK
            )

        except Exception as e:
            logger.error(str(e))
            logger.error(traceback.format_exc())
            return Response(
                {(type(e)).__name__: str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class CreateGetPathogenView(METADBAPIView):
    def get_permission_classes(self):
        if self.request.method == "POST":
            # Creating data requires being an admin user
            permission_classes = [
                IsAuthenticated,
                IsActiveSite,
                IsActiveUser,
                IsAdminUser,
            ]
        else:
            # Getting data requires being an authenticated, approved user (or an admin)
            permission_classes = [
                IsAuthenticated,
                IsActiveSite,
                IsActiveUser,
                ([IsSiteApproved, IsAdminApproved], IsAdminUser),
            ]
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

            # Check the request data contains only model fields allowed for creation
            rejected, unknown = enforce_field_set(
                data=request.data,
                accepted_fields=pathogen_model.create_fields(user=request.user),
                rejected_fields=pathogen_model.no_create_fields(user=request.user),
            )

            # Serializer also carries out validation of input data
            serializer = pathogen_model.get_serializer(user=request.user)(
                data=request.data
            )

            # Rejected fields (e.g. CID) are not allowed during creation
            errors = {}
            errors.update(rejected)

            # Unknown fields will be a warning
            self.API_RESPONSE.warnings.update(unknown)

            # If data is valid, save to the database. If not valid, return errors
            if serializer.is_valid() and not errors:
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                # Combine serializer errors with current errors
                errors.update(serializer.errors)
                return Response(errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.error(str(e))
            logger.error(traceback.format_exc())
            return Response(
                {(type(e)).__name__: str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def get(self, request, pathogen_code):
        """
        Use `request.query_params` to filter data for the model specified by `pathogen_code`.
        """
        try:
            # Get the corresponding model. The base class Pathogen is accepted when creating data
            pathogen_model = get_pathogen_model(pathogen_code, accept_base=True)

            # If pathogen model does not exist, return error
            if pathogen_model is None:
                return Response(
                    {pathogen_code: METADBAPIResponse.NOT_FOUND},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # Prepare paginator
            paginator = CursorPagination()
            paginator.ordering = "created"
            paginator.page_size = settings.CURSOR_PAGINATION_PAGE_SIZE

            _mutable = request.query_params._mutable
            request.query_params._mutable = True

            # Remove cursor parameter from the request, as its used for pagination and not filtering
            cursor = request.query_params.get(paginator.cursor_query_param)
            if cursor:
                request.query_params.pop(paginator.cursor_query_param)

            # Remove the distinct parameter from the request, as its not a filter parameter
            distinct = request.query_params.get("distinct")
            if distinct:
                request.query_params.pop("distinct")

            request.query_params._mutable = _mutable

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
                    user=request.user,
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
                serializer = pathogen_model.get_serializer(user=request.user)(
                    qs, many=True
                )

                return Response(serializer.data, status=status.HTTP_200_OK)
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
                serializer = pathogen_model.get_serializer(user=request.user)(
                    result_page, many=True
                )

                self.API_RESPONSE.next = paginator.get_next_link()  # type: ignore
                self.API_RESPONSE.previous = paginator.get_previous_link()  # type: ignore
                return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(str(e))
            logger.error(traceback.format_exc())
            return Response(
                {(type(e)).__name__: str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


def get_query(data):
    key, value = next(iter(data.items()))

    # OR
    if key == "|":
        q_objects = [get_query(k_v) for k_v in value]
        q_objects_or = functools.reduce(operator.or_, q_objects)
        return q_objects_or

    # AND
    elif key == "&":
        q_objects = [get_query(k_v) for k_v in value]
        q_objects_and = functools.reduce(operator.and_, q_objects)
        return q_objects_and

    # NOT
    elif key == "~":
        q_object = [get_query(k_v) for k_v in value][0]
        q_object_not = ~q_object
        return q_object_not

    else:
        q = Q(**{key: value})
        return q


class QueryPathogenView(METADBAPIView):
    permission_classes = [
        IsAuthenticated,
        IsActiveSite,
        IsActiveUser,
        ([IsSiteApproved, IsAdminApproved], IsAdminUser),
    ]

    def post(self, request, pathogen_code):
        try:
            # Get the corresponding model. The base class Pathogen is accepted when creating data
            pathogen_model = get_pathogen_model(pathogen_code, accept_base=True)

            # If pathogen model does not exist, return error
            if pathogen_model is None:
                return Response(
                    {pathogen_code: METADBAPIResponse.NOT_FOUND},
                    status=status.HTTP_404_NOT_FOUND,
                )

            query = get_query(request.data)

            # Initial queryset
            qs = pathogen_model.objects.filter(suppressed=False)
            qs = qs.filter(query)

            # Serialize the results
            serializer = pathogen_model.get_serializer(user=request.user)(qs, many=True)

            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(str(e))
            logger.error(traceback.format_exc())
            return Response(
                {(type(e)).__name__: str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class UpdateSuppressPathogenView(METADBAPIView):
    permission_classes = [
        IsAuthenticated,
        IsActiveSite,
        IsActiveUser,
        (
            [
                IsSiteApproved,
                IsAdminApproved,
                IsSiteAuthority,
                IsSameSiteAsUnsuppressedCID,
            ],
            IsAdminUser,
        ),
    ]

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

            # Check the request data contains only model fields allowed for updating
            rejected, unknown = enforce_field_set(
                data=request.data,
                accepted_fields=pathogen_model.update_fields(user=request.user),
                rejected_fields=pathogen_model.no_update_fields(user=request.user),
            )

            # Rejected fields (e.g. CID) are not allowed during updates
            errors = {}
            errors.update(rejected)

            # Unknown fields will be a warning
            self.API_RESPONSE.warnings.update(unknown)

            # Serializer also carries out validation of input data
            serializer = pathogen_model.get_serializer(user=request.user)(
                instance=instance, data=request.data, partial=True
            )

            # If data is valid, update existing record in the database. If not valid, return errors
            if serializer.is_valid() and not errors:
                if not serializer.validated_data:
                    errors.setdefault("non_field_errors", []).append(
                        "No fields were updated."
                    )
                    return Response(errors, status=status.HTTP_400_BAD_REQUEST)
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                # Combine serializer errors with current errors
                errors.update(serializer.errors)
                return Response(errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.error(str(e))
            logger.error(traceback.format_exc())
            return Response(
                {(type(e)).__name__: str(e)},
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
                {(type(e)).__name__: str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class DeletePathogenView(METADBAPIView):
    permission_classes = [
        IsAuthenticated,
        IsActiveSite,
        IsActiveUser,
        IsAdminUser,
    ]

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
                {(type(e)).__name__: str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
