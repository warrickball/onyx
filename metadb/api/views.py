from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.core.exceptions import FieldError
from django.shortcuts import get_object_or_404
from django.http import Http404
import api.serializers
import data.models
import inspect


def get_pathogen_model_or_404(pathogen_code):
    '''
    Returns the model for the given `pathogen_code`, raising a `Http404` if it doesn't exist.
    '''
    members = inspect.getmembers(data.models, inspect.isclass)
    for name, model in members:
        if pathogen_code.upper() == name.upper():
            return model
    raise Http404


@api_view(["POST"])
def create(request):
    # Check for provided pathogen_code
    pathogen_code = request.data.get("pathogen_code")
    if not pathogen_code:
        return Response({"detail" : "no pathogen was provided"}, status=status.HTTP_400_BAD_REQUEST)

    # Get the model
    pathogen_model = get_pathogen_model_or_404(pathogen_code)

    # Serializer validates input data
    serializer = getattr(api.serializers, f"{pathogen_model.__name__}Serializer")(data=request.data)

    # If data is valid, save to the database. If invalid, return errors
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
def get(request, pathogen_code):
    # Get the model
    pathogen_model = get_pathogen_model_or_404(pathogen_code)
    
    # Create queryset of all objects by default
    instances = pathogen_model.objects.all()

    # For each query param, filter the data
    for field, value in request.query_params.items():
        try:
            instances = instances.filter(**{field : value})
        except FieldError as e:
            return Response({"detail" : str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    # Serialize the filtered data and then return it
    serializer = getattr(api.serializers, f"{pathogen_model.__name__}Serializer")(instances, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["PUT", "PATCH"])
def update(request, pathogen_code, cid):
    # Get the model
    pathogen_model = get_pathogen_model_or_404(pathogen_code)
    
    # Get the instance to be updated
    instance = get_object_or_404(pathogen_model, cid=cid)
    
    # If a PUT request was sent, check for every field of the model in the request data, and validate each
    # If a PATCH request was sent, only validate the fields that were provided
    if request.method == "PUT":
        serializer = getattr(api.serializers, f"{pathogen_model.__name__}Serializer")(instance=instance, data=request.data)
    else:
        serializer = getattr(api.serializers, f"{pathogen_model.__name__}Serializer")(instance=instance, data=request.data, partial=True)

    # If data is valid, update existing record in the database. If invalid, return errors
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["DELETE"])
def delete(request, pathogen_code, cid):
    pathogen_model = get_pathogen_model_or_404(pathogen_code)
    
    # Attempt to delete object with the provided cid, and return response
    response = get_object_or_404(pathogen_model, cid=cid).delete()
    return Response({"detail" : response}, status=status.HTTP_200_OK)


@api_view(["GET"])
def get_cid(request, cid):
    # Get superclass instance of the object with the given cid
    super_instance = get_object_or_404(data.models.Pathogen, cid=cid)

    # Get the model for the given cid
    pathogen_model = get_pathogen_model_or_404(super_instance.pathogen_code)

    # Find subclass instance for the given cid
    instance = pathogen_model.objects.get(cid=cid)

    # Serialize the instance and return it
    serializer = getattr(api.serializers, f"{pathogen_model.__name__}Serializer")(instance)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["PUT", "PATCH"])
def update_cid(request, cid):
    # Get superclass instance of the object with the given cid
    super_instance = get_object_or_404(data.models.Pathogen, cid=cid)

    # Get the model for the given cid
    pathogen_model = get_pathogen_model_or_404(super_instance.pathogen_code)

    # Find subclass instance for the given cid
    instance = get_object_or_404(pathogen_model, cid=cid)

    # If a PUT request was sent, check for every field of the model in the request data, and validate each
    # If a PATCH request was sent, only validate the fields that were provided
    if request.method == "PUT":
        serializer = getattr(api.serializers, f"{pathogen_model.__name__}Serializer")(instance=instance, data=request.data)
    else:
        serializer = getattr(api.serializers, f"{pathogen_model.__name__}Serializer")(instance=instance, data=request.data, partial=True)

    # If data is valid, update existing record in the database. If invalid, return errors
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["DELETE"])
def delete_cid(request, cid):
    # Get superclass instance of the object with the given cid
    super_instance = get_object_or_404(data.models.Pathogen, cid=cid)

    # Get the model for the given cid
    pathogen_model = get_pathogen_model_or_404(super_instance.pathogen_code)

    # Attempt to delete object with the provided cid, and return response
    response = get_object_or_404(pathogen_model, cid=cid).delete()
    return Response({"detail" : response}, status=status.HTTP_200_OK)
