from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.pagination import CursorPagination
from rest_framework.views import APIView
from rest_framework.exceptions import ErrorDetail
from django.shortcuts import get_object_or_404
from django.http import Http404
from django.conf import settings
from django.core.exceptions import FieldDoesNotExist
from . import serializers, models
from .models import Pathogen
from accounts.views import IsApproved
from utils.responses import Responses
from data.tasks import generate_stats
import inspect



def get_pathogen_model_or_404(pathogen_code):
    '''
    Returns the model for the given `pathogen_code`, raising a `Http404` if it doesn't exist.
    '''
    members = inspect.getmembers(models, inspect.isclass)
    for name, model in members:
        if pathogen_code.upper() == name.upper() and (model == Pathogen or Pathogen in model.__bases__):
            return model
    raise Http404



def process_data(data, model, forbidden_fields, ignore_lookups=False, enforce_optional_value_groups=False):
    all_fields = model.all_fields()
    choice_fields = model.choice_fields()
    invalid_fields = {}

    for field in data:
        full_field = field
        if ignore_lookups:
            try:
                dunders = field.split("__")
                # TODO: this doesnt work for 1-to-1 relations e.g. fasta__pc_acgt
                lookups = model._meta.get_field(dunders[0]).get_lookups()
                if len(dunders) > 1 and dunders[-1] in lookups:
                    field = "__".join(dunders[:-1])
            except FieldDoesNotExist:
                pass

        if field not in all_fields:
            invalid_fields[field] = [
                ErrorDetail(
                    string="This field is unknown.",
                    code="unknown"
                )
            ]
        elif field in forbidden_fields:
            invalid_fields[field] = [
                ErrorDetail(
                    string="This field is forbidden.",
                    code="forbidden"
                )
            ]
        elif field in choice_fields:
            valid_choice = False
            choices = model.get_choices(field)

            for choice in choices:
                if data[full_field].upper() == choice.upper():
                    data[full_field] = choice
                    valid_choice = True
            
            if not valid_choice:
                invalid_fields[full_field] = [
                    ErrorDetail(
                        string=f"'{data[full_field]}' is not a valid choice.",
                        code="invalid"
                    ),
                    {"Valid choices" : choices}
                ]
    
    if enforce_optional_value_groups:
        for group in model.optional_value_groups():
            at_least_one = False
            for field in group:
                if field in data:
                    at_least_one = True
                    break
            if not at_least_one:
                if not invalid_fields.get("optional_value_errors"):
                    invalid_fields["optional_value_errors"] = []
                invalid_fields["optional_value_errors"].append(
                    [
                        "At least one of the following fields is required.",
                        {"Fields" : group}
                    ]
                )

    return invalid_fields



class PathogenCodeView(APIView):
    permission_classes = [IsAuthenticated, IsApproved]

    def get(self, request):
        members = inspect.getmembers(models, inspect.isclass)
        pathogen_codes = []
        for name, model in members:
            if Pathogen in model.__bases__:
                pathogen_codes.append(name.upper())
        return Response({"pathogen_codes" : pathogen_codes}, status=status.HTTP_200_OK)



class CreateGetPathogenView(APIView):
    permission_classes = [IsAuthenticated, IsApproved]

    def post(self, request, pathogen_code):
        '''
        Creates a new record using `request.data`, for the model specified by `pathogen_code`.
        '''
        pathogen_model = get_pathogen_model_or_404(pathogen_code)

        # If a pathogen_code was provided in the body, and it doesn't match the url, tell them to stop it
        request_pathogen_code = request.data.get("pathogen_code")
        if request_pathogen_code and request_pathogen_code.upper() != pathogen_code.upper():
            return Responses._400_mismatch_pathogen_code
        
        # If an institute was provided, check it matches the user's institute
        request_institute_code = request.data.get("institute")
        if request_institute_code and request_institute_code.upper() != request.user.institute.code: 
            return Responses._403_incorrect_institute_for_user

        # Custom processing and validation of data
        invalid_fields = process_data(
            data=request.data,
            model=pathogen_model,
            forbidden_fields=pathogen_model.internal_fields(),
            enforce_optional_value_groups=True
        )

        # Serializer also carries out validation of input data
        serializer = getattr(serializers, f"{pathogen_model.__name__}Serializer")(data=request.data)

        # If data is valid, save to the database. If invalid, return errors
        if serializer.is_valid() and (not invalid_fields):
            instance = serializer.save()
            generate_stats.delay(instance.cid, instance.fasta_path, instance.bam_path)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            # Combine serializer and custom errors
            errors = dict(serializer.errors)
            for field, value in invalid_fields.items():
                errors[field] = value
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)


    def get(self, request, pathogen_code):
        '''
        Uses `request.query_params` to filter and return data for the given `pathogen_code`.
        '''
        pathogen_model = get_pathogen_model_or_404(pathogen_code)
        
        _mutable = request.query_params._mutable
        request.query_params._mutable = True

        # Take out the query params we do not wish to filter on
        cursor = request.query_params.pop("cursor", None)
        if cursor:
            cursor = cursor[-1]
        stats = request.query_params.pop("stats", None)
        if stats:
            stats = stats[-1]

        # Custom processing and validation of data
        invalid_fields = process_data(
            data=request.query_params,
            model=pathogen_model,
            forbidden_fields={},
            ignore_lookups=True
        )

        request.query_params._mutable = _mutable

        # Create queryset of all non-suppressed objects by default
        instances = pathogen_model.objects.filter(suppressed=False)

        # For each query param, filter the data
        for field in request.query_params:
            values = request.query_params.getlist(field)
            
            if field == "institute":
                # A regrettably hardcoded default that makes queries much more user friendly
                field = "institute__code"
            
            for value in values:
                try:
                    if value == settings.FIELD_NULL_TOKEN:
                        value = None
                    instances = instances.filter(**{field : value})
                except Exception as e:
                    if not invalid_fields.get(field):
                        # This line looks dreadful but its just replacing a specific annoying bit of unicode present in lots of django errors
                        # Worst case is I missed some slightly different unicode and the user gets a weird error message
                        invalid_fields[field] = [str(e.args[0]).replace("\u201c%(value)s\u201d value", f"'{value}'")]

        # If validation and/or filtering failed, return a response with the details
        if invalid_fields:
            return Response(invalid_fields, status=status.HTTP_400_BAD_REQUEST)

        # Add the cursor back in to query params as its needed for pagination
        if cursor is not None:
            _mutable = request.query_params._mutable
            request.query_params._mutable = True
            request.query_params["cursor"] = cursor       
            request.query_params._mutable = _mutable

        # Paginate the response
        instances = instances.order_by("id")
        paginator = CursorPagination()
        paginator.ordering = "created"
        paginator.page_size = settings.CURSOR_PAGINATION_PAGE_SIZE        
        result_page = paginator.paginate_queryset(instances, request)

        # if not instances:
        #     result_page = [{f : None for f in model_fields}]

        # Serialize the filtered data and then return it
        print(stats)
        if stats and stats.upper() == "TRUE":
            serializer = getattr(serializers, f"{pathogen_model.__name__}StatsSerializer")(result_page, many=True)
        else:
            serializer = getattr(serializers, f"{pathogen_model.__name__}Serializer")(result_page, many=True)

        return paginator.get_paginated_response(serializer.data)



class UpdateSuppressPathogenView(APIView):
    permission_classes = [IsAuthenticated, IsApproved]

    def patch(self, request, pathogen_code, cid):
        '''
        Uses the provided `pathogen_code` and `cid` to update a record with `request.data`.
        '''
        pathogen_model = get_pathogen_model_or_404(pathogen_code)
        
        # Get the instance to be updated
        instance = get_object_or_404(pathogen_model.objects.filter(suppressed=False), cid=cid)
        
        # Check user is the correct institute
        if request.user.institute.code != instance.institute.code:
            return Responses._403_incorrect_institute_for_user

        # Custom processing and validation of data
        invalid_fields = process_data(
            data=request.data,
            model=pathogen_model,
            forbidden_fields=pathogen_model.readonly_fields(), 
        )

        for field, value in request.data.items():
            if value == settings.FIELD_NULL_TOKEN:
                request.data[field] = None

        # Serializer also carries out validation of input data
        serializer = getattr(serializers, f"{pathogen_model.__name__}Serializer")(instance=instance, data=request.data, partial=True)

        # If data is valid, update existing record in the database. If invalid, return errors
        if serializer.is_valid() and (not invalid_fields):
            if len(serializer.validated_data) == 0:
                return Responses._400_no_updates_provided
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            # Combine serializer and custom errors
            errors = dict(serializer.errors)
            for field, value in invalid_fields.items():
                errors[field] = value
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)


    def delete(self, request, pathogen_code, cid):
        '''
        Uses the provided `pathogen_code` and `cid` to suppress a record.
        '''
        pathogen_model = get_pathogen_model_or_404(pathogen_code)

        # Get the instance to be suppressed
        instance = get_object_or_404(pathogen_model, cid=cid)

        # Check user is the correct institute
        if request.user.institute.code != instance.institute.code:
            return Responses._403_incorrect_institute_for_user

        # Suppress and save
        instance.suppressed = True
        instance.save(update_fields=["suppressed"])
        
        # Just to double check
        instance = get_object_or_404(pathogen_model, cid=cid)
        
        # Return the details
        return Response(
            {
                "detail" : {
                    "cid" : cid,
                    "suppressed" : instance.suppressed
                }
            },
            status=status.HTTP_200_OK
        )



class DeletePathogenView(APIView):
    permission_classes = [IsAdminUser]

    def delete(self, request, pathogen_code, cid):
        '''
        Uses the provided `pathogen_code` and `cid` to permanently delete a record.
        '''
        pathogen_model = get_pathogen_model_or_404(pathogen_code)
        
        # Attempt to delete object with the provided cid, and return response
        response = get_object_or_404(pathogen_model, cid=cid).delete()
        
        return Response({"detail" : response}, status=status.HTTP_200_OK)
