from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.pagination import CursorPagination
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.http import Http404
from django.conf import settings
from . import serializers, models
from .filters import METADBFilter
from .models import Pathogen
from accounts.views import IsApproved
from utils.responses import Responses
import inspect



def get_pathogen_model_or_404(pathogen_code, accept_base=True):
    '''
    Returns the model for the given `pathogen_code`, raising a `Http404` if it doesn't exist.
    '''
    members = inspect.getmembers(models, inspect.isclass)
    
    for name, model in members:
        if accept_base:
            if pathogen_code.upper() == name.upper() and (model == Pathogen or Pathogen in model.__bases__):
                return model
        else:
            if pathogen_code.upper() == name.upper() and Pathogen in model.__bases__:
                return model

    raise Http404



def enforce_optional_value_groups(data, groups):
    errors = {
        "required_fields" : []
    }
    for group in groups:
        for field in group:
            if field in data:
                break
        else:
            # If you're reading this I'm sorry
            # I couldn't help but try a for-else
            # I just found out it can be done, so I did it :)
            errors["required_fields"].append(
                {
                    "At least one of the following fields is required." : group
                }
            )
    
    if errors["required_fields"]:
        return errors
    else:
        return {}



def enforce_field_set(data, accepted_fields, rejected_fields):
    errors = {}

    for field in data:
        if field in rejected_fields:
            errors[field] = [
                "This field cannot be accepted."
            ]
        elif field not in accepted_fields:
            errors[field] = [
                "This field is unknown."
            ]
    
    return errors



class PathogenCodeView(APIView):
    permission_classes = [IsAuthenticated, IsApproved]

    def get(self, request):
        members = inspect.getmembers(models, inspect.isclass)
        pathogen_codes = []
        
        for name, model in members:
            if Pathogen in model.__bases__:
                pathogen_codes.append(name.upper())
        
        return Response(
            {
                "pathogen_codes" : pathogen_codes
            }, 
            status=status.HTTP_200_OK
        )



class CreateGetPathogenView(APIView):
    def get_permissions(self):
        if self.request.method == "POST":
            permission_classes = [IsAdminUser]
        else:
            permission_classes = [IsAuthenticated, IsApproved]
        return [permission() for permission in permission_classes]


    def post(self, request, pathogen_code):
        '''
        Use `request.data` to save a model instance for the model specified by `pathogen_code`.
        '''
        pathogen_model = get_pathogen_model_or_404(pathogen_code, accept_base=False)

        # If a pathogen_code was provided in the body, and it doesn't match the url, tell them to stop it
        request_pathogen_code = request.data.get("pathogen_code")
        if request_pathogen_code and request_pathogen_code.upper() != pathogen_code.upper():
            return Responses._400_mismatch_pathogen_code
        
        # If an institute was provided, check it matches the user's institute
        request_institute_code = request.data.get("institute")
        if request_institute_code and request_institute_code.upper() != request.user.institute.code: 
            return Responses._403_incorrect_institute_for_user
        
        errors = {}

        # Check the request data contains at least one field from each optional value group
        errors = errors | enforce_optional_value_groups(
            data=request.data, 
            groups=pathogen_model.optional_value_groups()
        )
        # Check the request data contains only model fields allowed for creation
        errors = errors | enforce_field_set(
            data=request.data, 
            accepted_fields=pathogen_model.create_fields(), 
            rejected_fields=pathogen_model.non_create_fields()
        )
        # Serializer also carries out validation of input data
        serializer = getattr(serializers, f"{pathogen_model.__name__}Serializer")(data=request.data)

        # If data is valid, save to the database. If not valid, return errors
        if serializer.is_valid() and (not errors):
            serializer.save()
            return Response(
                serializer.data, 
                status=status.HTTP_200_OK
            )
        else:
            errors = errors | dict(serializer.errors)
            return Response(
                errors, 
                status=status.HTTP_400_BAD_REQUEST
            )


    def get(self, request, pathogen_code):
        '''
        Use `request.query_params` to filter data for the model specified by `pathogen_code`.
        '''
        pathogen_model = get_pathogen_model_or_404(pathogen_code)

        # Prepare paginator
        paginator = CursorPagination()
        paginator.ordering = "created"
        paginator.page_size = settings.CURSOR_PAGINATION_PAGE_SIZE  

        # Take out the pagination cursor param from the request
        _mutable = request.query_params._mutable
        request.query_params._mutable = True
        cursor = request.query_params.get(paginator.cursor_query_param)
        if cursor:
            request.query_params.pop(paginator.cursor_query_param)
        request.query_params._mutable = _mutable

        errors = {}

        # Generate filterset
        filterset = METADBFilter(
            pathogen_model,
            pathogen_model.filter_fields(),
            request.query_params, 
            queryset=pathogen_model.objects.filter(suppressed=False),
        )

        # Append unknown fields to error dict
        for field in request.query_params:
            if field not in filterset.filters:
                errors[field] = ["This field is unknown."]

        if not filterset.is_valid():
            # Append invalid fields to error dict
            for field, msg in filterset.errors.items():
                errors[field] = msg
        
        if errors:
            return Response(
                errors, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Add the pagination cursor param back into the request
        if cursor is not None:
            _mutable = request.query_params._mutable
            request.query_params._mutable = True
            request.query_params[paginator.cursor_query_param] = cursor       
            request.query_params._mutable = _mutable

        # Paginate the response
        instances = filterset.qs.order_by("id")    
        result_page = paginator.paginate_queryset(instances, request)

        # Serialize the results
        serializer = getattr(serializers, f"{pathogen_model.__name__}Serializer")(
            result_page, 
            many=True
        )
        return paginator.get_paginated_response(serializer.data)


class UpdateSuppressPathogenView(APIView):
    permission_classes = [IsAdminUser]

    def patch(self, request, pathogen_code, cid):
        '''
        Use `request.data` and a `cid` to update an instance for the model specified by `pathogen_code`.
        '''
        pathogen_model = get_pathogen_model_or_404(pathogen_code)
        
        # Get the instance to be updated
        instance = get_object_or_404(pathogen_model.objects.filter(suppressed=False), cid=cid)
        
        # Check user is the correct institute
        if request.user.institute.code != instance.institute.code:
            return Responses._403_incorrect_institute_for_user

        errors = {}

        # Check the request data contains only model fields allowed for updating
        errors = errors | enforce_field_set(
            data=request.data, 
            accepted_fields=pathogen_model.update_fields(), 
            rejected_fields=pathogen_model.non_update_fields()
        )
        # Serializer also carries out validation of input data
        serializer = getattr(serializers, f"{pathogen_model.__name__}Serializer")(instance=instance, data=request.data, partial=True)

        # If data is valid, update existing record in the database. If not valid, return errors
        if serializer.is_valid() and (not errors):
            if not serializer.validated_data:
                return Responses._400_no_updates_provided

            serializer.save()
            return Response(
                serializer.data, 
                status=status.HTTP_200_OK
            )
        else:
            errors = errors | dict(serializer.errors)
            return Response(
                errors, 
                status=status.HTTP_400_BAD_REQUEST
            )


    def delete(self, request, pathogen_code, cid):
        '''
        Use the provided `pathogen_code` and `cid` to suppress a record.
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
        Use the provided `pathogen_code` and `cid` to permanently delete a record.
        '''
        pathogen_model = get_pathogen_model_or_404(pathogen_code)
        
        # Attempt to delete object with the provided cid, and return response
        response = get_object_or_404(pathogen_model, cid=cid).delete()
        
        return Response(
            {"detail" : response}, 
            status=status.HTTP_200_OK
        )
