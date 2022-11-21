from django.db import models
from django.core.validators import MinLengthValidator
from django.db.models import Field
from django.db.models.lookups import BuiltinLookup
from secrets import token_hex
from utils.fields import YearMonthField, LowerCharField


def generate_cid():
    """
    Simple function that generates a random new CID.

    The CID consists of the prefix `C-` followed by 8 random hex digits.

    This means there are `16^8 = 4,294,967,296` CIDs to choose from - should be enough!
    """
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


# class FastaStatistics(models.Model):
#     metadata = models.OneToOneField(
#         "data.Pathogen", on_delete=models.CASCADE, related_name="fasta"
#     )
#     fasta_header = models.CharField(max_length=100)
#     num_seqs = models.IntegerField()
#     num_bases = models.IntegerField()
#     pc_acgt = models.FloatField()
#     gc_content = models.FloatField()
#     pc_masked = models.FloatField()
#     pc_invalid = models.FloatField()
#     pc_ambig = models.FloatField()
#     pc_ambig_2 = models.FloatField()
#     pc_ambig_3 = models.FloatField()
#     longest_acgt = models.IntegerField()
#     longest_masked = models.IntegerField()
#     longest_invalid = models.IntegerField()
#     longest_ambig = models.IntegerField()
#     longest_gap = models.IntegerField()
#     longest_ungap = models.IntegerField()


class Signal(models.Model):
    code = LowerCharField(max_length=8, unique=True)
    modified = models.DateTimeField()


class PathogenCode(models.Model):
    code = LowerCharField(max_length=8, unique=True)


class Pathogen(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)
    suppressed = models.BooleanField(default=False)

    pathogen_code = models.ForeignKey("PathogenCode", on_delete=models.CASCADE)
    site = models.ForeignKey("accounts.Site", on_delete=models.CASCADE)
    cid = models.CharField(default=generate_cid, max_length=12, unique=True)
    sample_id = models.CharField(max_length=24, validators=[MinLengthValidator(8)])
    run_name = models.CharField(max_length=96, validators=[MinLengthValidator(18)])

    collection_month = YearMonthField(null=True)
    received_month = YearMonthField()
    published_date = models.DateField(auto_now_add=True)

    fasta_path = models.TextField()
    bam_path = models.TextField()

    class Meta:
        unique_together = ["pathogen_code", "sample_id", "run_name"]
        indexes = [
            models.Index(fields=["cid"]),
            models.Index(fields=["sample_id"]),
            models.Index(fields=["run_name"]),
            models.Index(fields=["sample_id", "run_name"]),
            models.Index(fields=["collection_month"]),
            models.Index(fields=["received_month"]),
            models.Index(fields=["published_date"]),
            models.Index(fields=["fasta_path"]),
            models.Index(fields=["bam_path"]),
        ]

    FIELD_PERMISSIONS = {
        "id": [],
        "created": [],
        "last_modified": [],
        "suppressed": [],
        "pathogen_code": ["create"],
        "site": ["create"],
        "cid": [],
        "sample_id": ["create"],
        "run_name": ["create"],
        "collection_month": ["create", "update"],
        "received_month": ["create", "update"],
        "published_date": [],
        "fasta_path": ["create", "update"],
        "bam_path": ["create", "update"],
    }

    FILTER_FIELDS = {
        "id": {"type": models.IntegerField},
        "created": {"type": models.DateTimeField},
        "last_modified": {"type": models.DateTimeField},
        "suppressed": {"type": models.BooleanField},
        "pathogen_code__code": {
            "type": models.CharField,
            "db_choices": True,
            "alias": "pathogen_code",
        },
        "site__code": {
            "type": models.CharField,
            "db_choices": True,
            "alias": "site",
        },
        "cid": {"type": models.CharField},
        "sample_id": {"type": models.CharField},
        "run_name": {"type": models.CharField},
        "collection_month": {"type": YearMonthField},
        "received_month": {"type": YearMonthField},
        "published_date": {"type": models.DateField},
        "fasta_path": {"type": models.TextField},
        "bam_path": {"type": models.TextField},
    }

    OPTIONAL_VALUE_GROUPS = []

    @classmethod
    def create_fields(cls):
        return [
            field for field, perms in cls.FIELD_PERMISSIONS.items() if "create" in perms
        ]

    @classmethod
    def no_create_fields(cls):
        return [
            field
            for field, perms in cls.FIELD_PERMISSIONS.items()
            if "create" not in perms
        ]

    @classmethod
    def update_fields(cls):
        return [
            field for field, perms in cls.FIELD_PERMISSIONS.items() if "update" in perms
        ]

    @classmethod
    def no_update_fields(cls):
        return [
            field
            for field, perms in cls.FIELD_PERMISSIONS.items()
            if "update" not in perms
        ]


class Mpx(Pathogen):
    sample_type = LowerCharField(
        max_length=50, choices=[("swab", "swab"), ("serum", "serum")]
    )
    seq_platform = LowerCharField(
        max_length=50,
        choices=[
            ("illumina", "illumina"),
            ("oxford_nanopore", "oxford_nanopore"),
            ("pacific_biosciences", "pacific_biosciences"),
            ("ion_torrent", "ion_torrent"),
        ],
    )
    instrument_model = models.TextField()
    enrichment_method = LowerCharField(
        max_length=50,
        choices=[
            ("other", "other"),
            ("pcr", "pcr"),
            ("random", "random"),
            ("random_pcr", "random_pcr"),
            ("none", "none"),
        ],
    )
    seq_strategy = LowerCharField(
        max_length=50,
        choices=[
            ("amplicon", "amplicon"),
            ("other", "other"),
            ("targeted_capture", "targeted_capture"),
            ("wga", "wga"),
            ("wgs", "wgs"),
        ],
    )
    source_of_library = LowerCharField(
        max_length=50,
        choices=[
            ("genomic", "genomic"),
            ("metagenomic", "metagenomic"),
            ("metatranscriptomic", "metatranscriptomic"),
            ("other", "other"),
            ("transcriptomic", "transcriptomic"),
            ("viral_rna", "viral_rna"),
        ],
    )
    bioinfo_pipe_name = models.TextField()
    bioinfo_pipe_version = models.TextField()
    country = LowerCharField(
        max_length=50,
        choices=[
            ("eng", "eng"),
            ("wales", "wales"),
            ("scot", "scot"),
            ("ni", "ni"),
        ],
    )
    ukhsa_region = LowerCharField(max_length=50, choices=[("ne", "ne")])
    run_layout = LowerCharField(
        max_length=50, choices=[("single", "single"), ("paired", "paired")]
    )
    patient_ageband = LowerCharField(
        max_length=50,
        choices=[
            ("0-5", "0-5"),
            ("6-10", "6-10"),
            ("11-15", "11-15"),
            ("16-20", "16-20"),
            ("21-25", "21-25"),
            ("26-30", "26-30"),
            ("31-35", "31-35"),
            ("36-40", "36-40"),
            ("41-45", "41-45"),
            ("46-50", "46-50"),
            ("51-55", "51-55"),
            ("56-60", "56-60"),
            ("61-65", "61-65"),
            ("66-70", "66-70"),
            ("71-75", "71-75"),
            ("76-80", "76-80"),
            ("81-85", "81-85"),
            ("86-90", "86-90"),
            ("91-95", "91-95"),
            ("96-100", "96-100"),
            ("100+", "100+"),
        ],
        null=True,
    )
    travel_status = LowerCharField(
        max_length=50, choices=[("yes", "yes"), ("no", "no")], null=True
    )
    outer_postcode = models.CharField(
        max_length=5, validators=[MinLengthValidator(3)], null=True
    )
    epi_cluster = models.CharField(
        max_length=24, validators=[MinLengthValidator(5)], null=True
    )
    patient_id = models.CharField(
        max_length=24, validators=[MinLengthValidator(5)], null=True
    )
    sample_site = LowerCharField(
        max_length=50, choices=[("sore", "sore"), ("genital", "genital")], null=True
    )
    csv_template_version = models.TextField()

    FIELD_PERMISSIONS = Pathogen.FIELD_PERMISSIONS | {
        "sample_type": ["create", "update"],
        "sample_site": ["create", "update"],
        "patient_ageband": ["create", "update"],
        "country": ["create", "update"],
        "ukhsa_region": ["create", "update"],
        "outer_postcode": ["create", "update"],
        "epi_cluster": ["create", "update"],
        "travel_status": ["create", "update"],
        "patient_id": ["create", "update"],
        "seq_platform": ["create", "update"],
        "instrument_model": ["create", "update"],
        "run_layout": ["create", "update"],
        "enrichment_method": ["create", "update"],
        "source_of_library": ["create", "update"],
        "seq_strategy": ["create", "update"],
        "bioinfo_pipe_name": ["create", "update"],
        "bioinfo_pipe_version": ["create", "update"],
        "csv_template_version": ["create"],
    }

    FILTER_FIELDS = Pathogen.FILTER_FIELDS | {
        "sample_type": {"type": LowerCharField, "choices": True},
        "sample_site": {"type": LowerCharField, "choices": True},
        "patient_ageband": {"type": LowerCharField, "choices": True},
        "country": {"type": LowerCharField, "choices": True},
        "ukhsa_region": {"type": LowerCharField, "choices": True},
        "outer_postcode": {"type": models.CharField},
        "epi_cluster": {"type": models.CharField},
        "travel_status": {"type": LowerCharField, "choices": True},
        "patient_id": {"type": models.CharField},
        "seq_platform": {"type": LowerCharField, "choices": True},
        "instrument_model": {"type": models.TextField},
        "run_layout": {"type": LowerCharField, "choices": True},
        "enrichment_method": {"type": LowerCharField, "choices": True},
        "source_of_library": {"type": LowerCharField, "choices": True},
        "seq_strategy": {"type": LowerCharField, "choices": True},
        "bioinfo_pipe_name": {"type": models.TextField},
        "bioinfo_pipe_version": {"type": models.TextField},
        "csv_template_version": {"type": models.TextField},
    }
