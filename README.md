# `metadb`

## Setup & registration
```
$ metadbclient make-config
```

```
$ metadbclient register
```

## Filtering

```
$ metadbclient get <PATHOGEN_CODE> --field <FIELD> <VALUE> --field <FIELD> <VALUE> ...
```

### Table of lookups

| Lookup            | Numeric | Text | Date (YYYY-MM-DD) | Date (YYYY-MM) | True/False |
| ----------------- | :-----: | :--: | :---------------: | :------------: | :--------: |
| `ne`              | x       | x    | x                 | x              | x          |
| `lt`              | x       | x    | x                 | x              | x          |
| `lte`             | x       | x    | x                 | x              | x          |
| `gt`              | x       | x    | x                 | x              | x          |
| `gte`             | x       | x    | x                 | x              | x          |
| `in`              | x       | x    | x                 | x              | x          |
| `range`           | x       | x    | x                 | x              | x          |
| `isnull`          | x       | x    | x                 | x              | x          |
| `contains`        |         | x    |                   |                |            |
| `startswith`      |         | x    |                   |                |            | 
| `endswith`        |         | x    |                   |                |            | 
| `iexact`          |         | x    |                   |                |            |  
| `icontains`       |         | x    |                   |                |            | 
| `istartswith`     |         | x    |                   |                |            | 
| `iendswith`       |         | x    |                   |                |            | 
| `regex`           |         | x    |                   |                |            | 
| `iregex`          |         | x    |                   |                |            | 
| `iso_year`        |         |      | x                 | x              |            |
| `iso_year__in`    |         |      | x                 | x              |            |
| `iso_year__range` |         |      | x                 | x              |            |
| `iso_week`        |         |      | x                 |                |            |
| `iso_week__in`    |         |      | x                 |                |            |
| `iso_week__range` |         |      | x                 |                |            |

### Examples

```
$ metadbclient get covid --field cid C-123456
$ metadbclient get covid --field sample_type__in SWAB,SERUM
$ metadbclient get covid --field collection_month__range 2022-03,2022-07
$ metadbclient get covid --field received_month__isnull true
$ metadbclient get covid --field published_date__iso_week__range 33,37 --field published_date__iso_year 2022
```
