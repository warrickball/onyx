from django.db import models
from django.db.models import Field
from django.db.models.lookups import BuiltinLookup
from django.contrib.auth.models import Group
from django.contrib.contenttypes.models import ContentType
from accounts.models import User
from utils.fields import LowerCharField


@Field.register_lookup
class NotEqual(models.Lookup):
    lookup_name = "ne"

    def as_sql(self, compiler, connection):
        lhs, lhs_params = self.process_lhs(compiler, connection)
        rhs, rhs_params = self.process_rhs(compiler, connection)
        params = lhs_params + rhs_params
        return "%s <> %s" % (lhs, rhs), params


@Field.register_lookup
class IsNull(BuiltinLookup):
    lookup_name = "isnull"
    prepare_rhs = False

    def as_sql(self, compiler, connection):
        if str(self.rhs) in ["0", "false", "False"]:
            self.rhs = False

        elif str(self.rhs) in ["1", "false", "False"]:
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


class Signal(models.Model):
    code = LowerCharField(max_length=8, unique=True)
    modified = models.DateTimeField(auto_now=True)


class GroupCluster(models.Model):
    name = models.TextField(unique=True)
    groups = models.ManyToManyField(Group)


class GroupToContentType(models.Model):
    group = models.OneToOneField(Group, on_delete=models.CASCADE)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)


class Request(models.Model):
    endpoint = models.CharField(max_length=100, null=True)
    method = models.CharField(max_length=10, null=True)
    status = models.PositiveSmallIntegerField()
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    address = models.CharField(max_length=20, null=True)
    exec_time = models.IntegerField(null=True)
    date = models.DateTimeField(auto_now=True)
