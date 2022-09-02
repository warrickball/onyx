from django.db import models
from utils.fields import YearMonthField
from secrets import token_hex
from accounts.models import Institute
from utils.functions import get_field_values


# class FastaStats(models.Model):
#     metadata = models.OneToOneField("data.Pathogen", on_delete=models.CASCADE, related_name="fasta")
#     # TODO: fasta header ?
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

#     # TODO: would need library_primers for tiles
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


@models.Field.register_lookup
class NotEqual(models.Lookup):
    lookup_name = 'ne'

    def as_sql(self, compiler, connection):
        lhs, lhs_params = self.process_lhs(compiler, connection)
        rhs, rhs_params = self.process_rhs(compiler, connection)
        params = lhs_params + rhs_params
        return '%s <> %s' % (lhs, rhs), params


# TODO: Structure containing all fields and their create, update, etc status
class Pathogen(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)
    suppressed = models.BooleanField(default=False)

    cid = models.CharField(default=generate_cid, max_length=12, unique=True)
    sample_id = models.CharField(max_length=24)
    run_name = models.CharField(max_length=96)
    pathogen_code = models.CharField(
        max_length=8,
        choices=[
            ("MPX", "MPX"),
            ("COVID", "COVID")
        ]
    )
    institute = models.ForeignKey("accounts.Institute", on_delete=models.CASCADE)
    published_date = models.DateField(auto_now_add=True)

    fasta_path = models.TextField()
    bam_path = models.TextField()
    is_external = models.CharField(
        max_length=1,
        choices=[
            ("Y", "Y"),
            ("N", "N")
        ]
    )
    collection_month = YearMonthField(null=True)
    received_month = YearMonthField(null=True)

    class Meta:
        unique_together = [
            "sample_id", 
            "run_name",
            "pathogen_code"
        ]
    
    @classmethod
    def optional_value_groups(cls):
        return [
            ["collection_month", "received_month"]
        ]

    @classmethod
    def excluded_fields(cls):
        '''
        Fields that are excluded when sending data to the client.
        '''
        return ["id", "created", "last_modified", "suppressed"]
    
    @classmethod
    def create_fields(cls):
        '''
        Fields that can be submitted on creation of a model instance.
        '''
        return {"sample_id", "run_name", "pathogen_code", "institute", "published_date", "fasta_path", "bam_path", "is_external", "collection_month", "received_month"}
    
    @classmethod
    def non_create_fields(cls):
        '''
        Fields that cannot be submitted on creation of a model instance.
        '''
        return {"cid", "published_date"}
    
    @classmethod
    def update_fields(cls):
        '''
        Fields that can be submitted on update of a model instance.
        '''
        return {"fasta_path", "bam_path", "is_external", "collection_month", "received_month"}

    @classmethod
    def non_update_fields(cls):
        '''
        Fields that cannot be submitted on update of a model instance.
        '''
        return {"cid", "sample_id", "run_name", "pathogen_code", "institute", "published_date"}

    @classmethod
    def filter_fields(cls):
        '''
        Fields that can be filtered on, and their types.
        '''
        return {
            "cid" : models.CharField,
            "sample_id" : models.CharField,
            "run_name" : models.CharField,
            "pathogen_code" : models.CharField,
            "institute__code" : models.CharField,
            "published_date" : models.DateField,
            "fasta_path" : models.TextField,
            "bam_path" : models.TextField,
            "is_external" : models.CharField,
            "collection_month" : YearMonthField,
            "received_month" : YearMonthField
        }
    
    @classmethod
    def choice_filter_fields(cls):
        '''
        Fields with a restricted number of options.
        '''
        return {"pathogen_code", "institute__code", "is_external"}
    
    @classmethod
    def aliases(cls):
        '''
        Fields with alternate names used when filtering.
        '''
        return {
            "institute__code" : "institute"
        }

    @classmethod
    def get_institute__code_choices(cls):
        values = get_field_values(Institute, "code")
        return zip(values, values)

    @classmethod
    def get_choices(cls, field):
        # Bit dodgy
        if hasattr(cls, f"get_{field}_choices"):
            return getattr(cls, f"get_{field}_choices")()
        else:
            choices = cls._meta.get_field(field).choices  # type: ignore
            if choices:
                return [choice for choice in choices]
            else:
                return []


class Mpx(Pathogen):
    fasta_header = models.CharField(max_length=100)
    seq_platform = models.CharField(
        max_length=50,
        choices=[
            ("ILLUMINA", "ILLUMINA"),
            ("OXFORD_NANOPORE", "OXFORD_NANOPORE"),
            ("PACIFIC_BIOSCIENCES", "PACIFIC_BIOSCIENCES"),
            ("ION_TORRENT", "ION_TORRENT")
        ]
    )

    @classmethod
    def create_fields(cls):
        return super().create_fields() | {"fasta_header", "seq_platform"}
    
    @classmethod
    def update_fields(cls):
        return super().update_fields() | {"fasta_header", "seq_platform"}
    
    @classmethod
    def filter_fields(cls):
        pathogen_fields = super().filter_fields()
        mpx_fields = {
            "fasta_header" : models.CharField,
            "seq_platform" : models.CharField
        }
        return pathogen_fields | mpx_fields

    @classmethod
    def choice_filter_fields(cls):
        return super().choice_filter_fields() | {"seq_platform"}


class Covid(Pathogen):
    fasta_header = models.CharField(max_length=100)
    sample_type = models.CharField(
        max_length=50,
        choices=[
            ("SWAB", "SWAB"),
            ("SERUM", "SERUM")
        ]
    )

    @classmethod
    def create_fields(cls):
        return super().create_fields() | {"fasta_header", "sample_type"}
    
    @classmethod
    def update_fields(cls):
        return super().update_fields() | {"fasta_header", "sample_type"}

    @classmethod
    def filter_fields(cls):
        pathogen_fields = super().filter_fields()
        covid_fields = {
            "fasta_header" : models.CharField,
            "sample_type" : models.CharField
        }
        return pathogen_fields | covid_fields

    @classmethod
    def choice_filter_fields(cls):
        return super().choice_filter_fields() | {"sample_type"}
