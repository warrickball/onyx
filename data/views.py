from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.pagination import CursorPagination
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.http import Http404
from . import serializers, models
from .models import Pathogen
from accounts.views import IsApproved
from utils.responses import Responses
import inspect



# TODO: Could do with a consistent model for response, no matter errors or not
# Could have status code, errors and results for every response



def get_pathogen_model_or_404(pathogen_code):
    '''
    Returns the model for the given `pathogen_code`, raising a `Http404` if it doesn't exist.
    '''
    members = inspect.getmembers(models, inspect.isclass)
    for name, model in members:
        if pathogen_code.upper() == name.upper() and (model == Pathogen or Pathogen in model.__bases__):
            return model
    raise Http404



def convert_choice_fields(choice_fields, data):
    for field in data:
        if field in choice_fields:
            # TODO: find way to get choice values out of model, and use instead of capitalising
            # Want to check if the input shares characters with a choice, then convert it to that choice if so
            data[field] = data[field].upper()



def check_unknown_forbidden_fields(all_fields, forbidden_fields, data):
    # Not a fan of this but can't find a consistent solution that avoids stuff like the following issue
    # https://github.com/encode/django-rest-framework/issues/1655
    invalid_fields = {
        "unknown" : [],
        "forbidden" : []
    }
    valid = True
    for field in data:
        if field not in all_fields:
            invalid_fields["unknown"].append(field)
            valid = False
        elif field in forbidden_fields:
            invalid_fields["forbidden"].append(field)
            valid = False

    if valid:
        return None
    else:
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

        # Get the model
        pathogen_model = get_pathogen_model_or_404(pathogen_code)

        # If a pathogen_code was provided in the body, and it doesn't match the url, tell them to stop it
        request_pathogen_code = request.data.get("pathogen_code")
        if request_pathogen_code and request_pathogen_code.upper() != pathogen_code.upper():
            return Responses._400_mismatch_pathogen_code
        
        # If an institute was provided, check it matches the user's institute
        request_institute_code = request.data.get("institute")
        if request_institute_code and request_institute_code.upper() != request.user.institute.code: 
            return Responses._403_incorrect_institute_for_user

        # Check for unknown fields, and internal fields
        invalid_fields = check_unknown_forbidden_fields(
            all_fields=pathogen_model.all_fields(), 
            forbidden_fields=pathogen_model.internal_fields(), 
            data=request.data
        )
        if invalid_fields:
            return Response(invalid_fields, status=status.HTTP_400_BAD_REQUEST)

        # Convert input choice values to correct case
        convert_choice_fields(pathogen_model.choice_fields(), request.data)

        # Serializer validates input data
        serializer = getattr(serializers, f"{pathogen_model.__name__}Serializer")(data=request.data)

        # If data is valid, save to the database. If invalid, return errors
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    def get(self, request, pathogen_code):
        '''
        Uses `request.query_params` to filter and return data for the given `pathogen_code`.
        '''

        # Get the model
        pathogen_model = get_pathogen_model_or_404(pathogen_code)
        
        # Check for unknown fields and 'forbidden' fields
        invalid_fields = check_unknown_forbidden_fields(
            all_fields=pathogen_model.all_fields(), 
            forbidden_fields={}, 
            data=[f.split("__")[0] for f in request.query_params if f != "cursor"]
        )
        # If an id was provided (or an id__ field) as a query parameter, reject
        # NOTE: there is probably numerous cheeky ways around this 
        # But its not the end of the world if someone can figure out the pk, doesn't even matter really
        model_fields = pathogen_model.all_fields()
        forbidden = []
        for field in request.query_params:
            dunder_split = field.split("__")
            for f in dunder_split:
                if f == "id" or (f.endswith("_id") and f[:-len("_id")] in model_fields):
                    forbidden.append(f)
        if forbidden:
            if not invalid_fields:
                invalid_fields = {
                    "unknown" : [],
                    "forbidden" : forbidden
                }
            else:
                invalid_fields["forbidden"].extend(forbidden)
                invalid_fields["forbidden"] = list(set(invalid_fields["forbidden"]))
                invalid_fields["unknown"] = list(set(invalid_fields["unknown"]).difference(set(forbidden)))
        if invalid_fields:
            return Response(invalid_fields, status=status.HTTP_400_BAD_REQUEST)

        # Convert input choice values to correct case
        _mutable = request.query_params._mutable
        request.query_params._mutable = True
        convert_choice_fields(pathogen_model.choice_fields(), request.query_params)
        request.query_params._mutable = _mutable

        # Create queryset of all objects by default
        instances = pathogen_model.objects.all()

        # For each query param, filter the data
        for field in request.query_params:
            values = request.query_params.getlist(field)
            if field == "cursor":
                continue
            
            if field == "institute":
                # A regrettably hardcoded default that makes queries much more user friendly
                # TODO: find a better way to do this
                field = "institute__code"
            
            try:
                for value in values:
                    instances = instances.filter(**{field : value})
            except Exception as e:
                return Response({"detail" : repr(e)}, status=status.HTTP_400_BAD_REQUEST)

        # Paginate the response 
        # TODO: Read up exactly how cursor pagination works and how it should be done
        instances = instances.order_by("id")
        paginator = CursorPagination()
        paginator.ordering = "created"
        paginator.page_size = 5000
        result_page = paginator.paginate_queryset(instances, request)

        # Serialize the filtered data and then return it
        serializer = getattr(serializers, f"{pathogen_model.__name__}Serializer")(result_page, many=True)
        
        return paginator.get_paginated_response(serializer.data)



class UpdateDeletePathogenView(APIView):
    def get_permissions(self):
        if self.request.method == "PATCH":
            permission_classes = [IsAuthenticated, IsApproved]
        else:
            permission_classes = [IsAdminUser]
        return [permission() for permission in permission_classes]


    def patch(self, request, pathogen_code, cid):
        '''
        Uses the provided `cid` and `pathogen_code` to update a record with `request.data`.
        '''

        # Get the model
        pathogen_model = get_pathogen_model_or_404(pathogen_code)
        
        # Get the instance to be updated
        instance = get_object_or_404(pathogen_model, cid=cid)
        
        # Check user is the correct institute
        if request.user.institute.code != instance.institute.code:
            return Responses._403_incorrect_institute_for_user

        # Check for unknown fields, and readonly fields
        invalid_fields = check_unknown_forbidden_fields(
            all_fields=pathogen_model.all_fields(), 
            forbidden_fields=pathogen_model.readonly_fields(), 
            data=request.data
        )
        if invalid_fields:
            return Response(invalid_fields, status=status.HTTP_400_BAD_REQUEST)

        # Convert input choice values to correct case
        convert_choice_fields(pathogen_model.choice_fields(), request.data)

        serializer = getattr(serializers, f"{pathogen_model.__name__}Serializer")(instance=instance, data=request.data, partial=True)

        # If data is valid, update existing record in the database. If invalid, return errors
        if serializer.is_valid():
            if len(serializer.validated_data) == 0:
                return Responses._400_no_updates_provided
            
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    def delete(self, request, pathogen_code, cid):
        '''
        Uses the provided `cid` and `pathogen_code` to delete a record.
        '''

        # Get the model
        pathogen_model = get_pathogen_model_or_404(pathogen_code)
        
        # Attempt to delete object with the provided cid, and return response
        response = get_object_or_404(pathogen_model, cid=cid).delete()
        return Response({"detail" : response}, status=status.HTTP_200_OK)
