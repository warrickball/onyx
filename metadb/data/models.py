from django.db import models
from django.core.validators import MinLengthValidator
from utils.fields import YearMonthField, UpperCharField
from utils.permissions import generate_permissions
from accounts.models import Site, User
from internal.models import Choice
from secrets import token_hex


def generate_cid():
    """
    Simple function that generates a random new CID.

    The CID consists of the prefix `C-` followed by 8 random hex digits.

    This means there are `16^10 = 1,099,511,627,776` CIDs to choose from
    """
    cid = "C-" + "".join(token_hex(5).upper())

    if Record.objects.filter(cid=cid).exists():
        cid = generate_cid()

    return cid


class Record(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)
    suppressed = models.BooleanField(default=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    site = models.ForeignKey(Site, to_field="code", on_delete=models.CASCADE)
    cid = UpperCharField(default=generate_cid, max_length=12, unique=True)
    published_date = models.DateField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["site", "published_date"]),
            models.Index(fields=["site"]),
            models.Index(fields=["cid"]),
            models.Index(fields=["published_date"]),
        ]
        default_permissions = ["add", "change", "view", "delete", "suppress"]
        permissions = generate_permissions(
            model_name="record",
            fields=[
                "created",
                "last_modified",
                "suppressed",
                "user",
                "site",
                "cid",
                "published_date",
            ],
        )

    class CustomMeta:
        db_choice_fields = ["site"]
        optional_value_groups = []
        yearmonths = []
        yearmonth_orderings = []


class Genomic(Record):
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
        default_permissions = ["add", "change", "view", "delete", "suppress"]
        permissions = generate_permissions(
            model_name="genomic",
            fields=[
                "sample_id",
                "run_name",
                "collection_month",
                "received_month",
                "fasta_path",
                "bam_path",
            ],
        )

    class CustomMeta(Record.CustomMeta):
        yearmonths = Record.CustomMeta.yearmonths + [
            "collection_month",
            "received_month",
        ]
        yearmonth_orderings = Record.CustomMeta.yearmonth_orderings + [
            ("collection_month", "received_month")
        ]


class Metagenomic(Record):
    sample_id = models.CharField(max_length=24, validators=[MinLengthValidator(8)])
    run_name = models.CharField(max_length=96, validators=[MinLengthValidator(18)])
    collection_month = YearMonthField(null=True)
    received_month = YearMonthField()
    fastq_path = models.TextField()
    sample_type = models.ForeignKey(
        Choice,
        on_delete=models.CASCADE,
        related_name="%(app_label)s_%(class)s_sample_type",
    )
    seq_platform = models.ForeignKey(
        Choice,
        on_delete=models.CASCADE,
        related_name="%(app_label)s_%(class)s_seq_platform",
    )

    class Meta:
        unique_together = ["sample_id", "run_name"]
        indexes = [
            models.Index(fields=["sample_id"]),
            models.Index(fields=["run_name"]),
            models.Index(fields=["sample_id", "run_name"]),
            models.Index(fields=["collection_month"]),
            models.Index(fields=["received_month"]),
            models.Index(fields=["fastq_path"]),
        ]
        default_permissions = ["add", "change", "view", "delete", "suppress"]
        permissions = generate_permissions(
            model_name="metagenomic",
            fields=[
                "sample_id",
                "run_name",
                "collection_month",
                "received_month",
                "fastq_path",
            ],
        )


class Mpx(Genomic):
    sample_type = models.ForeignKey(
        Choice,
        on_delete=models.CASCADE,
        related_name="%(app_label)s_%(class)s_sample_type",
    )
    seq_platform = models.ForeignKey(
        Choice,
        on_delete=models.CASCADE,
        related_name="%(app_label)s_%(class)s_seq_platform",
    )
    enrichment_method = models.ForeignKey(
        Choice,
        on_delete=models.CASCADE,
        related_name="%(app_label)s_%(class)s_enrichment_method",
    )
    seq_strategy = models.ForeignKey(
        Choice,
        on_delete=models.CASCADE,
        related_name="%(app_label)s_%(class)s_seq_strategy",
    )
    source_of_library = models.ForeignKey(
        Choice,
        on_delete=models.CASCADE,
        related_name="%(app_label)s_%(class)s_source_of_library",
    )
    country = models.ForeignKey(
        Choice,
        on_delete=models.CASCADE,
        related_name="%(app_label)s_%(class)s_country",
    )
    run_layout = models.ForeignKey(
        Choice,
        on_delete=models.CASCADE,
        related_name="%(app_label)s_%(class)s_run_layout",
    )
    patient_ageband = models.ForeignKey(
        Choice,
        on_delete=models.CASCADE,
        related_name="%(app_label)s_%(class)s_patient_ageband",
        null=True,
    )
    sample_site = models.ForeignKey(
        Choice,
        on_delete=models.CASCADE,
        related_name="%(app_label)s_%(class)s_sample_site",
        null=True,
    )
    instrument_model = models.TextField()
    bioinfo_pipe_name = models.TextField()
    bioinfo_pipe_version = models.TextField()
    patient_id = models.CharField(
        max_length=24,
        validators=[MinLengthValidator(5)],
        null=True,
    )
    # PHA fields
    ukhsa_region = models.ForeignKey(
        Choice,
        on_delete=models.CASCADE,
        related_name="%(app_label)s_%(class)s_ukhsa_region",
        null=True,
    )
    travel_status = models.ForeignKey(
        Choice,
        on_delete=models.CASCADE,
        related_name="%(app_label)s_%(class)s_travel_status",
        null=True,
    )
    outer_postcode = models.CharField(
        max_length=5,
        validators=[MinLengthValidator(3)],
        null=True,
    )
    epi_cluster = models.CharField(
        max_length=24,
        validators=[MinLengthValidator(5)],
        null=True,
    )
    # Admin fields
    csv_template_version = models.TextField(null=True)

    class Meta:
        default_permissions = ["add", "change", "view", "delete", "suppress"]
        permissions = generate_permissions(
            model_name="mpx",
            fields=[
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
                "ukhsa_region",
                "travel_status",
                "outer_postcode",
                "epi_cluster",
                "csv_template_version",
            ],
        )
