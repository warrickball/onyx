from django.db import models
from accounts.models import Site, User
from utils.fields import UpperCharField
from secrets import token_hex


def generate_cid():
    """
    Simple function that generates a random new CID.

    The CID consists of the prefix `C-` followed by 10 random hex digits.

    This means there are `16^10 = 1,099,511,627,776` CIDs to choose from.
    """
    cid = "C-" + "".join(token_hex(5).upper())

    if Record.objects.filter(cid=cid).exists():
        cid = generate_cid()

    return cid


class Record(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)
    suppressed = models.BooleanField(default=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    site = models.ForeignKey(Site, to_field="code", on_delete=models.CASCADE)
    cid = UpperCharField(default=generate_cid, max_length=12, unique=True)
    published_date = models.DateField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["site", "published_date"]),
            models.Index(fields=["site"]),
            models.Index(fields=["cid"]),
            models.Index(fields=["published_date"]),
        ]
        default_permissions = []

    class ExtraMeta:
        db_choice_fields = ["site"]
        optional_value_groups = []
        yearmonths = []
        yearmonth_orderings = []
        metrics = []
