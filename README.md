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
#### Create a single record from name/value pairs
```
$ metadb create <project> --field <name> <value> --field <name> <value> ...
```
```python
from metadb import Session

with Session() as client:
    # Create a single record
    response = client.create(
        "project",
        fields={
            "name1": "value1",
            "name2": "value2",
            # ...
        },
    )

    # Print the response
    print(response)
```

#### Create multiple records from a csv/tsv
```
$ metadb create <project> --csv <csv>
$ metadb create <project> --tsv <tsv>
```
```python
from metadb import Session

with Session() as client:
    # Create from a csv of records
    responses = client.csv_create(
        "project",
        csv_path="/path/to/file.csv",
        # delimiter="\t", # For uploading from a tsv
    )

    # Iterating through the responses triggers the uploads
    for response in responses:
        print(response)
```

## Retrieve data
#### The `get` endpoint
```
$ metadb get <project> <cid>
```
```python
from metadb import Session 

with Session() as client:
    result = client.get("project", "cid")

    # Display the result
    # This is a dictionary representing a record, not a response object
    print(result)
```

#### The `filter` endpoint
```
$ metadb filter <project> --field <name> <value> --field <name> <value> ...
```
```python
from metadb import Session

# Retrieve all results matching ALL of the field requirements
with Session() as client:
    results = client.filter(
        "project",
        fields={
            "name1" : "value1",
            "name2" : "value2",
            "name3__startswith" : "value3",
            "name4__range" : ["value4", "value5"],
            # ...
        }
    )

    # Display the results
    # These are dictionaries representing records, not response objects
    for result in results:
        print(result)
```

#### The `query` endpoint 
```python
from metadb import Session, Field

with Session() as client:
    # The python bitwise operators can be used in a query.
    # These are:
    # AND: &
    # OR:  |
    # XOR: ^
    # NOT: ~

    # Example query:
    # This query is asking for all records that:
    # Do NOT have a sample_type of 'swab', AND:
    # - Have a collection_month between Feb-Mar 2022
    # - OR have a collection_month between Jun-Sept 2022
    results = client.query(
        "project",
        query=(~Field(sample_type="swab"))
        & (
            Field(collection_month__range=["2022-02", "2022-03"])
            | Field(collection_month__range=["2022-06", "2022-09"])
        ),
    )

    # Display the results
    # These are dictionaries representing records, not response objects
    for result in results:
        print(result)
```

#### Supported lookups for `filter` and `query`
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

Most of these lookups (excluding `ne`, which is a custom lookup meaning `not equal`) correspond directly to Django's built-in 'field lookups'. More information on what each lookup means can be found at: https://docs.djangoproject.com/en/4.1/ref/models/querysets/#field-lookups

## Update data
#### Update a single record from name/value pairs
```
$ metadb update <project> <cid> --field <name> <value> --field <name> <value> ...
```
```python
from metadb import Session

with Session() as client:
    response = client.update(
        "project",
        "cid",
        fields={
            "name1" : "value1",
            "name2" : "value2",
            # ...
        }
    )

    # Print the response
    print(response)
```

#### Update multiple records from a csv/tsv
```
$ metadb update <project> --csv <csv>
$ metadb update <project> --tsv <tsv>
```

## Suppress data
#### Suppress a single record
```
$ metadb suppress <project> <cid>
```

#### Suppress multiple records from a csv/tsv
```
$ metadb suppress <project> --csv <csv>
$ metadb suppress <project> --tsv <tsv>
```

## Delete data
#### Delete a single record
```
$ metadb delete <project> <cid>
```

#### Delete multiple records from a csv/tsv
```
$ metadb delete <project> --csv <csv>
$ metadb delete <project> --tsv <tsv>
```
