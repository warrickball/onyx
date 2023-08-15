from django.db import transaction, IntegrityError, DatabaseError
from rest_framework import serializers, exceptions
from accounts.models import User, Site
from utils.defaults import CurrentUserSiteDefault
from ..validators import (
    validate_optional_value_groups,
    validate_orderings,
    validate_non_futures,
    validate_identifiers,
    validate_choice_constraints,
    validate_conditional_required,
)


# TODO: Need to try out some nested FK data
# TODO: Need to handle required FKs, not just optional many-to-one
# TODO: Catch parse-errors within the keys that they occured?
class SerializerNode:
    def __init__(self, serializer_class, data=None, context=None):
        self.serializer_class = serializer_class
        self.context = context
        self.model = serializer_class.Meta.model
        self.identifiers = serializer_class.OnyxMeta.identifiers
        self.relations = serializer_class.OnyxMeta.relations
        self.nodes = {}
        self.data = {}

        if not isinstance(data, dict):
            raise exceptions.ValidationError(
                {"detail": "Expected a dictionary when parsing the request data."}
            )

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

                if not isinstance(field_data, list):
                    raise exceptions.ValidationError(
                        {"detail": f"Expected a list when parsing the {field} data."}
                    )

                for f_d in field_data:
                    self.nodes[field].append(
                        SerializerNode(
                            serializer_class=relation["serializer"],
                            data=f_d,
                            context=context,
                        )
                    )
            else:
                if not isinstance(field_data, dict):
                    raise exceptions.ValidationError(
                        {
                            "detail": f"Expected a dictionary when parsing the {field} data."
                        }
                    )

                self.nodes[field] = SerializerNode(
                    serializer_class=relation["serializer"],
                    data=field_data,
                    context=context,
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

        # Initialise a serializer and validate self.data
        # If an instance was not provided, will validate self.data for creation of an instance
        # If an instance was provided, will validate self.data for partial update of the instance
        self.serializer = self.serializer_class(
            instance=instance,
            data=self.data,
            partial=bool(instance),
            context=self.context,
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
        # Save the serializer and retrieve an instance
        # If a link was provided, pass it through to the serializer
        if link:
            instance = self.serializer.save(link=link)
        else:
            instance = self.serializer.save()

        # Save any nested objects, providing a link to the current instance
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
                raise exceptions.ValidationError(
                    {"detail": f"IntegrityError: {e.__cause__}"}
                )
            else:
                raise e.__cause__  #  type: ignore

        return instance


# https://www.django-rest-framework.org/api-guide/serializers/#dynamically-modifying-fields
class BaseRecordSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), default=serializers.CurrentUserDefault()
    )
    # site = serializers.PrimaryKeyRelatedField(
    #     queryset=Site.objects.all(), default=CurrentUserSiteDefault()
    # )

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
                relation = self.OnyxMeta.relations[field_name]
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
        Additional object-level validation.
        """
        errors = {}

        validate_identifiers(
            errors=errors,
            data=data,
            identifiers=self.OnyxMeta.identifiers,
        )

        if (not self.instance) and self.partial:
            # We only get to here if a serializer was initialised with no instance and partial = True.
            # This only happens when we create the serializer for validating just the identifiers.
            # In this case, we don't want to apply the other object-level validation.
            pass
        else:
            validate_optional_value_groups(
                errors=errors,
                data=data,
                groups=self.OnyxMeta.optional_value_groups,
                instance=self.instance,
            )

            validate_orderings(
                errors=errors,
                data=data,
                orderings=self.OnyxMeta.orderings,
                instance=self.instance,
            )

            validate_choice_constraints(
                errors=errors,
                data=data,
                choice_constraints=self.OnyxMeta.choice_constraints,
                project=self.context["project"],
                instance=self.instance,
            )

            validate_non_futures(
                errors=errors,
                data=data,
                non_futures=self.OnyxMeta.non_futures,
            )

            validate_conditional_required(
                errors=errors,
                data=data,
                conditional_required=self.OnyxMeta.conditional_required,
                instance=self.instance,
            )

        if errors:
            raise exceptions.ValidationError(errors)

        return data

    class Meta:
        fields = [
            "created",
            "last_modified",
            "user",
            # "site",
        ]

    class OnyxMeta:
        relations = {}
        identifiers = []
        optional_value_groups = []
        orderings = []
        non_futures = []
        choice_constraints = []
        conditional_required = {}


class ProjectRecordSerializer(BaseRecordSerializer):
    cid = serializers.CharField(required=False)

    class Meta:
        fields = BaseRecordSerializer.Meta.fields + [
            "cid",
            "published_date",
            "suppressed",
        ]
