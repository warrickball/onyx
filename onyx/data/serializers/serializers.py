from data.models import Record
from django.db import transaction, IntegrityError, DatabaseError
from rest_framework import serializers
from utils.validation import (
    enforce_optional_value_groups,
    enforce_orderings,
    enforce_non_futures,
    enforce_identifiers,
)


# TODO: Need to handle all manner of malformed `data`
# TODO: Also need to handle required FKs, not just optional many-to-one
class SerializerNode:
    def __init__(self, serializer_class, data=None):
        self.serializer_class = serializer_class
        self.model = serializer_class.Meta.model
        self.identifiers = serializer_class.ExtraMeta.identifiers
        self.relations = serializer_class.ExtraMeta.relations
        self.nodes = {}
        self.data = {}

        if isinstance(data, dict):
            related_data = {}

            for field, field_data in data.items():
                if field in self.relations:
                    related_data[field] = field_data
                else:
                    self.data[field] = field_data

            for field, field_data in related_data.items():
                relation = self.relations[field]

                if relation["kwargs"].get("many"):
                    self.nodes[field] = []

                    for f_d in field_data:
                        self.nodes[field].append(
                            SerializerNode(
                                serializer_class=relation["serializer"],
                                data=f_d,
                            )
                        )
                else:
                    self.nodes[field] = SerializerNode(
                        serializer_class=relation["serializer"],
                        data=field_data,
                    )

    def _validate_subnode_create(self, subnode):
        if not subnode.is_valid():
            return False, subnode.errors

        return True, {}

    def _validate_subnode_update(self, subnode, link=None):
        identifiers = {
            key: value
            for key, value in subnode.data.items()
            if key in subnode.identifiers
        }
        identifier_serializer = subnode.serializer_class(
            data=identifiers,
            partial=True,
        )

        if not identifier_serializer.is_valid():
            return False, identifier_serializer.errors
        else:
            ins = None

            if link:
                try:
                    ins = subnode.model.objects.get(
                        link=link,
                        **identifier_serializer.validated_data,
                    )
                except subnode.model.DoesNotExist:
                    pass

            if not subnode.is_valid(instance=ins):
                return False, subnode.errors

        return True, {}

    def is_valid(self, instance=None):
        valid = []

        self.serializer = self.serializer_class(
            instance=instance,
            data=self.data,
            partial=bool(instance),
        )
        valid.append(self.serializer.is_valid())
        self.errors = dict(self.serializer.errors)

        for field, node in self.nodes.items():
            if isinstance(node, list):
                subnode_errors = {}

                for i, n in enumerate(node):
                    if not instance:
                        val, errors = self._validate_subnode_create(n)
                    else:
                        val, errors = self._validate_subnode_update(n, link=instance)

                    valid.append(val)
                    if errors:
                        subnode_errors[i] = errors

                if subnode_errors:
                    self.errors[field] = subnode_errors

            else:
                if not instance:
                    val, errors = self._validate_subnode_create(node)
                else:
                    val, errors = self._validate_subnode_update(node, link=instance)

                valid.append(val)
                if errors:
                    self.errors[field] = errors

        return all(valid)

    def _save(self, link=None):
        if link:
            # If the instance is expecting a link, pass it through to the serializer
            instance = self.serializer.save(link=link)
        else:
            instance = self.serializer.save()

        for node in self.nodes.values():
            if isinstance(node, list):
                for n in node:
                    n._save(link=instance)
            else:
                node._save(link=instance)

        return instance

    def save(self):
        try:
            # Any exceptions thrown during the creation process will be re-raised as
            # DatabaseErrors, causing the entire database transaction to be rolled back
            with transaction.atomic():
                try:
                    instance = self._save()
                except Exception as e:
                    raise DatabaseError from e
        except DatabaseError as e:
            # Inform the user of any details regarding an IntegrityError
            # Otherwise, they will just see the generic 'Internal Server Error' message
            if isinstance(e.__cause__, IntegrityError):
                raise serializers.ValidationError(
                    {"detail": f"IntegrityError: {e.__cause__}"}
                )
            else:
                raise e.__cause__  #  type: ignore

        return instance


# https://www.django-rest-framework.org/api-guide/serializers/#dynamically-modifying-fields
class AbstractRecordSerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        # Don't pass the 'fields' arg up to the superclass
        fields = kwargs.pop("fields", None)

        # Instantiate the superclass normally
        super().__init__(*args, **kwargs)

        # The fields argument should be used ONLY for viewing data
        if fields is not None:
            allowed = []
            relations = {}

            # Add each provided field to the 'allowed' list
            # If a field is nested, also add it to the 'relations' dict
            for field_name, nested in fields.items():
                allowed.append(field_name)

                if nested:
                    relations[field_name] = nested

            # Initialise serializers for relations
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

    def validate(self, data):
        """
        Additional validation carried out on either object creation or update
        """
        errors = {}

        enforce_identifiers(
            errors=errors,
            data=data,
            identifiers=self.ExtraMeta.identifiers,
        )

        if (not self.instance) and self.partial:
            pass
        else:
            enforce_optional_value_groups(
                errors=errors,
                data=data,
                groups=self.ExtraMeta.optional_value_groups,
                instance=self.instance,
            )

            enforce_orderings(
                errors=errors,
                data=data,
                orderings=self.ExtraMeta.orderings,
                instance=self.instance,
            )

            enforce_non_futures(
                errors=errors,
                data=data,
                non_futures=self.ExtraMeta.non_futures,
            )

        if errors:
            raise serializers.ValidationError(errors)

        return data

    # def create(self, validated_data):
    #     try:
    #         # Any exceptions thrown during the creation process will be re-raised as
    #         # IntegrityErrors, causing the entire database transaction to be rolled back
    #         with transaction.atomic():
    #             try:
    #                 record = self._create(validated_data)
    #             except Exception as e:
    #                 raise IntegrityError from e
    #     except IntegrityError as e:
    #         # Any keys that are meant to be unique within validated_data
    #         # are known to be unique from when compared to the database during validation.
    #         # But this still leaves some possible causes for an integrity error:
    #         # > another process tries to create the same validated_data while this one is (race condition)
    #         # > the validated_data contains duplicate keys within itself, that do not exist in the database
    #         raise serializers.ValidationError({"detail": f"Error: {e.__cause__}"})
    #     return record

    # def update(self, instance, validated_data):
    #     try:
    #         with transaction.atomic():
    #             try:
    #                 record = self._update(validated_data, instance=instance)
    #             except Exception as e:
    #                 raise IntegrityError from e
    #     except IntegrityError as e:
    #         raise serializers.ValidationError({"detail": f"Error: {e.__cause__}"})

    #     return record

    # @classmethod
    # def _create(cls, validated_data, link=None):
    #     # Get the serializer's model
    #     model = getattr(cls, "Meta").model

    #     # Move any nested data from validated_data into related_data
    #     related_data = {}
    #     for name in cls.ExtraMeta.relations:
    #         r_d = validated_data.pop(name, None)
    #         if r_d:
    #             related_data[name] = r_d

    #     # Create the record with validated_data, with a FK if provided
    #     if link:
    #         record = model.objects.create(link=link, **validated_data)
    #     else:
    #         record = model.objects.create(**validated_data)

    #     # Recursively handle creation of related_data
    #     for name, data in related_data.items():
    #         serializer = cls.ExtraMeta.relations[name]["serializer"]
    #         many = cls.ExtraMeta.relations[name]["kwargs"].get("many")

    #         if many:
    #             for x in data:
    #                 serializer._create(x, link=record)
    #         else:
    #             serializer._create(data, link=record)

    #     return record

    # @classmethod
    # def _update(cls, validated_data, instance=None, link=None):
    #     # Get the serializer's model
    #     model = getattr(cls, "Meta").model

    #     # Move any nested data from validated_data into related_data
    #     related_data = {}
    #     for name in cls.ExtraMeta.relations:
    #         r_d = validated_data.pop(name, None)
    #         if r_d:
    #             related_data[name] = r_d

    #     if instance:
    #         for field, value in validated_data.items():
    #             setattr(instance, field, value)
    #         instance.save(update_fields=validated_data)
    #     else:
    #         identifiers = {
    #             identifier: validated_data.pop(identifier)
    #             for identifier in cls.ExtraMeta.identifiers
    #         }

    #         instance, _ = model.objects.update_or_create(
    #             defaults=validated_data, link=link, **identifiers
    #         )

    #     # Recursively handle update of related_data
    #     for name, data in related_data.items():
    #         serializer = cls.ExtraMeta.relations[name]["serializer"]
    #         many = cls.ExtraMeta.relations[name]["kwargs"].get("many")

    #         if many:
    #             for x in data:
    #                 serializer._update(x, link=instance)
    #         else:
    #             serializer._update(data, link=instance)

    #     return instance

    class ExtraMeta:
        relations = {}
        identifiers = []
        optional_value_groups = []
        orderings = []
        non_futures = []


class RecordSerializer(AbstractRecordSerializer):
    class Meta:
        model = Record
        fields = [
            "created",
            "last_modified",
            "suppressed",
            "user",
            "site",
            "cid",
            "published_date",
        ]
