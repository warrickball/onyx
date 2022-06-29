from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view
import api.serializers
import data.models


@api_view(["POST"])
def post(request, model_name):
    serializer = getattr(api.serializers, f"{model_name.upper()}Serializer")(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
def get(request, model_name):
    model = getattr(data.models, model_name.upper())
    instances = model.objects.all()
    for field, value in request.query_params.items():
        if hasattr(model, field):
            instances = instances.filter(**{field : value})
        else:
            return Response({"detail" : f"attribute '{field}' does not exist for {model.__name__}."}, status=status.HTTP_400_BAD_REQUEST)
    serializer = getattr(api.serializers, f"{model_name.upper()}Serializer")(instances, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["PUT", "PATCH"])
def update(request, model_name, cid):
    model = getattr(data.models, model_name.upper())
    instance = model.objects.filter(cid=cid).first()
    if not instance:
        return Response(
            {"detail" : f"{model.__name__} record with cid '{cid}' does not exist"}, 
            status=status.HTTP_404_NOT_FOUND
        )
    if request.method == "PUT":
        serializer = getattr(api.serializers, f"{model_name.upper()}Serializer")(instance=instance, data=request.data)
    else:
        serializer = getattr(api.serializers, f"{model_name.upper()}Serializer")(instance=instance, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["DELETE"])
def delete(request, model_name, cid):
    model = getattr(data.models, model_name.upper())
    response = model.objects.filter(cid=cid).delete()
    return Response(
        {"detail" : response},
        status=status.HTTP_200_OK
    )
