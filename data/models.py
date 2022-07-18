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
        unique=True # Creates index for the field. 
                    # TODO: this could be removed, and with db_index=True, would go from 2*log(N) to log(N) complexity.
                    # but is that worth the loss of extra validation from unique=True?
    )
    pathogen_code = models.CharField(
        max_length=8,
        choices=[
            ("MPX", "MPX"),
            ("COVID", "COVID")
        ]
    )
    institute = models.CharField(max_length=10)
    sender_sample_id = models.CharField(max_length=24)
    run_name = models.CharField(max_length=96)
    fasta_path = models.CharField(max_length=200)
    bam_path = models.TextField(max_length=200)
    is_external = models.BooleanField()
    collection_date = YearMonthField()
    received_date = YearMonthField()
    published_date = models.DateField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)
    
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


