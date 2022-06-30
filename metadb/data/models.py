from django.db import models


mpx = "MPX"
covid = "COVID"
organism_choices = [
    (mpx, "MPX"),
    (covid, "COVID")
]

swab = "SWAB"
serum = "SERUM"
sample_type_choices = [
    (swab, "SWAB"),
    (serum, "SERUM")
]

targeted = "TARGETED"
metagenomic = "METAGENOMIC"
seq_approach_choices = [
    (targeted, "TARGETED"),
    (metagenomic, "METAGENOMIC")
]

amplicon = "AMPLICON"
wgs = "WGS"
wga = "WGA"
targeted_capture = "TARGETED_CAPTURE"
other = "OTHER"
seq_strategy_choices = [
    (amplicon, "AMPLICON"),
    (wgs, "WGS"),
    (targeted_capture, "TARGETED_CAPTURE"),
    (other, "OTHER")
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


class Organism(models.Model):
    cid = models.CharField(max_length=100, unique=True)
    organism = models.CharField(
        max_length=100,
        choices=organism_choices
    )
    uploader = models.CharField(max_length=8)
    sender_sample_id = models.CharField(max_length=16)
    run_name = models.CharField(max_length=100)
    fasta_path = models.CharField(max_length=500)
    bam_path = models.TextField(max_length=500)
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


class MPX(Organism):
    fasta_header = models.CharField(max_length=100)
    sample_type = models.CharField(
        max_length=100,
        choices=sample_type_choices
    )
    seq_approach = models.CharField(
        max_length=100,
        choices=seq_approach_choices
    )
    seq_strategy = models.CharField(
        max_length=100,
        choices=seq_strategy_choices
    )
    seq_platform = models.CharField(
        max_length=100,
        choices=seq_platform_choices
    )


class COVID(Organism):
    fasta_header = models.CharField(max_length=100)
    sample_type = models.CharField(
        max_length=100,
        choices=sample_type_choices
    )
