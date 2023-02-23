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
$ metadb create <project> --field <name> <value> --field <name> <value> ...
$ metadb csv-create <project> <csv>
$ metadb tsv-create <project> <tsv>
```

## Retrieve data
```
$ metadb get <project> <cid>
$ metadb get <project> --field <name> <value> --field <name> <value> ...
```

#### Table of lookups

| Lookup            | Numeric | Text | Date (YYYY-MM-DD) | Date (YYYY-MM) | True/False |
| ----------------- | :-----: | :--: | :---------------: | :------------: | :--------: |
| `exact`           | ✓       | ✓    | ✓                 | ✓              | ✓          |
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
| `year`            |         |      | ✓                 | ✓              |            |
| `year__in`        |         |      | ✓                 | ✓              |            |
| `year__range`     |         |      | ✓                 | ✓              |            |
| `iso_year`        |         |      | ✓                 |                |            |
| `iso_year__in`    |         |      | ✓                 |                |            |
| `iso_year__range` |         |      | ✓                 |                |            |
| `iso_week`        |         |      | ✓                 |                |            |
| `iso_week__in`    |         |      | ✓                 |                |            |
| `iso_week__range` |         |      | ✓                 |                |            |

#### Examples
```
$ metadb get mpx C-123456
$ metadb get mpx --field sample_type__in swab,serum
$ metadb get mpx --field collection_month__range 2022-03,2022-07
$ metadb get mpx --field received_month__isnull true
$ metadb get mpx --field published_date__iso_week__range 33,37 --field published_date__iso_year 2022
```

## Update data
```
$ metadb update <project> <cid> --field <name> <value> --field <name> <value> ...
$ metadb csv-update <project> <CSV>
$ metadb tsv-update <project> <TSV>
```

## Suppress data
```
$ metadb suppress <project> <cid>
$ metadb csv-suppress <project> <CSV>
$ metadb tsv-suppress <project> <TSV>
```
