from django.db import models
from django.core.validators import MinLengthValidator
from utils.fields import ChoiceField, YearMonthField, UpperCharField
from accounts.models import Site, User
from secrets import token_hex


def generate_cid():
    """
    Simple function that generates a random new CID.

    The CID consists of the prefix `C-` followed by 10 random hex digits.

    This means there are `16^10 = 1,099,511,627,776` CIDs to choose from.
    """
    cid = "C-" + "".join(token_hex(5).upper())

    if Record.objects.filter(cid=cid).exists():
        cid = generate_cid()

    return cid


class OneToOne(models.Model):
    class Meta:
        abstract = True

    class ExtraMeta:
        pass


class ManyToOne(models.Model):
    class Meta:
        abstract = True

    class ExtraMeta:
        pass


class OneToMany(models.Model):
    class Meta:
        abstract = True

    class ExtraMeta:
        pass


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
        default_permissions = []

    class ExtraMeta:
        db_choice_fields = ["site"]
        optional_value_groups = []
        yearmonths = []
        yearmonth_orderings = []
        metrics = []


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
        default_permissions = []

    class ExtraMeta(Record.ExtraMeta):
        yearmonths = Record.ExtraMeta.yearmonths + [
            "collection_month",
            "received_month",
        ]
        yearmonth_orderings = Record.ExtraMeta.yearmonth_orderings + [
            ("collection_month", "received_month")
        ]


class Mpx(Genomic):
    sample_type = ChoiceField(name="sample_type")
    seq_platform = ChoiceField(name="seq_platform")
    enrichment_method = ChoiceField(name="enrichment_method")
    seq_strategy = ChoiceField(name="seq_strategy")
    source_of_library = ChoiceField(name="source_of_library")
    country = ChoiceField(name="country")
    run_layout = ChoiceField(name="run_layout")
    patient_ageband = ChoiceField(name="patient_ageband", null=True)
    sample_site = ChoiceField(name="sample_site", null=True)
    instrument_model = models.TextField()
    bioinfo_pipe_name = models.TextField()
    bioinfo_pipe_version = models.TextField()
    patient_id = models.CharField(
        max_length=24,
        validators=[MinLengthValidator(5)],
        null=True,
    )
    # PHA fields
    ukhsa_region = ChoiceField(name="ukhsa_region", null=True)
    travel_status = ChoiceField(name="travel_status", null=True)
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
        default_permissions = []

    class ExtraMeta(Genomic.ExtraMeta):
        metrics = Genomic.ExtraMeta.metrics + ["thresholdcycle"]


class MpxThresholdCycle(ManyToOne):
    record = models.ForeignKey(
        Record, on_delete=models.CASCADE, related_name="thresholdcycle"
    )
    test_id = models.IntegerField(unique=True)
    ct_value = models.FloatField()

    class Meta:
        default_permissions = []
