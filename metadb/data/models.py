from django.db import models
from utils.fields import YearMonthField
from secrets import token_hex
from utils.functions import get_field_values
from accounts.models import Institute
from django.db.models.fields.related import ForeignObjectRel
import accounts.models as acc_models
import sys, inspect


def generate_cid():
    cid = "C-" + "".join(token_hex(3).upper())
    if Pathogen.objects.filter(cid=cid).exists():
        cid = generate_cid()
    return cid


class FastaStats(models.Model):
    metadata = models.OneToOneField("data.Pathogen", on_delete=models.CASCADE, related_name="fasta")
    # TODO: fasta header ?
    num_seqs = models.IntegerField()
    num_bases = models.IntegerField()
    pc_acgt = models.FloatField()
    gc_content = models.FloatField()
    pc_masked = models.FloatField()
    pc_invalid = models.FloatField()
    pc_ambig = models.FloatField()
    pc_ambig_2 = models.FloatField()
    pc_ambig_3 = models.FloatField()
    longest_acgt = models.IntegerField()
    longest_masked = models.IntegerField()
    longest_invalid = models.IntegerField()
    longest_ambig = models.IntegerField()
    longest_gap = models.IntegerField()
    longest_ungap = models.IntegerField()


class BamStats(models.Model):
    metadata = models.OneToOneField("data.Pathogen", on_delete=models.CASCADE, related_name="bam")
    num_reads = models.IntegerField()
    pc_coverage = models.FloatField()
    mean_depth = models.FloatField()
    mean_entropy = models.FloatField()

    # num_pos = models.IntegerField()
    # mean_cov = models.FloatField()
    # pc_pos_cov_gte1 = models.FloatField()
    # pc_pos_cov_gte5 = models.FloatField()
    # pc_pos_cov_gte10 = models.FloatField()
    # pc_pos_cov_gte20 = models.FloatField()
    # pc_pos_cov_gte50 = models.FloatField()
    # pc_pos_cov_gte100 = models.FloatField()
    # pc_pos_cov_gte200 = models.FloatField()

    # TODO: would need library_primers for tiles
    # pc_tiles_medcov_gte1 = models.FloatField()
    # pc_tiles_medcov_gte5 = models.FloatField()
    # pc_tiles_medcov_gte10 = models.FloatField()
    # pc_tiles_medcov_gte20 = models.FloatField()
    # pc_tiles_medcov_gte50 = models.FloatField()
    # pc_tiles_medcov_gte100 = models.FloatField()
    # pc_tiles_medcov_gte200 = models.FloatField()
    # tile_n = models.IntegerField()
    # tile_vector = models.TextField()


class VAF(models.Model):
    bam_stats = models.ForeignKey("data.BamStats", on_delete=models.CASCADE, related_name="vafs")
    reference = models.CharField(max_length=100)
    position = models.IntegerField()
    depth = models.IntegerField()
    num_a = models.IntegerField()
    num_c = models.IntegerField()
    num_g = models.IntegerField()
    num_t = models.IntegerField()
    num_ds = models.IntegerField()


def project_models():
    data_models = inspect.getmembers(sys.modules[__name__], inspect.isclass)
    account_models = inspect.getmembers(acc_models, inspect.isclass)
    return [x[1] for x in data_models + account_models]


def get_structure(model, valid_models, graph, nodes, name=""):
    if not any([issubclass(mdl, model) for mdl, _ in nodes]) and model in valid_models:
        node = (model, name)
        graph[node] = {}
        nodes.add(node)
    else:
        return graph
    
    for field in model._meta.get_fields():
        if issubclass(type(field), ForeignObjectRel) or isinstance(field, models.ForeignKey):
            relation_model = field.related_model._meta.model
            get_structure(relation_model, valid_models, graph[node], nodes, name=field.name)
    return graph


def assemble_kwargs(kwargs, structure, prefix=""):
    for model, name in structure:
        if name:
            kwargs.append(f"{prefix}{name}")

        prefix_for_name = f"{prefix}{name + '__' if name else ''}"

        for field in model._meta.get_fields():
            if issubclass(type(field), ForeignObjectRel) or isinstance(field, models.ForeignKey):
                continue
            kwargs.append(f"{prefix_for_name}{field.name}")

        kwargs = assemble_kwargs(kwargs, structure[(model, name)], prefix=prefix_for_name)
    return kwargs


def get_nested_fields(cls):
    '''
    Collect every damn field that can be passed to the filter function
    '''
    structure = get_structure(cls, project_models(), {}, set())
    fields = assemble_kwargs([], structure)
    return fields


class Pathogen(models.Model):
    # Non-updatable fields
    cid = models.CharField(
        default=generate_cid,
        max_length=12, 
        unique=True
    )
    sender_sample_id = models.CharField(max_length=24)
    run_name = models.CharField(max_length=96)
    pathogen_code = models.CharField(
        max_length=8,
        choices=[
            ("PATHOGEN", "PATHOGEN"), # TODO: is only here for tests. Find way to make tests work without it
            ("MPX", "MPX"),
            ("COVID", "COVID")
        ]
    )
    institute = models.ForeignKey("accounts.Institute", on_delete=models.CASCADE)
    published_date = models.DateField(auto_now_add=True)
    created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)
    suppressed = models.BooleanField(default=False)

    # Updatable fields
    fasta_path = models.CharField(max_length=200)
    bam_path = models.TextField(max_length=200)
    is_external = models.BooleanField()

    # Optional fields
    collection_month = YearMonthField(null=True)
    received_month = YearMonthField(null=True)
    
    @classmethod
    def optional_value_groups(cls):
        return [
            ["collection_month", "received_month"]
        ]

    @classmethod
    def all_fields(cls, nested=True):
        '''
        All fields of the model
        '''
        if nested:
            fields = get_nested_fields(cls)
        else:
            fields = [f.name for f in cls._meta.get_fields()]
        return fields

    @classmethod
    def internal_fields(cls):
        '''
        Fields that cannot be user-submitted on creation of a model instance
        '''
        return {"id", "cid", "published_date", "created", "last_modified", "suppressed"}

    @classmethod
    def readonly_fields(cls):
        '''
        Fields that cannot be user-submitted on updating of a model instance
        '''
        return {"id", "cid", "sender_sample_id", "run_name", "pathogen_code", "institute", "published_date", "created", "last_modified", "suppressed"}
    
    @classmethod
    def excluded_fields(cls):
        '''
        Fields that are excluded when sending data to the client
        '''
        return ("id", "created", "last_modified", "suppressed")

    @classmethod
    def choice_fields(cls):
        '''
        Fields with restricted choice of input
        '''
        choice_fields = [f.name for f in cls._meta.get_fields() if hasattr(f, "choices") and f.choices is not None] # type: ignore
        print(choice_fields)
        # return {"pathogen_code", "institute"}
        return set(choice_fields)
        

    @classmethod
    def get_choices(cls, field):
        choices = cls._meta.get_field(field).choices  # type: ignore
        if choices:
            return [choice for choice, _ in choices]
        else:
            # Bit dodgy
            if hasattr(cls, f"get_{field}_choices"):
                return getattr(cls, f"get_{field}_choices")()
            else:
                return []

    @classmethod
    def get_institute_choices(cls):
        return get_field_values(Institute, "code")
    
    class Meta:
        unique_together = [
            "sender_sample_id", 
            "run_name",
            "pathogen_code"
        ]


class Mpx(Pathogen):
    fasta_header = models.CharField(max_length=100)
    seq_platform = models.CharField(
        max_length=50,
        choices=[
            ("ILLUMINA", "ILLUMINA"),
            ("OXFORD_NANOPORE", "OXFORD_NANOPORE"),
            ("PACIFIC_BIOSCIENCES", "PACIFIC_BIOSCIENCES"),
            ("ION_TORRENT", "ION_TORRENT")
        ]
    )

    @classmethod
    def choice_fields(cls):
        return super().choice_fields() | {"seq_platform"}


class Covid(Pathogen):
    fasta_header = models.CharField(max_length=100)
    sample_type = models.CharField(
        max_length=50,
        choices=[
            ("SWAB", "SWAB"),
            ("SERUM", "SERUM")
        ]
    )
    # TODO: attempt things like ct values

    @classmethod
    def choice_fields(cls):
        return super().choice_fields() | {"sample_type"}
