from django.db import models
from django.db.models.lookups import BuiltinLookup
from django.db.models.fields.related_lookups import RelatedLookupMixin
from accounts.models import User


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
        # TODO: Understand why did I do this ?? With 0 and 1?
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


class Request(models.Model):
    endpoint = models.CharField(max_length=100, blank=True)
    method = models.CharField(max_length=10, blank=True)
    status = models.PositiveSmallIntegerField()
    user = models.ForeignKey(User, on_delete=models.PROTECT, null=True)
    address = models.CharField(max_length=20, blank=True)
    exec_time = models.IntegerField(null=True)
    date = models.DateTimeField(auto_now=True)
    error_messages = models.TextField(blank=True)
