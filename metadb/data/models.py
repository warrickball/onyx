from django.db import models
from data.utils import generate_cid, YearMonthField
import data.config as config


class Uploader(models.Model):
    name = models.CharField(max_length=20, unique=True)
    code = models.CharField(max_length=8, unique=True)


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
        choices=config.PATHOGEN_CODES
    )
    uploader = models.CharField(max_length=8)
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
        choices=config.SEQ_PLATFORM_CHOICES
    )


class Covid(Pathogen):
    fasta_header = models.CharField(max_length=100)
    sample_type = models.CharField(
        max_length=50,
        choices=config.SAMPLE_TYPES
    )
