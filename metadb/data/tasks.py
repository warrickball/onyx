from django.utils import timezone
from data.models import Mpx, Signal
from accounts.models import User
from celery import shared_task
from cursor_pagination import CursorPaginator
import csv
import os


# from utils.stats import calculate_bam_stats, calculate_fasta_stats
# from data.models import Pathogen, FastaStats, BamStats, VAF


# @shared_task
# def generate_stats(cid, fasta_path, bam_path):
#     fasta_data = calculate_fasta_stats(fasta_path)
#     bam_data = calculate_bam_stats(bam_path)
#     vafs = bam_data.pop("vafs")

#     instance = Pathogen.objects.get(cid=cid)
#     fasta = FastaStats.objects.create(metadata=instance, **fasta_data)
#     bam = BamStats.objects.create(metadata=instance, **bam_data)
#     for vaf in vafs:
#         VAF.objects.create(bam_stats=bam, **vaf)

#


def paginator(qs, cursor=None, page_size=5000):
    paginator = CursorPaginator(qs, ordering=("-created", "-id"))
    page = paginator.page(first=page_size, after=cursor)
    data = {
        "objects": page.items,
        "has_next": page.has_next,
        "cursor": paginator.cursor(page[-1]),
    }
    return data


@shared_task
def create_mpx_table():
    signal, created = Signal.objects.get_or_create(code="mpx")

    if (not created) or (
        (timezone.now() - signal.modified).total_seconds()
        > int(os.environ["METADB_CELERY_BEAT_TIME"])
    ):
        print("no changes detected")
        return None

    print("changes detected")

    user = User.objects.get(
        username="briert"
    )  # TODO: either remove username requirement or move to env var

    serializer = Mpx.get_serializer(user=user)

    temp_file = f"{os.environ['METADB_MPX_TSV']}.temp"
    final_file = os.environ["METADB_MPX_TSV"]

    with open(temp_file, "w") as temp:
        writer = csv.DictWriter(
            temp,
            fieldnames=serializer.Meta.fields,
            delimiter="\t",
        )
        writer.writeheader()

        cursor = None
        has_next = True
        while has_next:
            data = paginator(Mpx.objects.filter(suppressed=False), cursor=cursor)
            serialized = serializer(data["objects"], many=True).data

            writer.writerows(serialized)

            cursor = data["cursor"]
            has_next = data["has_next"]

    os.rename(temp_file, final_file)

    print("changes acted on successfully")
