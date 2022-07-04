from django.db import models


mpx = "mpx"
covid = "covid"
pathogen_codes = [
    (mpx, "mpx"),
    (covid, "covid")
]

birm = "BIRM"
uploaders = [
    (birm, "BIRM")
]

swab = "SWAB"
serum = "SERUM"
sample_types = [
    (swab, "SWAB"),
    (serum, "SERUM")
]

illumina = "ILLUMINA"
oxford_nanopore = "OXFORD_NANOPORE"
pacific_biosciences = "PACIFIC_BIOSCIENCES"
ion_torrent = "ION_TORRENT"
seq_platform_choices = [
    (illumina, "ILLUMINA"),
    (oxford_nanopore, "OXFORD_NANOPORE"),
    (pacific_biosciences, "PACIFIC_BIOSCIENCES"),
    (ion_torrent, "ION_TORRENT")
]


class YearMonthField(models.DateField):
    pass # TODO


class Pathogen(models.Model):
    cid = models.CharField(
        max_length=128, 
        unique=True, 
        null=True
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
