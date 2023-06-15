from django.db import models
from django.contrib.auth.models import Group
from django.contrib.contenttypes.models import ContentType
from accounts.models import Site, User
from utils.fields import LowerCharField, UpperCharField
from utils.choices import format_choices
from utils.constraints import unique_together
from secrets import token_hex


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


class Signal(models.Model):
    code = LowerCharField(max_length=8, unique=True)
    modified = models.DateTimeField(auto_now=True)


class Choice(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    field = models.TextField()
    choice = LowerCharField(max_length=100)

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

    if Record.objects.filter(cid=cid).exists():
        cid = generate_cid()

    return cid


# TODO: Move some things into here?
class AbstractRecord(models.Model):
    class Meta:
        abstract = True


# TODO: Extend this class to have a ProjectRecord, where you store the cid?
# And make it so that ALL tables inherit from a different record table?
class Record(AbstractRecord):
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


# TODO: How best to track changes to any inherited models?
class RecordHistory(models.Model):
    record = models.ForeignKey(Record, on_delete=models.SET_NULL, null=True)
    cid = UpperCharField(max_length=12)
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    action = LowerCharField(
        max_length=10, choices=format_choices(["add", "change", "suppress", "delete"])
    )
    taken = models.DateTimeField(auto_now_add=True)
    changes = models.TextField(null=True)

    class Meta:
        indexes = [
            models.Index(fields=["record", "user"]),
            models.Index(fields=["record"]),
            models.Index(fields=["user"]),
        ]
