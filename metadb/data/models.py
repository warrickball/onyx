from django.db import models
from django.utils.dateparse import parse_date
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from datetime import date, datetime
from secrets import token_hex
from . import config


# TODO: Improve and test
class YearMonthField(models.DateField):
    '''
    Minimal override of DateField to support YYYY-MM format.
    '''
    default_error_messages = {
        "invalid": _(
            "“%(value)s” value has an invalid date format. It must be "
            "in YYYY-MM format."
        ),
        "invalid_date": _(
            "“%(value)s” value has the correct format (YYYY-MM) "
            "but it is an invalid date."
        ),
    }
    description = _("Date (without time OR day)")

    def to_python(self, value):
        if value is None:
            return value

        if isinstance(value, date):
            return value

        if isinstance(value, datetime):
            return value.date()

        if isinstance(value, str):
            try:
                parsed = parse_date(value + "-01")
                if parsed is not None:
                    return parsed
            except ValueError:
                raise ValidationError(
                    self.error_messages["invalid_date"],
                    code="invalid_date",
                    params={"value": value},
                )
        raise ValidationError(
            self.error_messages["invalid"],
            code="invalid",
            params={"value": value},
        )     


def generate_cid():
    cid = "C-" + "".join(token_hex(3).upper())
    if Pathogen.objects.filter(cid=cid).exists():
        cid = generate_cid()
    return cid


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
