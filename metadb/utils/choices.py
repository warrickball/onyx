SAMPLE_TYPE_CHOICES = ["swab", "serum"]
SEQ_PLATFORM_CHOICES = [
    "illumina",
    "oxford_nanopore",
    "pacific_biosciences",
    "ion_torrent",
]
ENRICHMENT_METHOD_CHOICES = [
    "other",
    "pcr",
    "random",
    "random_pcr",
    "none",
]
SEQ_STRATEGY_CHOICES = [
    "amplicon",
    "other",
    "targeted_capture",
    "wga",
    "wgs",
]
SOURCE_OF_LIBRARY_CHOICES = [
    "genomic",
    "metagenomic",
    "metatranscriptomic",
    "other",
    "transcriptomic",
    "viral_rna",
]
COUNTRY_CHOICES = [
    "eng",
    "wales",
    "scot",
    "ni",
]
RUN_LAYOUT_CHOICES = ["single", "paired"]
PATIENT_AGEBAND_CHOICES = [
    "0-5",
    "6-10",
    "11-15",
    "16-20",
    "21-25",
    "26-30",
    "31-35",
    "36-40",
    "41-45",
    "46-50",
    "51-55",
    "56-60",
    "61-65",
    "66-70",
    "71-75",
    "76-80",
    "81-85",
    "86-90",
    "91-95",
    "96-100",
    "100+",
]
SAMPLE_SITE_CHOICES = ["sore", "genital"]
UKHSA_REGION_CHOICES = ["ne"]
TRAVEL_STATUS_CHOICES = ["yes", "no"]
