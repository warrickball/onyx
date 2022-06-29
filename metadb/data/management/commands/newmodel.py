from django.core.management import base
import data.models as data_models


class Command(base.BaseCommand):
    help = "Create a new table in the database."
    fields = {
        "int" : "models.IntegerField",
        "bool" : "models.BooleanField",
        "chars" : "models.CharField",
        "text" : "models.TextField",
        "date" : "models.DateField",
        "datetime" : "models.DateTimeField",
    }

    def add_arguments(self, parser):
        parser.add_argument("table_name")
        for field in self.fields:
            parser.add_argument(f"--{field}", default=None, nargs=2, metavar=("NAME", "KWARGS"))

    def handle(self, *args, **options):
        with open(data_models.__file__, "a") as tables:
            tables.write(f"\n\n\nclass {options['table_name'].upper()}(BaseTable):")
            
            for field, field_class in self.fields.items():
                if options[field] is not None:
                    name, kwargs = options[field]
                    tables.write(f"\n{' ' * 4}{name} = {field_class}(**{kwargs})")
