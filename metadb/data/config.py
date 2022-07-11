# TODO: Should these all be stored in the database

PATHOGEN_CODES = [
    ("PATHOGEN", "PATHOGEN"), # Used for testing. TODO: This probably shouldn't be here
    ("MPX", "MPX"),
    ("COVID", "COVID")
]

SAMPLE_TYPES = [
    ("SWAB", "SWAB"),
    ("SERUM", "SERUM")
]

SEQ_PLATFORM_CHOICES = [
    ("ILLUMINA", "ILLUMINA"),
    ("OXFORD_NANOPORE", "OXFORD_NANOPORE"),
    ("PACIFIC_BIOSCIENCES", "PACIFIC_BIOSCIENCES"),
    ("ION_TORRENT", "ION_TORRENT")
]
