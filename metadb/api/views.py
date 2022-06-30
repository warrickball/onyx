from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import FieldError
import api.serializers
import data.models


def model_exists(func):
    '''
    Decorator that converts `model_name` to uppercase and determines whether a model with the name exists.
    '''
    def wrapped_func(request, model_name, *args, **kwargs):
        # Use upper-cased version of model name throughout
        model_name = model_name.upper()

        # If the model does not exist, return 404
        if not hasattr(data.models, model_name):
            return Response(
                {"detail" : f"model '{model_name}' does not exist"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        return func(request, model_name, *args, **kwargs)
    
    return wrapped_func


@api_view(["POST"])
def create(request):
    model_name = request.data.get("organism")

    if not model_name:
        return Response(
            {"detail" : "an organism must be provided"}, 
            status=status.HTTP_400_BAD_REQUEST
        )

    model_name = model_name.upper()

    if not hasattr(data.models, model_name):
        return Response(
            {"detail" : f"model '{model_name}' does not exist"}, 
            status=status.HTTP_404_NOT_FOUND
        )

    # Serializer validates input data
    serializer = getattr(api.serializers, f"{model_name}Serializer")(data=request.data)
    
    if serializer.is_valid():
        # Save data to the database as a new record for the given model
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# @api_view(["POST"])
# @model_exists
# def create(request, model_name):
#     # Serializer validates input data
#     serializer = getattr(api.serializers, f"{model_name}Serializer")(data=request.data)
    
#     if serializer.is_valid():
#         # Save data to the database as a new record for the given model
#         serializer.save()
#         return Response(serializer.data, status=status.HTTP_200_OK)
#     else:
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
@model_exists
def get(request, model_name):
    model = getattr(data.models, model_name)
    
    # Create queryset of all objects by default
    instances = model.objects.all()

    # For each query param, filter the data
    for field, value in request.query_params.items():
        try:
            instances = instances.filter(**{field : value})
        except FieldError as e:
            return Response({"detail" : str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    # Serialize the filtered data and then return it
    serializer = getattr(api.serializers, f"{model_name}Serializer")(instances, many=True)

    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["PUT", "PATCH"])
@model_exists
def update(request, model_name, cid):
    model = getattr(data.models, model_name)
    
    # The model instance to be updated
    instance = model.objects.filter(cid=cid).first()
    
    # If an incorrect cid has been provided, return an error message
    if not instance:
        return Response(
            {"detail" : f"{model.__name__} record with cid '{cid}' does not exist"}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    # If a PUT request was sent, check for every field of the model in the request data, and validate each
    # If a POST request was sent, only validate the fields that were provided
    if request.method == "PUT":
        serializer = getattr(api.serializers, f"{model_name}Serializer")(instance=instance, data=request.data)
    else:
        serializer = getattr(api.serializers, f"{model_name}Serializer")(instance=instance, data=request.data, partial=True)

    if serializer.is_valid():
        # Update data of the given record in the database
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["DELETE"])
@model_exists
def delete(request, model_name, cid):
    model = getattr(data.models, model_name)
    response = model.objects.filter(cid=cid).delete()
    return Response(
        {"detail" : response},
        status=status.HTTP_200_OK
    )


@api_view(["GET"])
def get_cid(request, cid):
    super_instance = data.models.Organism.objects.filter(cid=cid).first()
    if not super_instance:
        return Response(
            {"detail" : f"record with cid '{cid}' does not exist"}, 
            status=status.HTTP_404_NOT_FOUND
        )

    model = getattr(data.models, super_instance.organism)
    instance = model.objects.filter(cid=cid).first()
    serializer = getattr(api.serializers, f"{super_instance.organism}Serializer")(instance)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["PUT", "PATCH"])
def update_cid(request, cid):
    super_instance = data.models.Organism.objects.filter(cid=cid).first()
    if not super_instance:
        return Response(
            {"detail" : f"record with cid '{cid}' does not exist"}, 
            status=status.HTTP_404_NOT_FOUND
        )

    model = getattr(data.models, super_instance.organism)
    instance = model.objects.filter(cid=cid).first()

    if request.method == "PUT":
        serializer = getattr(api.serializers, f"{model.__name__}Serializer")(instance=instance, data=request.data)
    else:
        serializer = getattr(api.serializers, f"{model.__name__}Serializer")(instance=instance, data=request.data, partial=True)

    if serializer.is_valid():
        # Update data of the given record in the database
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["DELETE"])
def delete_cid(request, cid):
    super_instance = data.models.Organism.objects.filter(cid=cid).first()
    if not super_instance:
        return Response(
            {"detail" : f"record with cid '{cid}' does not exist"}, 
            status=status.HTTP_404_NOT_FOUND
        )

    model = getattr(data.models, super_instance.organism)
    response = model.objects.filter(cid=cid).delete()
    return Response(
        {"detail" : response},
        status=status.HTTP_200_OK
    )
