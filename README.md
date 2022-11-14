# `metadb`

## Create a config
```
$ metadb config create
```
## Register a user
```
$ metadb register
```

## Upload data

```
$ metadb create <PATHOGEN_CODE> --field <FIELD> <VALUE> --field <FIELD> <VALUE> ...
$ metadb csv-create <PATHOGEN_CODE> <CSV_FILE>
$ metadb tsv-create <PATHOGEN_CODE> <TSV_FILE>
```

## Get data

```
$ metadb get <PATHOGEN_CODE> --field <FIELD> <VALUE> --field <FIELD> <VALUE> ...
$ metadb get <PATHOGEN_CODE> <CID> --field <FIELD> <VALUE> --field <FIELD> <VALUE> ...
```

### Table of lookups

| Lookup            | Numeric | Text | Date (YYYY-MM-DD) | Date (YYYY-MM) | True/False |
| ----------------- | :-----: | :--: | :---------------: | :------------: | :--------: |
| `ne`              | ✓       | ✓    | ✓                 | ✓              | ✓          |
| `lt`              | ✓       | ✓    | ✓                 | ✓              | ✓          |
| `lte`             | ✓       | ✓    | ✓                 | ✓              | ✓          |
| `gt`              | ✓       | ✓    | ✓                 | ✓              | ✓          |
| `gte`             | ✓       | ✓    | ✓                 | ✓              | ✓          |
| `in`              | ✓       | ✓    | ✓                 | ✓              | ✓          |
| `notin`           | ✓       | ✓    | ✓                 | ✓              | ✓          |
| `range`           | ✓       | ✓    | ✓                 | ✓              | ✓          |
| `isnull`          | ✓       | ✓    | ✓                 | ✓              | ✓          |
| `contains`        |         | ✓    |                   |                |            |
| `startswith`      |         | ✓    |                   |                |            | 
| `endswith`        |         | ✓    |                   |                |            | 
| `iexact`          |         | ✓    |                   |                |            |  
| `icontains`       |         | ✓    |                   |                |            | 
| `istartswith`     |         | ✓    |                   |                |            | 
| `iendswith`       |         | ✓    |                   |                |            | 
| `regex`           |         | ✓    |                   |                |            | 
| `iregex`          |         | ✓    |                   |                |            | 
| `iso_year`        |         |      | ✓                 | ✓              |            |
| `iso_year__in`    |         |      | ✓                 | ✓              |            |
| `iso_year__range` |         |      | ✓                 | ✓              |            |
| `iso_week`        |         |      | ✓                 |                |            |
| `iso_week__in`    |         |      | ✓                 |                |            |
| `iso_week__range` |         |      | ✓                 |                |            |

### Examples

```
$ metadb get mpx C-123456
$ metadb get mpx --field sample_type__in SWAB,SERUM
$ metadb get mpx --field collection_month__range 2022-03,2022-07
$ metadb get mpx --field received_month__isnull true
$ metadb get mpx --field published_date__iso_week__range 33,37 --field published_date__iso_year 2022
```

## Update data
```
$ metadb update <PATHOGEN_CODE> <CID> --field <FIELD> <VALUE> --field <FIELD> <VALUE> ...
$ metadb csv-update <PATHOGEN_CODE> <CSV>
$ metadb tsv-update <PATHOGEN_CODE> <TSV>
```

## Suppress data
```
$ metadb suppress <PATHOGEN_CODE> <CID>
$ metadb csv-suppress <PATHOGEN_CODE> <CSV>
$ metadb tsv-suppress <PATHOGEN_CODE> <TSV>
```
