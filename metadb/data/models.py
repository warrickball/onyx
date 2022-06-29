from django.db import models

# Create your models here.

class Base(models.Model):
    cid = models.CharField(max_length=100, unique=True)
    organism = models.CharField(max_length=100)
    uploader = models.CharField(max_length=8)
    sender_sample_id = models.CharField(max_length=16)
    run_name = models.CharField(max_length=100)
    collection_date = models.DateField()
    received_date = models.DateField()
    published_date = models.DateField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)
    is_external = models.BooleanField()
    fasta_path = models.CharField(max_length=500)
    bam_path = models.TextField(max_length=500)

    class Meta:
        unique_together = ["sender_sample_id", "run_name"]


class MPX(Base):
    fasta_header = models.CharField(max_length=100)
    sample_type = models.CharField(
        max_length=2,
        choices=(
            ("sb", "swab"),
            ("sm", "serum"),
        )
    )
    seq_approach = models.CharField(
        max_length=1,
        choices=(
            ("t", "targeted"),
            ("m", "metagenomic"),
        )
    )
    seq_strategy = models.CharField(
        max_length=2,
        choices=(
            ("am", "amplicon"),
            ("ws", "wgs"),
            ("wa", "wga"),
            ("tc", "targeted_capture"),
            ("ot", "other")
        )
    )
    seq_platform = models.CharField(
        max_length=2,
        choices=(
            ("il", "illumina"),
            ("on", "oxford_nanopore"),
            ("pb", "pacific_biosciences"),
            ("it", "ion_torrent")
        )
    )


class COVID(Base):
    pillar = models.IntegerField(
        choices=(
            (1, 1),
            (2, 2)
        )
    )