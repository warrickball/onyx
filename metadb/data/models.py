from django.db import models
from django.core.validators import MinLengthValidator
from django.db.models import Field
from django.db.models.lookups import BuiltinLookup
from django.contrib.auth.models import Group
from secrets import token_hex
from utils.fields import YearMonthField, LowerCharField
from utils.functions import get_choices
from utils import choices


def generate_cid():
    """
    Simple function that generates a random new CID.

    The CID consists of the prefix `C-` followed by 8 random hex digits.

    This means there are `16^8 = 4,294,967,296` CIDs to choose from - should be enough!
    """
    cid = "C-" + "".join(token_hex(4).upper())

    if ProjectItem.objects.filter(cid=cid).exists():
        cid = generate_cid()

    return cid


def generate_permissions(model_name, fields):
    return [
        (f"{action}_{model_name}__{x}", f"Can {action} {model_name} {x}")
        for action in ["add", "change", "delete", "view"]
        for x in fields
    ]


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


class Signal(models.Model):
    code = LowerCharField(max_length=8, unique=True)
    modified = models.DateTimeField(auto_now=True)


class GroupCluster(models.Model):
    name = models.TextField(unique=True)
    groups = models.ManyToManyField(Group)


class Project(models.Model):
    code = LowerCharField(max_length=8, unique=True)


class ProjectItem(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)
    suppressed = models.BooleanField(default=False)
    project = models.ForeignKey("Project", on_delete=models.CASCADE)
    site = models.ForeignKey("accounts.Site", on_delete=models.CASCADE)
    cid = models.CharField(default=generate_cid, max_length=12, unique=True)
    published_date = models.DateField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["site"]),
            models.Index(fields=["cid"]),
            models.Index(fields=["published_date"]),
        ]

        permissions = generate_permissions(
            model_name="projectitem",
            fields=[
                "project",
                "created",
                "last_modified",
                "suppressed",
                "site",
                "cid",
                "published_date",
            ],
        )

    FILTER_FIELDS = {
        "id": {"type": models.IntegerField},
        "created": {"type": models.DateTimeField},
        "last_modified": {"type": models.DateTimeField},
        "suppressed": {"type": models.BooleanField},
        "project__code": {
            "type": models.CharField,
            "db_choices": True,
            "alias": "project",
        },
        "site__code": {
            "type": models.CharField,
            "db_choices": True,
            "alias": "site",
        },
        "cid": {"type": models.CharField},
        "published_date": {"type": models.DateField},
    }

    OPTIONAL_VALUE_GROUPS = []


class Pathogen(ProjectItem):
    sample_id = models.CharField(max_length=24, validators=[MinLengthValidator(8)])
    run_name = models.CharField(max_length=96, validators=[MinLengthValidator(18)])
    collection_month = YearMonthField(null=True)
    received_month = YearMonthField()
    fasta_path = models.TextField()
    bam_path = models.TextField()

    class Meta:
        unique_together = ["sample_id", "run_name"]
        indexes = [
            models.Index(fields=["sample_id"]),
            models.Index(fields=["run_name"]),
            models.Index(fields=["sample_id", "run_name"]),
            models.Index(fields=["collection_month"]),
            models.Index(fields=["received_month"]),
            models.Index(fields=["fasta_path"]),
            models.Index(fields=["bam_path"]),
        ]

        permissions = generate_permissions(
            model_name="pathogen",
            fields=[
                "sample_id",
                "run_name",
                "collection_month",
                "received_month",
                "fasta_path",
                "bam_path",
            ],
        )

    FILTER_FIELDS = ProjectItem.FILTER_FIELDS | {
        "sample_id": {"type": models.CharField},
        "run_name": {"type": models.CharField},
        "collection_month": {"type": YearMonthField},
        "received_month": {"type": YearMonthField},
        "fasta_path": {"type": models.TextField},
        "bam_path": {"type": models.TextField},
    }


class Metagenomic(ProjectItem):
    fastq_path = models.TextField()

    class Meta:
        permissions = generate_permissions(
            model_name="metagenomic",
            fields=["fastq_path"],
        )


class Mpx(Pathogen):
    csv_template_version = models.TextField()
    sample_type = LowerCharField(
        max_length=50,
        choices=get_choices(choices.SAMPLE_TYPE_CHOICES),
    )
    seq_platform = LowerCharField(
        max_length=50,
        choices=get_choices(choices.SEQ_PLATFORM_CHOICES),
    )
    instrument_model = models.TextField()
    enrichment_method = LowerCharField(
        max_length=50,
        choices=get_choices(choices.ENRICHMENT_METHOD_CHOICES),
    )
    seq_strategy = LowerCharField(
        max_length=50,
        choices=get_choices(choices.SEQ_STRATEGY_CHOICES),
    )
    source_of_library = LowerCharField(
        max_length=50,
        choices=get_choices(choices.SOURCE_OF_LIBRARY_CHOICES),
    )
    bioinfo_pipe_name = models.TextField()
    bioinfo_pipe_version = models.TextField()
    country = LowerCharField(
        max_length=50,
        choices=get_choices(choices.COUNTRY_CHOICES),
    )
    run_layout = LowerCharField(
        max_length=50,
        choices=get_choices(choices.RUN_LAYOUT_CHOICES),
    )
    patient_ageband = LowerCharField(
        max_length=50,
        choices=get_choices(choices.PATIENT_AGEBAND_CHOICES),
        null=True,
    )
    patient_id = models.CharField(
        max_length=24, validators=[MinLengthValidator(5)], null=True
    )
    sample_site = LowerCharField(
        max_length=50,
        choices=get_choices(choices.SAMPLE_SITE_CHOICES),
        null=True,
    )

    class Meta:
        permissions = generate_permissions(
            model_name="mpx",
            fields=[
                "csv_template_version",
                "sample_type",
                "sample_site",
                "patient_ageband",
                "country",
                "patient_id",
                "seq_platform",
                "instrument_model",
                "run_layout",
                "enrichment_method",
                "source_of_library",
                "seq_strategy",
                "bioinfo_pipe_name",
                "bioinfo_pipe_version",
            ],
        )

    FILTER_FIELDS = Pathogen.FILTER_FIELDS | {
        "csv_template_version": {"type": models.TextField},
        "sample_type": {"type": LowerCharField, "choices": True},
        "sample_site": {"type": LowerCharField, "choices": True},
        "patient_ageband": {"type": LowerCharField, "choices": True},
        "country": {"type": LowerCharField, "choices": True},
        "patient_id": {"type": models.CharField},
        "seq_platform": {"type": LowerCharField, "choices": True},
        "instrument_model": {"type": models.TextField},
        "run_layout": {"type": LowerCharField, "choices": True},
        "enrichment_method": {"type": LowerCharField, "choices": True},
        "source_of_library": {"type": LowerCharField, "choices": True},
        "seq_strategy": {"type": LowerCharField, "choices": True},
        "bioinfo_pipe_name": {"type": models.TextField},
        "bioinfo_pipe_version": {"type": models.TextField},
    }


class MpxPha(Mpx):
    ukhsa_region = LowerCharField(
        max_length=50,
        choices=get_choices(choices.UKHSA_REGION_CHOICES),
    )
    travel_status = LowerCharField(
        max_length=50,
        choices=get_choices(choices.TRAVEL_STATUS_CHOICES),
        null=True,
    )
    outer_postcode = models.CharField(
        max_length=5, validators=[MinLengthValidator(3)], null=True
    )
    epi_cluster = models.CharField(
        max_length=24, validators=[MinLengthValidator(5)], null=True
    )

    class Meta:
        permissions = generate_permissions(
            model_name="mpxpha",
            fields=[
                "ukhsa_region",
                "travel_status",
                "outer_postcode",
                "epi_cluster",
            ],
        )

    FILTER_FIELDS = Mpx.FILTER_FIELDS | {
        "ukhsa_region": {"type": LowerCharField, "choices": True},
        "travel_status": {"type": LowerCharField, "choices": True},
        "outer_postcode": {"type": models.CharField},
        "epi_cluster": {"type": models.CharField},
    }
