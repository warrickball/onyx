# `metadb`
```
$ metadb -h
usage: metadb [-h] [-v] {command} ...

positional arguments:
  {command}
    config       Config-specific commands.
    site         Site-specific commands.
    admin        Admin-specific commands.
    register     Register a new user in metadb.
    login        Log in to metadb.
    logout       Log out of metadb.
    logoutall    Log out of metadb everywhere.
    create       Upload metadata to metadb.
    get          Get metadata from metadb.
    update       Update metadata within metadb.
    suppress     Suppress metadata within metadb.
    delete       Delete metadata within metadb.

options:
  -h, --help     show this help message and exit
  -v, --version  Client version number.
```

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
$ metadb create <project> --csv <csv>
$ metadb create <project> --tsv <tsv>
```

## Retrieve data
```
$ metadb get <project> <cid>
$ metadb get <project> --field <name> <value> --field <name> <value> ...
```

#### Supported lookups

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
$ metadb update <project> --csv <csv>
$ metadb update <project> --tsv <tsv>
```

## Suppress data
```
$ metadb suppress <project> <cid>
$ metadb suppress <project> --csv <csv>
$ metadb suppress <project> --tsv <tsv>
```

## Delete data
```
$ metadb delete <project> <cid>
$ metadb delete <project> --csv <csv>
$ metadb delete <project> --tsv <tsv>
```
