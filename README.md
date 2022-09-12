# `metadb`

## Setup & registration
```
$ metadbclient make-config
```

```
$ metadbclient register
```

## Uploading data

```
$ metadbclient create <PATHOGEN_CODE> --tsv <TSV_FILE>
$ metadbclient create <PATHOGEN_CODE> --csv <CSV_FILE>
$ metadbclient create <PATHOGEN_CODE> --field <FIELD> --field <FIELD> <VALUE> ...
```

## Filtering data

```
$ metadbclient get <PATHOGEN_CODE> --field <FIELD> <VALUE> --field <FIELD> <VALUE> ...
$ metadbclient get <PATHOGEN_CODE> <CID> --field <FIELD> <VALUE> --field <FIELD> <VALUE> ...
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
$ metadbclient get covid --field cid C-123456
$ metadbclient get covid --field sample_type__in SWAB,SERUM
$ metadbclient get covid --field collection_month__range 2022-03,2022-07
$ metadbclient get covid --field received_month__isnull true
$ metadbclient get covid --field published_date__iso_week__range 33,37 --field published_date__iso_year 2022
```

## Updating data
```
$ metadbclient update <PATHOGEN_CODE> <CID> --field <FIELD> <VALUE> --field <FIELD> <VALUE> ...
```

## Suppressing data
```
$ metadbclient suppress <PATHOGEN_CODE> <CID>
```
