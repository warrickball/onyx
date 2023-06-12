# from django.utils import timezone
# from data.models.projects import Mpx
# from data.models import Signal
# from utils.project import (
#     get_project_and_model,
# )
# from celery import shared_task
# from .serializers import MpxSerializer
# from cursor_pagination import CursorPaginator
# import csv
# import os


# def get_fields_from_permissions(permissions):
#     return [
#         field
#         for (_, _, field) in (
#             x.partition("__") for x in permissions.values_list("codename", flat=True)
#         )
#         if field
#     ]


# def paginator(qs, cursor=None, page_size=5000):
#     paginator = CursorPaginator(qs, ordering=("-created", "-id"))
#     page = paginator.page(first=page_size, after=cursor)
#     data = {
#         "objects": page.items,
#         "has_next": page.has_next,
#         "cursor": paginator.cursor(page[-1]),
#     }
#     return data


# @shared_task
# def create_mpx_tables():
#     signal, created = Signal.objects.get_or_create(code="mpx")

#     if (not created) and (
#         (timezone.now() - signal.modified).total_seconds()
#         > 60 * int(os.environ["ONYX_CELERY_BEAT_TIME"])
#     ):
#         print("no changes detected")
#         return None

#     print("changes detected")

#     temp_mpx_file = f"{os.environ['ONYX_MPX_TSV']}.temp"
#     final_mpx_file = os.environ["ONYX_MPX_TSV"]
#     temp_pha_mpx_file = f"{os.environ['ONYX_PHA_MPX_TSV']}.temp"
#     final_pha_mpx_file = os.environ["ONYX_PHA_MPX_TSV"]

#     mpx_project, _ = get_project_and_model("mpx")
#     mpx_view_fields = get_fields_from_permissions(
#         mpx_project.view_group.permissions.all()  # type: ignore
#     )

#     mpxpha_project, _ = get_project_and_model("mpxpha")
#     mpxpha_view_fields = get_fields_from_permissions(
#         mpxpha_project.view_group.permissions.all()  # type: ignore
#     )

#     with open(temp_mpx_file, "w") as temp_mpx, open(
#         temp_pha_mpx_file, "w"
#     ) as temp_pha_mpx:
#         mpx_writer = csv.DictWriter(
#             temp_mpx,
#             fieldnames=mpx_view_fields,
#             delimiter="\t",
#         )
#         mpx_writer.writeheader()

#         pha_mpx_writer = csv.DictWriter(
#             temp_pha_mpx,
#             fieldnames=mpxpha_view_fields,
#             delimiter="\t",
#         )
#         pha_mpx_writer.writeheader()

#         cursor = None
#         has_next = True
#         while has_next:
#             data = paginator(Mpx.objects.filter(suppressed=False), cursor=cursor)

#             mpx_serialized = MpxSerializer(
#                 data["objects"],
#                 many=True,
#                 fields=mpx_view_fields,
#             ).data
#             mpx_writer.writerows(mpx_serialized)

#             pha_mpx_serialized = MpxSerializer(
#                 data["objects"],
#                 many=True,
#                 fields=mpxpha_view_fields,
#             ).data
#             pha_mpx_writer.writerows(pha_mpx_serialized)

#             cursor = data["cursor"]
#             has_next = data["has_next"]

#     os.rename(temp_mpx_file, final_mpx_file)
#     os.rename(temp_pha_mpx_file, final_pha_mpx_file)

#     print("changes acted on successfully")
