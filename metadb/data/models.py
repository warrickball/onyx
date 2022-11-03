from django.db import models
from django.core.validators import MinLengthValidator
from django.db.models import Field
from django.db.models.lookups import BuiltinLookup
from rest_framework import serializers
from secrets import token_hex

from accounts.models import Site
from utils.fields import YearMonthField, LowerCharField
from utils import fieldserializers


def generate_cid():
    cid = "C-" + "".join(token_hex(4).upper())
    if Pathogen.objects.filter(cid=cid).exists():
        cid = generate_cid()
    return cid


@Field.register_lookup
class NotEqual(models.Lookup):
    lookup_name = "ne"

    def as_sql(self, compiler, connection):
        lhs, lhs_params = self.process_lhs(compiler, connection)
        rhs, rhs_params = self.process_rhs(compiler, connection)
        params = lhs_params + rhs_params
        return "%s <> %s" % (lhs, rhs), params


@Field.register_lookup
class IsNull(BuiltinLookup):
    lookup_name = "isnull"
    prepare_rhs = False

    def as_sql(self, compiler, connection):
        if str(self.rhs) in ["0", "false", "False"]:
            self.rhs = False

        elif str(self.rhs) in ["1", "false", "False"]:
            self.rhs = True

        if not isinstance(self.rhs, bool):
            raise ValueError(
                "The QuerySet value for an isnull lookup must be True or False."
            )

        sql, params = compiler.compile(self.lhs)
        if self.rhs:
            return "%s IS NULL" % sql, params
        else:
            return "%s IS NOT NULL" % sql, params


class PathogenCode(models.Model):
    code = LowerCharField(max_length=8, unique=True)


class Pathogen(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)
    suppressed = models.BooleanField(default=False)
    published_date = models.DateField(auto_now_add=True)

    pathogen_code = models.ForeignKey("PathogenCode", on_delete=models.CASCADE)
    site = models.ForeignKey("accounts.Site", on_delete=models.CASCADE)

    cid = models.CharField(default=generate_cid, max_length=12, unique=True)
    sender_sample_id = models.CharField(
        max_length=24, validators=[MinLengthValidator(8)]
    )
    collection_month = YearMonthField(null=True)
    received_month = YearMonthField(null=True)

    run_name = models.CharField(max_length=96, validators=[MinLengthValidator(18)])
    fasta_path = models.TextField()
    bam_path = models.TextField()
    is_external = models.BooleanField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["sender_sample_id", "run_name", "pathogen_code"],
                name="sample_run_pathogen_unique_together",
            )
        ]
        indexes = [
            models.Index(fields=["cid"]),
            models.Index(fields=["sender_sample_id"]),
            models.Index(fields=["run_name"]),
            models.Index(fields=["sender_sample_id", "run_name"]),
            models.Index(fields=["collection_month"]),
            models.Index(fields=["received_month"]),
            models.Index(fields=["published_date"]),
        ]

    FIELD_PERMISSIONS = {
        "id": ["hidden"],
        "created": ["hidden"],
        "last_modified": ["hidden"],
        "suppressed": ["hidden"],
        "cid": ["no create", "no update"],
        "sender_sample_id": ["create", "no update"],
        "run_name": ["create", "no update"],
        "pathogen_code": ["create", "no update"],
        "site": ["create", "no update"],
        "published_date": ["no create", "no update"],
        "fasta_path": ["create", "update"],
        "bam_path": ["create", "update"],
        "is_external": ["create", "update"],
        "collection_month": ["create", "update"],
        "received_month": ["create", "update"],
    }

    FILTER_FIELDS = {
        "cid": {"type": models.CharField},
        "sender_sample_id": {"type": models.CharField},
        "run_name": {"type": models.CharField},
        "pathogen_code__code": {
            "type": models.CharField,
            "db_choices": True,
            "alias": "pathogen_code",
            "root_field": "pathogen_code",
        },
        "site__code": {
            "type": models.CharField,
            "db_choices": True,
            "alias": "site",
            "root_field": "site",
        },
        "published_date": {"type": models.DateField},
        "fasta_path": {"type": models.TextField},
        "bam_path": {"type": models.TextField},
        "is_external": {"type": models.BooleanField},
        "collection_month": {"type": YearMonthField},
        "received_month": {"type": YearMonthField},
    }

    OPTIONAL_VALUE_GROUPS = [["collection_month", "received_month"]]

    # loop through user groups
    # loop through site groups

    @classmethod
    def user_fields(cls, user):
        if user.is_staff:
            fields = "__all__"

        elif user.site.is_pha:
            fields = [
                field
                for field, perms in cls.FIELD_PERMISSIONS.items()
                if "hidden" not in perms
            ]

        else:
            fields = [
                field
                for field, perms in cls.FIELD_PERMISSIONS.items()
                if "hidden" not in perms and "pha_only" not in perms
            ]

        return fields

    @classmethod
    def create_fields(cls, user):
        if user.is_staff or user.site.is_pha:
            fields = [
                field
                for field, perms in cls.FIELD_PERMISSIONS.items()
                if "create" in perms
            ]
        else:
            fields = [
                field
                for field, perms in cls.FIELD_PERMISSIONS.items()
                if "create" in perms and "pha_only" not in perms
            ]
        return fields

    @classmethod
    def no_create_fields(cls, user):
        if user.is_staff or user.site.is_pha:
            fields = [
                field
                for field, perms in cls.FIELD_PERMISSIONS.items()
                if "no create" in perms
            ]
        else:
            fields = [
                field
                for field, perms in cls.FIELD_PERMISSIONS.items()
                if "no create" in perms and "pha_only" not in perms
            ]
        return fields

    @classmethod
    def update_fields(cls, user):
        if user.is_staff or user.site.is_pha:
            fields = [
                field
                for field, perms in cls.FIELD_PERMISSIONS.items()
                if "update" in perms
            ]
        else:
            fields = [
                field
                for field, perms in cls.FIELD_PERMISSIONS.items()
                if "update" in perms and "pha_only" not in perms
            ]
        return fields

    @classmethod
    def no_update_fields(cls, user):
        if user.is_staff or user.site.is_pha:
            fields = [
                field
                for field, perms in cls.FIELD_PERMISSIONS.items()
                if "no update" in perms
            ]
        else:
            fields = [
                field
                for field, perms in cls.FIELD_PERMISSIONS.items()
                if "no update" in perms and "pha_only" not in perms
            ]
        return fields

    @classmethod
    def filter_fields(cls, user):
        if user.is_staff or user.site.is_pha:
            filter_fields = cls.FILTER_FIELDS
        else:
            filter_fields = {}
            for k, v in cls.FILTER_FIELDS.items():
                if "root_field" in v:
                    k = v["root_field"]
                if "pha_only" not in cls.FIELD_PERMISSIONS[k]:
                    filter_fields[k] = v
        return filter_fields

    @classmethod
    def get_serializer(cls, user):
        class PathogenSerializer(serializers.ModelSerializer):

            collection_month = fieldserializers.YearMonthField(
                required=False, allow_null=True
            )
            received_month = fieldserializers.YearMonthField(
                required=False, allow_null=True
            )
            site = serializers.SlugRelatedField(
                queryset=Site.objects.all(), slug_field="code"
            )
            pathogen_code = serializers.SlugRelatedField(
                queryset=PathogenCode.objects.all(), slug_field="code"
            )

            class Meta:
                model = cls
                fields = cls.user_fields(user)

            def validate(self, data):
                """
                Additional validation carried out on either object creation or update

                Update is indicated by the existence of a `self.instance`

                Creation is indicated by `self.instance = None`
                """
                errors = {}
                model = self.Meta.model

                if self.instance:
                    # An update is occuring

                    # Want to ensure each group still has at least one non-null field after update
                    for group in model.OPTIONAL_VALUE_GROUPS:
                        # List of non-null fields from the group
                        instance_group_fields = [
                            field
                            for field in group
                            if getattr(self.instance, field) is not None
                        ]

                        # List of fields specified by the request data that are going to be nullified
                        fields_to_nullify = [
                            field
                            for field in group
                            if field in data and data[field] is None
                        ]

                        # If the resulting set is empty, it means one of two not-good things:
                        # The request contains enough fields from the group being nullified that there will be no non-null fields left from the group
                        # There were (somehow) no non-null fields in the group to begin with
                        if set(instance_group_fields) - set(fields_to_nullify) == set():
                            errors.setdefault("at_least_one_required", []).append(group)

                else:
                    # Creation is occuring
                    # Want to ensure each group has at least one non-null field when creating
                    for group in model.OPTIONAL_VALUE_GROUPS:
                        for field in group:
                            if field in data and data[field] is not None:
                                break
                        else:
                            # If you're reading this I'm sorry
                            # I couldn't help but try a for-else
                            # I just found out it can be done, so I did it :)
                            errors.setdefault("at_least_one_required", []).append(group)

                if errors:
                    raise serializers.ValidationError(errors)

                return data

        return PathogenSerializer


class Mpx(Pathogen):
    fasta_header = models.CharField(max_length=100)
    seq_platform = LowerCharField(
        max_length=50,
        choices=[
            ("illumina", "illumina"),
            ("oxford_nanopore", "oxford_nanopore"),
            ("pacific_biosciences", "pacific_biosciences"),
            ("ion_torrent", "ion_torrent"),
        ],
    )

    FIELD_PERMISSIONS = Pathogen.FIELD_PERMISSIONS | {
        "fasta_header": ["create", "update"],
        "seq_platform": ["create", "update"],
    }

    FILTER_FIELDS = Pathogen.FILTER_FIELDS | {
        "fasta_header": {"type": models.CharField},
        "seq_platform": {"type": models.CharField, "choices": True},
    }

    @classmethod
    def get_serializer(cls, user):
        class MpxSerializer(super().get_serializer(user)):

            seq_platform = fieldserializers.LowerChoiceField(
                choices=Mpx._meta.get_field("seq_platform").choices
            )

            class Meta:
                model = cls
                fields = cls.user_fields(user)

        return MpxSerializer


class Covid(Pathogen):
    fasta_header = models.CharField(max_length=100)
    sample_type = LowerCharField(
        max_length=50, choices=[("swab", "swab"), ("serum", "serum")]
    )

    FIELD_PERMISSIONS = Pathogen.FIELD_PERMISSIONS | {
        "fasta_header": ["create", "update"],
        "sample_type": ["create", "update"],
    }

    FILTER_FIELDS = Pathogen.FILTER_FIELDS | {
        "fasta_header": {"type": models.CharField},
        "sample_type": {"type": models.CharField, "choices": True},
    }

    @classmethod
    def get_serializer(cls, user):
        class CovidSerializer(super().get_serializer(user)):

            sample_type = fieldserializers.LowerChoiceField(
                choices=Covid._meta.get_field("sample_type").choices
            )

            class Meta:
                model = cls
                fields = cls.user_fields(user)

        return CovidSerializer
