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
$ metadb create <PROJECT> --field <FIELD> <VALUE> --field <FIELD> <VALUE> ...
$ metadb csv-create <PROJECT> <CSV_FILE>
$ metadb tsv-create <PROJECT> <TSV_FILE>
```

## Get data

```
$ metadb get <PROJECT> --field <FIELD> <VALUE> --field <FIELD> <VALUE> ...
$ metadb get <PROJECT> <CID> --field <FIELD> <VALUE> --field <FIELD> <VALUE> ...
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
$ metadb update <PROJECT> <CID> --field <FIELD> <VALUE> --field <FIELD> <VALUE> ...
$ metadb csv-update <PROJECT> <CSV>
$ metadb tsv-update <PROJECT> <TSV>
```

## Suppress data
```
$ metadb suppress <PROJECT> <CID>
$ metadb csv-suppress <PROJECT> <CSV>
$ metadb tsv-suppress <PROJECT> <TSV>
```
