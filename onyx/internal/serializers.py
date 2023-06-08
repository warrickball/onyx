from rest_framework import serializers
from django.db import IntegrityError, transaction


# https://www.django-rest-framework.org/api-guide/serializers/#dynamically-modifying-fields
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
                relation = self.ExtraMeta.relations[field_name]
                self.fields[field_name] = relation["serializer"](
                    fields=nested,
                    **relation["kwargs"],
                )

            # Drop any fields that are not specified in the `fields` argument.
            allowed = set(allowed)
            existing = set(self.fields)
            for field_name in existing - allowed:
                self.fields.pop(field_name)

    def create(self, validated_data):
        try:
            # Any exceptions thrown during the creation process will
            # cause the entire database transaction to be rolled back
            with transaction.atomic():
                record = self._create(validated_data)
        except IntegrityError:
            # Any keys that are meant to be unique within validated_data
            # are known to be unique from when compared to the database during validation.
            # But this still leaves some possible causes for an integrity error:
            # > another process tries to create the same validated_data while this one is (race condition)
            # > the validated_data contains duplicate keys within itself, that do not exist in the database
            raise serializers.ValidationError(
                {
                    "detail": "IntegrityError occured on create. Either a race condition, or the request input contains duplicate keys."
                }
            )
        return record

    @classmethod
    def _create(cls, validated_data, link=None):
        # Get the serializer's model
        model = getattr(cls, "Meta").model

        # Move any nested data from validated_data into related_data
        related_data = {}
        for name in cls.ExtraMeta.relations:
            related_data[name] = validated_data.pop(name, None)

        # Create the record with validated_data, with a FK if provided
        if link:
            record = model.objects.create(link=link, **validated_data)
        else:
            record = model.objects.create(**validated_data)

        # Recursively handle creation of related_data
        for name, data in related_data.items():
            serializer = cls.ExtraMeta.relations[name]["serializer"]
            many = cls.ExtraMeta.relations[name]["kwargs"].get("many")

            if many:
                for x in data:
                    serializer._create(x, link=record)
            else:
                serializer._create(data, link=record)

        return record

    class ExtraMeta:
        relations = {}
