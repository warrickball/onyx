from django.db import models
from accounts.models import User


@models.Field.register_lookup
class NotEqual(models.Lookup):
    lookup_name = "ne"

    def as_sql(self, compiler, connection):
        lhs, lhs_params = self.process_lhs(compiler, connection)
        rhs, rhs_params = self.process_rhs(compiler, connection)
        params = lhs_params + rhs_params
        return "%s <> %s" % (lhs, rhs), params


# Credit to tuatara for this lookup
# https://gist.github.com/tuatara/6188a4c7bacab1f52c80
@models.CharField.register_lookup
@models.TextField.register_lookup
class LengthLookup(models.Transform):
    lookup_name = "length"

    def as_sql(self, compiler, connection):
        lhs, params = compiler.compile(self.lhs)
        return "CHAR_LENGTH(%s)" % lhs, params

    # SQLite doesn't implement CHAR_LENGTH, but its implementation of LENGTH conforms
    # with standard SQL CHAR_LENGTH (i.e. number of chars, not number of bytes)
    def as_sqlite(self, compiler, connection):
        lhs, params = compiler.compile(self.lhs)
        return "LENGTH(%s)" % lhs, params

    @property
    def output_field(self):
        return models.IntegerField()


class Request(models.Model):
    endpoint = models.CharField(max_length=100, blank=True)
    method = models.CharField(max_length=10, blank=True)
    status = models.PositiveSmallIntegerField()
    user = models.ForeignKey(User, on_delete=models.PROTECT, null=True)
    address = models.CharField(max_length=20, blank=True)
    exec_time = models.IntegerField(null=True)
    date = models.DateTimeField(auto_now=True)
    error_messages = models.TextField(blank=True)
