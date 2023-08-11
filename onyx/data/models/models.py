import uuid
from secrets import token_hex
from django.db import models
from django.contrib.auth.models import Group
from django.contrib.contenttypes.models import ContentType
from accounts.models import Site, User
from utils.fields import LowerCharField, UpperCharField
from utils.choices import format_choices
from utils.constraints import unique_together
from simple_history.models import HistoricalRecords


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
    project = models.ForeignKey(Project, to_field="code", on_delete=models.CASCADE)
    field = models.TextField()
    choice = LowerCharField(max_length=100)
    is_active = models.BooleanField(default=True)
    constraints = models.ManyToManyField("Choice", related_name="reverse_constraints")

    class Meta:
        indexes = [
            models.Index(fields=["project", "field"]),
        ]
        constraints = [
            unique_together(
                model_name="choice",
                fields=["project", "field", "choice"],
            ),
        ]


# TODO: Separate dedicated system for country + county -> latitude/longitude?
# Where to store this?
# We also probably want a validate_country_county function
# Just needs to check these match correctly
# and then if they do, we can just add the corresponding latitude + longitude
class Country(models.Model):
    country = LowerCharField(max_length=100, unique=True)
    latitude = models.FloatField()  # str better?
    longitude = models.FloatField()


class County(models.Model):
    country = LowerCharField(max_length=100)
    county = LowerCharField(max_length=100)
    latitude = models.FloatField()
    longitude = models.FloatField()

    class Meta:
        constraints = [
            unique_together(
                model_name="county",
                fields=["country", "county"],
            ),
        ]


def generate_cid():
    """
    Simple function that generates a random new CID.

    The CID consists of the prefix `C-` followed by 10 random hex digits.

    This means there are `16^10 = 1,099,511,627,776` CIDs to choose from.
    """
    cid = "C-" + "".join(token_hex(5).upper())

    if CID.objects.filter(cid=cid).exists():
        cid = generate_cid()

    return cid


class CID(models.Model):
    cid = UpperCharField(default=generate_cid, max_length=12, unique=True)


class BaseRecord(models.Model):
    # TODO: Make uuid primary key?
    # Stop worrying about collisions. its not going to happen m8
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    history = HistoricalRecords(inherit=True)
    created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    # TODO: Display sites again
    # site = models.ForeignKey(Site, to_field="code", on_delete=models.CASCADE)

    class Meta:
        default_permissions = []
        abstract = True


class ProjectRecord(BaseRecord):
    cid = UpperCharField(max_length=12, unique=True)
    published_date = models.DateField(auto_now_add=True)
    suppressed = models.BooleanField(default=False)

    class Meta:
        default_permissions = []
        abstract = True
        indexes = [
            models.Index(fields=["published_date"]),
            models.Index(fields=["suppressed"]),
        ]

    def save(self, *args, **kwargs):
        if not self.pk:
            cid = CID.objects.create()
            self.cid = cid.cid

        super().save(*args, **kwargs)
