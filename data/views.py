from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.pagination import CursorPagination
from django.core.exceptions import FieldError
from django.shortcuts import get_object_or_404
from django.http import Http404
from . import serializers, models
from .models import Pathogen
from accounts.views import IsApproved
from utils.responses import Responses
import inspect


def get_pathogen_model_or_404(pathogen_code):
    '''
    Returns the model for the given `pathogen_code`, raising a `Http404` if it doesn't exist.
    '''
    members = inspect.getmembers(models, inspect.isclass)
    for name, model in members:
        if pathogen_code.upper() == name.upper():
            return model
    raise Http404


@api_view(["POST"])
@permission_classes([IsAuthenticated, IsApproved])
def create(request):
    # If a cid was provided, tell them no
    if request.data.get("cid"):
        return Responses.cannot_provide_cid

    # Check if an institute was provided
    institute = request.data.get("institute")
    if not institute:
        return Responses.no_institute

    # Check user is the correct institute
    # TODO: Probably a better way to do this involving groups or user permissions
    if request.user.institute.code != institute:
        return Responses.cannot_be_institute

    # Check for provided pathogen_code
    pathogen_code = request.data.get("pathogen_code")
    if not pathogen_code:
        return Responses.no_pathogen_code

    # Get the model
    pathogen_model = get_pathogen_model_or_404(pathogen_code)

    # Serializer validates input data
    serializer = getattr(serializers, f"{pathogen_model.__name__}Serializer")(data=request.data)

    # If data is valid, save to the database. If invalid, return errors
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsApproved])
def get(request, pathogen_code):
    # Get the model
    pathogen_model = get_pathogen_model_or_404(pathogen_code)
    
    # Create queryset of all objects by default
    instances = pathogen_model.objects.all()

    # If an id was provided as a query parameter, tell them no
    if request.query_params.get("id"):
        return Responses.cannot_query_id

    # For each query param, filter the data
    for field, value in request.query_params.items():
        if field != "cursor": # TODO: it works but its a bit crude
            try:
                instances = instances.filter(**{field : value})
            except FieldError as e:
                return Response({"detail" : str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    # Paginate the response 
    # TODO: Read up exactly how cursor pagination works and how it should be done
    instances = instances.order_by("id")
    paginator = CursorPagination()
    paginator.ordering = "created"
    paginator.page_size = 10000
    result_page = paginator.paginate_queryset(instances, request)

    # Serialize the filtered data and then return it
    serializer = getattr(serializers, f"{pathogen_model.__name__}Serializer")(result_page, many=True)
    
    return paginator.get_paginated_response(serializer.data)


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsApproved])
def get_cid(request, cid):
    # Get superclass instance of the object with the given cid
    super_instance = get_object_or_404(Pathogen, cid=cid)

    # Get the model for the given cid
    pathogen_model = get_pathogen_model_or_404(super_instance.pathogen_code)

    # Find subclass instance for the given cid
    instance = pathogen_model.objects.get(cid=cid)

    # Serialize the instance and return it
    serializer = getattr(serializers, f"{pathogen_model.__name__}Serializer")(instance)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["PUT", "PATCH"])
@permission_classes([IsAuthenticated, IsApproved])
def update(request, pathogen_code, cid):
    # Get the model
    pathogen_model = get_pathogen_model_or_404(pathogen_code)
    
    # Get the instance to be updated
    instance = get_object_or_404(pathogen_model, cid=cid)
    
    # Check user is the correct institute
    if request.user.institute.code != instance.institute.code:
        return Responses.cannot_be_institute

    # If a PUT request was sent, check for every field of the model in the request data, and validate each
    # If a PATCH request was sent, only validate the fields that were provided
    if request.method == "PUT":
        serializer = getattr(serializers, f"{pathogen_model.__name__}Serializer")(instance=instance, data=request.data)
    else:
        serializer = getattr(serializers, f"{pathogen_model.__name__}Serializer")(instance=instance, data=request.data, partial=True)

    # If data is valid, update existing record in the database. If invalid, return errors
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["PUT", "PATCH"])
@permission_classes([IsAuthenticated, IsApproved])
def update_cid(request, cid):
    # Get superclass instance of the object with the given cid
    super_instance = get_object_or_404(Pathogen, cid=cid)

    # Get the model for the given cid
    pathogen_model = get_pathogen_model_or_404(super_instance.pathogen_code)

    # Find subclass instance for the given cid
    instance = get_object_or_404(pathogen_model, cid=cid)

    # Check user is the correct institute
    if request.user.institute.code != instance.institute.code:
        return Responses.cannot_be_institute

    # If a PUT request was sent, check for every field of the model in the request data, and validate each
    # If a PATCH request was sent, only validate the fields that were provided
    if request.method == "PUT":
        serializer = getattr(serializers, f"{pathogen_model.__name__}Serializer")(instance=instance, data=request.data)
    else:
        serializer = getattr(serializers, f"{pathogen_model.__name__}Serializer")(instance=instance, data=request.data, partial=True)

    # If data is valid, update existing record in the database. If invalid, return errors
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["DELETE"])
@permission_classes([IsAdminUser])
def delete(request, pathogen_code, cid):
    # Get the model for the given cid
    pathogen_model = get_pathogen_model_or_404(pathogen_code)
    
    # Attempt to delete object with the provided cid, and return response
    response = get_object_or_404(pathogen_model, cid=cid).delete()
    return Response({"detail" : response}, status=status.HTTP_200_OK)


@api_view(["DELETE"])
@permission_classes([IsAdminUser])
def delete_cid(request, cid):
    # Get superclass instance of the object with the given cid
    super_instance = get_object_or_404(Pathogen, cid=cid)

    # Get the model for the given cid
    pathogen_model = get_pathogen_model_or_404(super_instance.pathogen_code)

    # Attempt to delete object with the provided cid, and return response
    response = get_object_or_404(pathogen_model, cid=cid).delete()
    return Response({"detail" : response}, status=status.HTTP_200_OK)
