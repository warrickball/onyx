from django.db import models
from django.contrib.auth.models import Group
from django.contrib.contenttypes.models import ContentType
from accounts.models import Site, User
from utils.fields import LowerCharField, UpperCharField
from utils.choices import format_choices
from utils.constraints import unique_together
from simple_history.models import HistoricalRecords
from secrets import token_hex
import uuid


# TODO: Don't actually need half the stuff being recorded in Project and Scope models
class Project(models.Model):
    code = LowerCharField(max_length=50, unique=True)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    add_group = models.OneToOneField(
        Group,
        on_delete=models.CASCADE,
        related_name="%(app_label)s_%(class)s_add",
    )
    view_group = models.OneToOneField(
        Group,
        on_delete=models.CASCADE,
        related_name="%(app_label)s_%(class)s_view",
    )
    change_group = models.OneToOneField(
        Group,
        on_delete=models.CASCADE,
        related_name="%(app_label)s_%(class)s_change",
    )
    suppress_group = models.OneToOneField(
        Group,
        on_delete=models.CASCADE,
        related_name="%(app_label)s_%(class)s_suppress",
    )
    delete_group = models.OneToOneField(
        Group,
        on_delete=models.CASCADE,
        related_name="%(app_label)s_%(class)s_delete",
    )


class Scope(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    code = LowerCharField(max_length=50)
    action = LowerCharField(
        max_length=10,
        choices=format_choices(["add", "view", "change", "suppress", "delete"]),
    )
    group = models.OneToOneField(Group, on_delete=models.CASCADE)

    class Meta:
        constraints = [
            unique_together(
                model_name="scope",
                fields=["project", "code", "action"],
            ),
        ]


class Choice(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    field = models.TextField()
    choice = LowerCharField(max_length=100)
    is_active = models.BooleanField(default=True)

    class Meta:
        indexes = [
            models.Index(fields=["content_type", "field"]),
        ]
        constraints = [
            unique_together(
                model_name="choice",
                fields=["content_type", "field", "choice"],
            ),
        ]


def generate_cid():
    """
    Simple function that generates a random new CID.

    The CID consists of the prefix `C-` followed by 10 random hex digits.

    This means there are `16^10 = 1,099,511,627,776` CIDs to choose from.
    """
    cid = "C-" + "".join(token_hex(5).upper())

    if ProjectRecord.objects.filter(cid=cid).exists():
        cid = generate_cid()

    return cid


class BaseRecord(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    history = HistoricalRecords(inherit=True)
    created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    # site = models.ForeignKey(Site, to_field="code", on_delete=models.CASCADE)

    class Meta:
        default_permissions = []


class ProjectRecord(BaseRecord):
    cid = UpperCharField(default=generate_cid, max_length=12, unique=True)
    published_date = models.DateField(auto_now_add=True)
    suppressed = models.BooleanField(default=False)

    class Meta:
        default_permissions = []
        indexes = [
            models.Index(fields=["cid"]),
            models.Index(fields=["published_date"]),
            models.Index(fields=["suppressed"]),
        ]
