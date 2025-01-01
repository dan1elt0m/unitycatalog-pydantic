# Unity Catalog Pydantic 
[![CodeQL](https://github.com/dan1elt0m/unitycatalog-pydantic/actions/workflows/codeql-analysis.yml/badge.svg)](https://github.com/dan1elt0m/sadel/actions/workflows/codeql-analysis.yml)
[![test](https://github.com/dan1elt0m/unitycatalog-pydantic/actions/workflows/test.yml/badge.svg)](https://github.com/dan1elt0m/sadel/actions/workflows/test.yml)
![Python Version from PEP 621 TOML](https://img.shields.io/python/required-version-toml?tomlFilePath=https%3A%2F%2Fraw.githubusercontent.com%2Fdan1elt0m%2Funitycatalog-pydantic%2Fmain%2Fpyproject.toml)
[![codecov](https://codecov.io/github/dan1elt0m/dan1elt0m/graph/badge.svg?token=NECZRE656C)](https://codecov.io/github/dan1elt0m/unitycatalog-pydantic)


**Disclaimer: This project is unofficial and not affiliated with or endorsed by the official Unity Catalog team.**

Simplifies managing OSS Unity Catalog tables using Pydantic models.

## Installation
```bash
pip install unitycatalog-pydantic
```

## Examples 

### Create Table

```python
from unitycatalog.client import ApiClient, TablesApi
from unitycatalog_pydantic import UCModel

class MyTable(UCModel):
    col1: str
    col2: int
    col3: float

# Initialize the API client
catalog_client = ApiClient(...)
tables_api = TablesApi(catalog_client)

# Create the table
table_info = await MyTable.create(
    tables_api=tables_api,
    catalog_name="my_catalog",
    schema_name="my_schema",
    storage_location="s3://my_bucket/my_path",
)
```

### Retrieve Table
```python
table_info = await MyTable.get(
    tables_api=tables_api,
    catalog_name="my_catalog",
    schema_name="my_schema",
)
```

### Delete Table

```python
await MyTable.delete(
    tables_api=tables_api,
    catalog_name="my_catalog",
    schema_name="my_schema",
)
```

### Nested Models
```python
from pydantic import BaseModel
from unitycatalog.client import ApiClient, TablesApi
from unitycatalog_pydantic import UCModel

class NestedModel(BaseModel):
    nested_col1: str
    nested_col2: int

class MyTable(UCModel):
    col1: str
    col2: NestedModel

# Initialize the API client
catalog_client = ApiClient(...)
tables_api = TablesApi(catalog_client)

# Create the table
table_info = await MyTable.create(
    tables_api=tables_api,
    catalog_name="my_catalog",
    schema_name="my_schema",
    storage_location="s3://my_bucket/my_path",
)
```

### Using a BaseModel as root model
```python
from pydantic import BaseModel
from unitycatalog.client import ApiClient, TablesApi
from unitycatalog_pydantic import create_table

class NestedModel(BaseModel):
    nested_col1: str
    nested_col2: int

class MyTable(BaseModel):
    col1: str
    col2: NestedModel

# Initialize the API client
catalog_client = ApiClient(...)
tables_api = TablesApi(catalog_client)

# Create the table
table_info = await create_table(
    model=MyTable,
    tables_api=tables_api,
    catalog_name="my_catalog",
    schema_name="my_schema",
    storage_location="s3://my_bucket/my_path",
)
```

## Configuration

- tables_api: The `TablesApi` client.
- catalog_name: The catalog name.
- schema_name: The schema name.
- storage_location: The storage location.
- table_type: The table type (default is `TableType.EXTERNAL`).
- data_source_format: The data source format (default is `DataSourceFormat.DELTA`).
- comment: A comment for the table. If not provided, the table docstring is used
- properties: The properties of the table.
- by_alias: Whether to use the alias or name for the columns (default is `True`).
- json_schema_mode: The mode in which to generate the schema (default is `validation`).
- alias: The table alias. If not provided, the class name is used.


## Caveats

Tested on Parquet, Delta, and CSV data source formats. Other formats may not work as expected.

- Currently, Parquet and Unity Catalog type integration is pretty limited. For instance, there is no way to specify the
  integer type, because Parquet doesn't recognize integer SQL types. The same goes for other types like `DATE`, `TIMESTAMP`, etc.. This is an integration issue and not a problem with the library itself.
- You can't use nested models for CSV data source format. This is because CSV doesn't support nested types. This is an issue with the data source format and not the library itself.
- Latest version of DuckDB doesn't support reading some of the required fields for UC's ColumnInfo model. e.g., precision fields. This is an integration issue and not a problem with the library itself.