# from celery import shared_task
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
