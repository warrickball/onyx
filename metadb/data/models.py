from django.db import models
import secrets


pathogen_codes = [
    ("pathogen", "pathogen"), # Used for testing. TODO: This probably shouldn't be here
    ("mpx", "mpx"),
    ("covid", "covid")
]

uploaders = [
    ("BIRM", "BIRM")
]

sample_types = [
    ("SWAB", "SWAB"),
    ("SERUM", "SERUM")
]

seq_platform_choices = [
    ("ILLUMINA", "ILLUMINA"),
    ("OXFORD_NANOPORE", "OXFORD_NANOPORE"),
    ("PACIFIC_BIOSCIENCES", "PACIFIC_BIOSCIENCES"),
    ("ION_TORRENT", "ION_TORRENT")
]


def generate_cid():
    # cid = "CLIMB-" + "".join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))
    cid = "CLIMB-" + "".join(secrets.token_hex(3).upper())
    if Pathogen.objects.filter(cid=cid).exists():
        cid = generate_cid()
    return cid


class YearMonthField(models.DateField):
    pass # TODO


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
        choices=pathogen_codes
    )
    uploader = models.CharField(
        max_length=8,
        choices=uploaders,
    )
    sender_sample_id = models.CharField(max_length=24)
    run_name = models.CharField(max_length=96)
    fasta_path = models.CharField(max_length=200)
    bam_path = models.TextField(max_length=200)
    is_external = models.BooleanField()
    collection_date = models.DateField()
    received_date = models.DateField()
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
        choices=seq_platform_choices
    )


class Covid(Pathogen):
    fasta_header = models.CharField(max_length=100)
    sample_type = models.CharField(
        max_length=50,
        choices=sample_types
    )
