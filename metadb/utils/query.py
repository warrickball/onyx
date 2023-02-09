from django.db.models import Q
from rest_framework import status
from rest_framework.response import Response
import operator
import functools
from utils.response import METADBAPIResponse


class KeyValue:
    """
    Class for representing a single key-value pair.
    """

    def __init__(self, key, value):
        self.key = key
        self.value = value



def make_keyvalues(data):
    """
    Traverses the provided `data` and replaces request values with `KeyValue` objects.
    Returns a list of these `KeyValue` objects.
    """
    if len(data.items()) != 1:
        raise Exception

    key, value = next(iter(data.items()))

    if key in {"&", "|", "^"}:
        keyvalues = [make_keyvalues(k_v) for k_v in value]
        return functools.reduce(operator.add, keyvalues)

    elif key == "~":
        if len(value) != 1:
            raise Exception
        return make_keyvalues(value[0])

    else:
        # Initialise KeyValue object
        keyvalue = KeyValue(key, value)

        # Replace the request.data value with the KeyValue object
        data[key] = keyvalue

        # Now return the Keyvalue object
        # All this is being done so that its easy to modify the key/value in the request.data structure
        # To modify the key/values, we will be able to change them in the returned list
        # And because they are the same objects as in request.data, that will be altered as well
        return [keyvalue]


def get_query(data):
    """
    Traverses the provided `data` and forms the corresponding Q object.
    """
    if len(data.items()) != 1:
        raise Exception

    key, value = next(iter(data.items()))

    # AND of multiple keyvalues
    if key == "&":
        q_objects = [get_query(k_v) for k_v in value]
        return functools.reduce(operator.and_, q_objects)

    # OR of multiple keyvalues
    elif key == "|":
        q_objects = [get_query(k_v) for k_v in value]
        return functools.reduce(operator.or_, q_objects)

    # XOR of multiple keyvalues
    elif key == "^":
        q_objects = [get_query(k_v) for k_v in value]
        return functools.reduce(operator.xor, q_objects)

    # NOT of a single keyvalue
    elif key == "~":
        if len(value) != 1:
            raise Exception
        return ~get_query(value[0])

    # Base case: a keyvalue to filter on
    else:
        # 'value' here is a KeyValue object
        # That by this point, should have been cleaned and corrected to work in a query
        q = Q(**{value.key: value.value})
        return q


def get_filterset_datas_from_query_params(query_params):
    filterset_datas = []

    for field in query_params:
        values = list(set(query_params.getlist(field)))

        for i, value in enumerate(values):
            if len(filterset_datas) == i:
                filterset_datas.append({})

            filterset_datas[i][field] = value

    return filterset_datas


def get_filterset_datas_from_keyvalues(keyvalues):
    filterset_datas = [{}]

    for keyvalue in keyvalues:
        # Place the keyvalue in the first dictionary where the key is not present
        # If we reach the end with no placement, create a new dictionary and add it in there
        for filterset_data in filterset_datas:
            if keyvalue.key not in filterset_data:
                filterset_data[keyvalue.key] = keyvalue
                break
        else:
            filterset_datas.append({keyvalue.key: keyvalue})

    return filterset_datas


def apply_get_filterset(fs, model, view_fields, filterset_datas, qs):
    # A filterset can only take a a query with one of each field at a time
    # So given that the get view only AND's fields together, we can represent this
    # as a series of filtersets ANDed together
    for i, filterset_data in enumerate(filterset_datas):
        # Generate filterset of current queryset
        filterset = fs(
            model,
            view_fields,
            data=filterset_data,
            queryset=qs,
        )

        # If unknown field lookups were provided, return 400
        if i == 0:
            unknown = {}

            for field in filterset_data:
                if field not in filterset.filters:
                    unknown[field] = [METADBAPIResponse.UNKNOWN_FIELD]

            if unknown:
                return Response(
                    unknown,
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # Retrieve the resulting filtered queryset
        qs = filterset.qs

        # If not valid, return errors
        if not filterset.is_valid():
            return Response(filterset.errors, status=status.HTTP_400_BAD_REQUEST)

    return qs


def apply_query_filterset(fs, model, view_fields, filterset_datas):
    # Use a filterset, applied to each dict in filterset_datas, to validate the data
    for i, filterset_data in enumerate(filterset_datas):
        # Slightly cursed, but it works
        filterset = fs(
            model,
            view_fields,
            data={k: v.value for k, v in filterset_data.items()},
            queryset=model.objects.none(),
        )

        # If unknown field lookups were provided, return 400
        if i == 0:
            unknown = {}

            for field in filterset_data:
                if field not in filterset.filters:
                    unknown[field] = [METADBAPIResponse.UNKNOWN_FIELD]

            if unknown:
                return Response(
                    unknown,
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # If not valid, return errors
        if not filterset.is_valid():
            return Response(filterset.errors, status=status.HTTP_400_BAD_REQUEST)

        # Add the cleaned values to the KeyValue objects
        for k, keyvalue in filterset_data.items():
            keyvalue.value = filterset.form.cleaned_data[k]
    