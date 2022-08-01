from django.db import models
from utils.fields import YearMonthField
from secrets import token_hex


def generate_cid():
    cid = "C-" + "".join(token_hex(3).upper())
    if Pathogen.objects.filter(cid=cid).exists():
        cid = generate_cid()
    return cid


class Pathogen(models.Model):
    cid = models.CharField(
        default=generate_cid,
        max_length=12, 
        unique=True
    )
    pathogen_code = models.CharField(
        max_length=8,
        choices=[
            ("PATHOGEN", "PATHOGEN"), # TODO: is only here for tests. Find way to make tests work without it
            ("MPX", "MPX"),
            ("COVID", "COVID")
        ]
    )
    institute = models.ForeignKey("accounts.Institute", on_delete=models.CASCADE)
    sender_sample_id = models.CharField(max_length=24) # TODO: Should this + run name not be updateable?
    run_name = models.CharField(max_length=96)
    fasta_path = models.CharField(max_length=200)
    bam_path = models.TextField(max_length=200)
    is_external = models.BooleanField() # TODO: need to add + test some optional fields, could make this optional (with default false for example)
    collection_month = YearMonthField()
    received_month = YearMonthField()
    published_date = models.DateField(auto_now_add=True)
    created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)
    # fasta_stats = models.ForeignKey("FastaStats", on_delete=models.CASCADE) # TODO:?
    # bam_stats = models.ForeignKey("BamStats", on_delete=models.CASCADE) # TODO:?

    class Meta:
        unique_together = [
            "sender_sample_id", 
            "run_name"
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


class Covid(Pathogen):
    fasta_header = models.CharField(max_length=100)
    sample_type = models.CharField(
        max_length=50,
        choices=[
            ("SWAB", "SWAB"),
            ("SERUM", "SERUM")
        ]
    )


