# `metadb`
```
$ metadb -h
usage: metadb [-h] [-u USER] [-p] [-v] {command} ...

positional arguments:
  {command}
    config              Config-specific commands.
    site                Site-specific commands.
    admin               Admin-specific commands.
    register            Register a new user.
    login               Log in to metadb.
    logout              Log out of metadb.
    logoutall           Log out of metadb on all devices.
    create              Upload metadata records.
    testcreate          Test uploading metadata records.
    get                 Get a metadata record.
    filter              Filter metadata records.
    update              Update metadata records.
    suppress            Suppress metadata records.
    delete              Delete metadata records.

options:
  -h, --help            show this help message and exit
  -u USER, --user USER  Which user to execute the command as.
  -p, --env-password    When a password is required, the client will use the env variable with format 'METADB_<USER>_PASSWORD'.
  -v, --version         Client version number.
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
    print(result) # This is a dictionary representing a record, not a response object
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
            "name4__range" : "value4, value5",
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
from metadb import Session, F

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
        query=(~F(sample_type="swab"))
        & (
            F(collection_month__range=["2022-02", "2022-03"])
            | F(collection_month__range=["2022-06", "2022-09"])
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
```python
from metadb import Session

with Session() as client:
    # Update from a csv of records
    responses = client.csv_update(
        "project",
        csv_path="/path/to/file.csv",
        # delimiter="\t", # For uploading from a tsv
    )

    # Iterating through the responses triggers the updates
    for response in responses:
        print(response)
```

## Suppress data
#### Suppress a single record
```
$ metadb suppress <project> <cid>
```
```python
from metadb import Session 

with Session() as client:
    result = client.suppress("project", "cid")
    print(result)
```

#### Suppress multiple records from a csv/tsv
```
$ metadb suppress <project> --csv <csv>
$ metadb suppress <project> --tsv <tsv>
```
```python
from metadb import Session

with Session() as client:
    # Suppress from a csv of records
    responses = client.csv_suppress(
        "project",
        csv_path="/path/to/file.csv",
        # delimiter="\t", # For uploading from a tsv
    )

    # Iterating through the responses triggers the suppressions
    for response in responses:
        print(response)
```

## Delete data
#### Delete a single record
```
$ metadb delete <project> <cid>
```
```python
from metadb import Session 

with Session() as client:
    result = client.delete("project", "cid")
    print(result)
```

#### Delete multiple records from a csv/tsv
```
$ metadb delete <project> --csv <csv>
$ metadb delete <project> --tsv <tsv>
```
```python
from metadb import Session

with Session() as client:
    # Delete from a csv of records
    responses = client.csv_delete(
        "project",
        csv_path="/path/to/file.csv",
        # delimiter="\t", # For uploading from a tsv
    )

    # Iterating through the responses triggers the deletions
    for response in responses:
        print(response)
```
