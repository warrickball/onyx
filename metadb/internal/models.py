from django.db import models
from django.db.models.lookups import BuiltinLookup
from django.db.models.fields.related_lookups import RelatedLookupMixin
from django.contrib.auth.models import Group
from django.contrib.contenttypes.models import ContentType
from accounts.models import User
from utils.fields import LowerCharField


class NotEqual(models.Lookup):
    lookup_name = "ne"

    def as_sql(self, compiler, connection):
        lhs, lhs_params = self.process_lhs(compiler, connection)
        rhs, rhs_params = self.process_rhs(compiler, connection)
        params = lhs_params + rhs_params
        return "%s <> %s" % (lhs, rhs), params


class NotEqualRelated(RelatedLookupMixin, NotEqual):
    pass


class IsNull(BuiltinLookup):
    lookup_name = "isnull"
    prepare_rhs = False

    def as_sql(self, compiler, connection):
        if str(self.rhs).lower() in ["0", "false"]:
            self.rhs = False

        elif str(self.rhs).lower() in ["1", "true"]:
            self.rhs = True

        if not isinstance(self.rhs, bool):
            raise ValueError(
                "The QuerySet value for an isnull lookup must be True or False."
            )

        sql, params = compiler.compile(self.lhs)
        if self.rhs:
            return "%s IS NULL" % sql, params
        else:
            return "%s IS NOT NULL" % sql, params


class IsNullRelated(RelatedLookupMixin, IsNull):
    pass


class Signal(models.Model):
    code = LowerCharField(max_length=8, unique=True)
    modified = models.DateTimeField(auto_now=True)


class Project(models.Model):
    code = LowerCharField(max_length=50, unique=True)
    hidden = models.BooleanField(default=False)
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


class Request(models.Model):
    endpoint = models.CharField(max_length=100, null=True)
    method = models.CharField(max_length=10, null=True)
    status = models.PositiveSmallIntegerField()
    user = models.ForeignKey(User, on_delete=models.PROTECT, null=True)
    address = models.CharField(max_length=20, null=True)
    exec_time = models.IntegerField(null=True)
    date = models.DateTimeField(auto_now=True)


class History(models.Model):
    record = models.ForeignKey("data.Record", on_delete=models.SET_NULL, null=True)
    cid = models.CharField(max_length=12)
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    action = LowerCharField(
        max_length=10,
        choices=[
            ("add", "add"),
            ("change", "change"),
            ("suppress", "suppress"),
            ("delete", "delete"),
        ],
    )
    taken = models.DateTimeField(auto_now_add=True)
    changes = models.TextField(null=True)

    class Meta:
        indexes = [
            models.Index(fields=["record", "user"]),
            models.Index(fields=["record"]),
            models.Index(fields=["user"]),
        ]


class Choice(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    field = models.TextField()
    choice = LowerCharField(max_length=100)

    class Meta:
        unique_together = ["content_type", "field", "choice"]
        indexes = [
            models.Index(fields=["content_type", "field", "choice"]),
            models.Index(fields=["content_type"]),
            models.Index(fields=["field"]),
            models.Index(fields=["choice"]),
        ]
