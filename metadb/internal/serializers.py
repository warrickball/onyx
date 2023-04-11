from rest_framework import serializers


# https://www.django-rest-framework.org/api-guide/serializers/#dynamically-modifying-fields
class DynamicFieldsModelSerializer(serializers.ModelSerializer):
    """
    A ModelSerializer that takes an additional `fields` argument that
    controls which fields should be displayed.
    """

    def __init__(self, *args, **kwargs):
        # Don't pass the 'fields' arg up to the superclass
        fields = kwargs.pop("fields", None)

        # Instantiate the superclass normally
        super().__init__(*args, **kwargs)

        if fields is not None:
            # Drop any fields that are not specified in the `fields` argument.
            allowed = set(fields)
            existing = set(self.fields)
            for field_name in existing - allowed:
                self.fields.pop(field_name)


class NestedDynamicFieldsModelSerializer(serializers.ModelSerializer):
    """
    A ModelSerializer that takes an additional `fields` argument that
    controls which fields should be displayed.
    """

    def __init__(self, *args, **kwargs):
        # Don't pass the 'fields' arg up to the superclass
        fields = kwargs.pop("fields", None)

        # Instantiate the superclass normally
        super().__init__(*args, **kwargs)

        if fields is not None:
            allowed = []
            relations = {}

            for field_name, nested in fields.items():
                allowed.append(field_name)

                if nested:
                    relations[field_name] = nested

            # Handle relations
            for field_name, nested in relations.items():
                relation = self.CustomMeta.relations[field_name]
                self.fields[field_name] = relation["serializer"](
                    fields=nested,
                    **relation["kwargs"],
                )

            # Drop any fields that are not specified in the `fields` argument.
            allowed = set(allowed)
            existing = set(self.fields)
            for field_name in existing - allowed:
                self.fields.pop(field_name)

    class CustomMeta:
        relations = {}
