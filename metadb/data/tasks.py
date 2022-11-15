from django.utils import timezone
from data.models import Mpx, Signal
from celery import shared_task
from .serializers import MpxSerializer, PhaMpxSerializer
from cursor_pagination import CursorPaginator
import csv
import os


# from utils.stats import calculate_fasta_stats
# from data.models import FastaStatistics, Pathogen


# @shared_task
# def generate_fasta_statistics(cid, fasta_path):
#     fasta_data = calculate_fasta_stats(fasta_path)
#     metadata = Pathogen.objects.get(cid=cid)
#     fasta = FastaStatistics.objects.create(metadata=metadata, **fasta_data)
#     metadata.fasta_statistics = True
#     metadata.save(update_fields=["fasta_statistics"])


# @shared_task
# def generate_bam_statistics(cid, bam_path):
#     bam_data = calculate_fasta_stats(bam_path)
#     metadata = Pathogen.objects.get(cid=cid)
#     bam = BamStatistics.objects.create(metadata=metadata, **bam_data)
#     metadata.bam_statistics = True
#     metadata.save(update_fields=["bam_statistics"])


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
def create_mpx_tables():
    signal, created = Signal.objects.get_or_create(code="mpx")

    if (not created) and (
        (timezone.now() - signal.modified).total_seconds()
        > int(os.environ["METADB_CELERY_BEAT_TIME"])
    ):
        print("no changes detected")
        return None

    print("changes detected")

    temp_mpx_file = f"{os.environ['METADB_MPX_TSV']}.temp"
    final_mpx_file = os.environ["METADB_MPX_TSV"]
    temp_pha_mpx_file = f"{os.environ['METADB_PHA_MPX_TSV']}.temp"
    final_pha_mpx_file = os.environ["METADB_PHA_MPX_TSV"]

    with open(temp_mpx_file, "w") as temp_mpx, open(
        temp_pha_mpx_file, "w"
    ) as temp_pha_mpx:
        mpx_writer = csv.DictWriter(
            temp_mpx,
            fieldnames=MpxSerializer.Meta.fields,
            delimiter="\t",
        )
        mpx_writer.writeheader()

        pha_mpx_writer = csv.DictWriter(
            temp_pha_mpx,
            fieldnames=PhaMpxSerializer.Meta.fields,
            delimiter="\t",
        )
        pha_mpx_writer.writeheader()

        cursor = None
        has_next = True
        while has_next:
            data = paginator(Mpx.objects.filter(suppressed=False), cursor=cursor)

            mpx_serialized = MpxSerializer(data["objects"], many=True).data
            mpx_writer.writerows(mpx_serialized)

            pha_mpx_serialized = PhaMpxSerializer(data["objects"], many=True).data
            pha_mpx_writer.writerows(pha_mpx_serialized)

            cursor = data["cursor"]
            has_next = data["has_next"]

    os.rename(temp_mpx_file, final_mpx_file)
    os.rename(temp_pha_mpx_file, final_pha_mpx_file)

    print("changes acted on successfully")
