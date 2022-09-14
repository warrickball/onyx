from django.db import models
from django.core.validators import MinLengthValidator
from django.db.models import Field
from django.db.models.lookups import BuiltinLookup
from utils.fields import YearMonthField
from secrets import token_hex


# class FastaStats(models.Model):
#     metadata = models.OneToOneField("data.Pathogen", on_delete=models.CASCADE, related_name="fasta")
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


# class BamStats(models.Model):
#     metadata = models.OneToOneField("data.Pathogen", on_delete=models.CASCADE, related_name="bam")
#     num_reads = models.IntegerField()
#     pc_coverage = models.FloatField()
#     mean_depth = models.FloatField()
#     mean_entropy = models.FloatField()

#     # num_pos = models.IntegerField()
#     # mean_cov = models.FloatField()
#     # pc_pos_cov_gte1 = models.FloatField()
#     # pc_pos_cov_gte5 = models.FloatField()
#     # pc_pos_cov_gte10 = models.FloatField()
#     # pc_pos_cov_gte20 = models.FloatField()
#     # pc_pos_cov_gte50 = models.FloatField()
#     # pc_pos_cov_gte100 = models.FloatField()
#     # pc_pos_cov_gte200 = models.FloatField()

#     # NOTE: would need library_primers for tiles
#     # pc_tiles_medcov_gte1 = models.FloatField()
#     # pc_tiles_medcov_gte5 = models.FloatField()
#     # pc_tiles_medcov_gte10 = models.FloatField()
#     # pc_tiles_medcov_gte20 = models.FloatField()
#     # pc_tiles_medcov_gte50 = models.FloatField()
#     # pc_tiles_medcov_gte100 = models.FloatField()
#     # pc_tiles_medcov_gte200 = models.FloatField()
#     # tile_n = models.IntegerField()
#     # tile_vector = models.TextField()


# class VAF(models.Model):
#     bam_stats = models.ForeignKey("data.BamStats", on_delete=models.CASCADE, related_name="vafs")
#     reference = models.CharField(max_length=100)
#     position = models.IntegerField()
#     depth = models.IntegerField()
#     num_a = models.IntegerField()
#     num_c = models.IntegerField()
#     num_g = models.IntegerField()
#     num_t = models.IntegerField()
#     num_ds = models.IntegerField()


def generate_cid():
    cid = "C-" + "".join(token_hex(3).upper())
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


class Pathogen(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)
    suppressed = models.BooleanField(default=False)

    cid = models.CharField(default=generate_cid, max_length=12, unique=True)
    sender_sample_id = models.CharField(
        max_length=24, validators=[MinLengthValidator(8)]
    )
    run_name = models.CharField(max_length=96, validators=[MinLengthValidator(18)])
    pathogen_code = models.CharField(
        max_length=8, choices=[("MPX", "MPX"), ("COVID", "COVID")]
    )
    institute = models.ForeignKey("accounts.Institute", on_delete=models.CASCADE)
    published_date = models.DateField(auto_now_add=True)

    fasta_path = models.TextField()
    bam_path = models.TextField()
    is_external = models.BooleanField()
    collection_month = YearMonthField(null=True)
    received_month = YearMonthField(null=True)

    class Meta:
        unique_together = ["sender_sample_id", "run_name", "pathogen_code"]

    FIELD_PERMISSIONS = {
        "id": ["hidden"],
        "created": ["hidden"],
        "last_modified": ["hidden"],
        "suppressed": ["hidden"],
        "cid": ["no create", "no update"],
        "sender_sample_id": ["create", "no update"],
        "run_name": ["create", "no update"],
        "pathogen_code": ["create", "no update"],
        "institute": ["create", "no update"],
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
        "pathogen_code": {"type": models.CharField, "db_choices": True},
        "institute__code": {
            "type": models.CharField,
            "db_choices": True,
            "alias": "institute",
        },
        "published_date": {"type": models.DateField},
        "fasta_path": {"type": models.TextField},
        "bam_path": {"type": models.TextField},
        "is_external": {"type": models.BooleanField},
        "collection_month": {"type": YearMonthField},
        "received_month": {"type": YearMonthField},
    }

    OPTIONAL_VALUE_GROUPS = [["collection_month", "received_month"]]

    @classmethod
    def hidden_fields(cls):
        return [
            field for field, perms in cls.FIELD_PERMISSIONS.items() if "hidden" in perms
        ]

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
            if "no create" in perms
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
            if "no update" in perms
        ]


class Mpx(Pathogen):
    fasta_header = models.CharField(max_length=100)
    # sample_type = models.CharField(max_length=16, validators=[MinLengthValidator(8)])
    # run_sequencer = models.CharField(max_length=96)
    # run_seq_protocol = models.CharField(max_length=96)
    # run_layout = models.CharField(
    #     choices=[
    #         ("SINGLE", "SINGLE"),
    #         ("PAIRED", "PAIRED"),
    #     ]
    # )
    # run_selection = models.CharField(
    #     choices=[
    #         ("PCR", "PCR"),
    #         ("RANDOM", "RANDOM"),
    #         ("RANDOM_PCR", "RANDOM_PCR"),
    #         ("NONE", "NONE"),
    #         ("OTHER", "OTHER")
    #     ]
    # )
    # seq_approach = models.CharField(
    #     choices=[
    #         ("GENOMIC", "GENOMIC"),
    #         ("METAGENOMIC", "METAGENOMIC"),
    #         ("METATRANSCRIPTOMIC", "METATRANSCRIPTOMIC"),
    #         ("TRANSCRIPTOMIC", "TRANSCRIPTOMIC"),
    #         ("VIRAL_RNA", "VIRAL_RNA"),
    #         ("OTHER", "OTHER")
    #     ]
    # )
    # seq_strategy = models.CharField(
    #     choices=[
    #         ("AMPICON", "AMPLICON"),
    #         ("TARGETED_CAPTURE", "TARGETED_CAPTURE"),
    #         ("WGA", "WGA"),
    #         ("WGS", "WGS"),
    #         ("OTHER", "OTHER")
    #     ]
    # )
    seq_platform = models.CharField(
        max_length=50,
        choices=[
            ("ILLUMINA", "ILLUMINA"),
            ("OXFORD_NANOPORE", "OXFORD_NANOPORE"),
            ("PACIFIC_BIOSCIENCES", "PACIFIC_BIOSCIENCES"),
            ("ION_TORRENT", "ION_TORRENT"),
        ],
    )
    # instrument_model = models.CharField(max_length=48)
    # bioinfo_pipe_name = models.CharField(max_length=96)
    # bioinfo_pipe_version = models.CharField(max_length=48)
    # previous_sample_id = models.CharField(null=True, max_length=24, validators=[MinLengthValidator(8)])

    FIELD_PERMISSIONS = Pathogen.FIELD_PERMISSIONS | {
        "fasta_header": ["create", "update"],
        "seq_platform": ["create", "update"],
    }

    FILTER_FIELDS = Pathogen.FILTER_FIELDS | {
        "fasta_header": {"type": models.CharField},
        "seq_platform": {"type": models.CharField, "choices": True},
    }


class Covid(Pathogen):
    fasta_header = models.CharField(max_length=100)
    sample_type = models.CharField(
        max_length=50, choices=[("SWAB", "SWAB"), ("SERUM", "SERUM")]
    )

    FIELD_PERMISSIONS = Pathogen.FIELD_PERMISSIONS | {
        "fasta_header": ["create", "update"],
        "sample_type": ["create", "update"],
    }

    FILTER_FIELDS = Pathogen.FILTER_FIELDS | {
        "fasta_header": {"type": models.CharField},
        "sample_type": {"type": models.CharField, "choices": True},
    }
