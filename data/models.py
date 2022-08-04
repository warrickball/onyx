from django.db import models
from utils.fields import YearMonthField
from secrets import token_hex


def generate_cid():
    cid = "C-" + "".join(token_hex(3).upper())
    if Pathogen.objects.filter(cid=cid).exists():
        cid = generate_cid()
    return cid


class Pathogen(models.Model):
    # Non-updatable fields
    cid = models.CharField(
        default=generate_cid,
        max_length=12, 
        unique=True
    )
    sender_sample_id = models.CharField(max_length=24)
    run_name = models.CharField(max_length=96)
    pathogen_code = models.CharField(
        max_length=8,
        choices=[
            ("PATHOGEN", "PATHOGEN"), # TODO: is only here for tests. Find way to make tests work without it
            ("MPX", "MPX"),
            ("COVID", "COVID")
        ]
    )
    institute = models.ForeignKey("accounts.Institute", on_delete=models.CASCADE)
    published_date = models.DateField(auto_now_add=True)
    created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    # Updatable fields
    fasta_path = models.CharField(max_length=200)
    bam_path = models.TextField(max_length=200)
    is_external = models.BooleanField()
    collection_month = YearMonthField()
    received_month = YearMonthField()
    # fasta_stats = models.ForeignKey("FastaStats", on_delete=models.CASCADE) # TODO:?
    # bam_stats = models.ForeignKey("BamStats", on_delete=models.CASCADE) # TODO:?

    @classmethod
    def all_fields(cls):
        '''
        All fields of the model
        '''
        return {f.name for f in cls._meta.get_fields()}

    @classmethod
    def internal_fields(cls):
        '''
        Fields that cannot be user-submitted on creation of a model instance
        '''
        return {"id", "cid", "published_date", "created", "last_modified"}

    @classmethod
    def readonly_fields(cls):
        '''
        Fields that cannot be user-submitted on updating of a model instance
        '''
        return {"id", "cid", "sender_sample_id", "run_name", "pathogen_code", "institute", "published_date", "created", "last_modified"}
    
    @classmethod
    def choice_fields(cls):
        '''
        Fields with restricted choice of input
        '''
        return {"pathogen_code", "institute"} # NOTE: Institute being here may cause some weird stuff

    class Meta:
        unique_together = [
            "sender_sample_id", 
            "run_name",
            "pathogen_code"
        ]


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
    def choice_fields(cls):
        return super().choice_fields() | {"seq_platform"}


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
    def choice_fields(cls):
        return super().choice_fields() | {"sample_type"}
