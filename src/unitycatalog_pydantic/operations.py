from __future__ import annotations

import logging
from typing import Annotated, Type, Optional, Union

from pydantic import Field, BaseModel
from unitycatalog.client import TablesApi, TableType, DataSourceFormat, TableInfo, CreateTable

from unitycatalog_pydantic.map import get_column_info_list

logger = logging.getLogger(__name__)

BaseModelOrUCModel = Union[BaseModel, "UCModel"]

async def create_table(
    model: Annotated[Type[BaseModelOrUCModel], Field(description="The table model")],
    tables_api: Annotated[TablesApi, Field(description="The TablesApi client")],
    catalog_name: Annotated[str, Field(description="The catalog name")],
    schema_name: Annotated[str, Field(description="The schema name")],
    storage_location: Annotated[str, Field(description="The storage location")],
    table_type: Annotated[
        TableType, Field(default=TableType.EXTERNAL, description="The table type")
    ] = TableType.EXTERNAL,
    data_source_format: Annotated[
        DataSourceFormat,
        Field(default=DataSourceFormat.DELTA, description="The data source format"),
    ] = DataSourceFormat.DELTA,
    comment: Annotated[
        Optional[str], Field(description="A comment of the table")
    ] = None,
    properties: Annotated[
        Optional[dict], Field(description="The properties of the table")
    ] = None,
    by_alias: Annotated[
        bool, Field(description="Whether to use the alias or name for the column")
    ] = False,
    json_schema_mode: Annotated[
        str, Field(description="The mode in which to generate the schema")
    ] = "validation",
    alias: Annotated[
        Optional[str],
        Field(description="The table name alias."),
    ] = None,
) -> TableInfo:
    """
    Create a table in Unity Catalog.

    Args:
        model (Annotated[Type[BaseModelOrUCModel], Field(description="The table model")]): The table model.
        tables_api (Annotated[TablesApi, Field(description="The TablesApi client")]): The TablesApi client.
        catalog_name (Annotated[str, Field(description="The catalog name")]): The catalog name.
        schema_name (Annotated[str, Field(description="The schema name")]): The schema name.
        storage_location (Annotated[str, Field(description="The storage location")]): The storage location.
        table_type (Annotated[TableType, Field(default=TableType.EXTERNAL, description="The table type")]): The table type. Defaults to TableType.EXTERNAL.
        data_source_format (Annotated[DataSourceFormat, Field(default=DataSourceFormat.DELTA, description="The data source format")]): The data source format. Defaults to DataSourceFormat.DELTA.
        comment (Annotated[Optional[str], Field(description="A comment of the table")]): A comment of the table. Defaults to None.
        properties (Annotated[Optional[dict], Field(description="The properties of the table")]): The properties of the table. Defaults to None.
        by_alias (Annotated[bool, Field(description="Whether to use the alias or name for the column")]): Whether to use the alias or name for the column. Defaults to False.
        json_schema_mode (Annotated[str, Field(description="The mode in which to generate the schema")]): The mode in which to generate the schema. Defaults to "validation".
        alias (Annotated[Optional[str], Field(description="The table name alias.")]): The table name alias. Defaults to None.

    Returns:
        TableInfo: The table information.
    """
    # Use the model docstring as table comment if comment not provided
    if not comment:
        comment = model.__doc__

    return await tables_api.create_table(
        CreateTable(
            name=alias or model.__name__.lower(),
            catalog_name=catalog_name,
            schema_name=schema_name,
            table_type=table_type,
            data_source_format=data_source_format.upper(),
            storage_location=storage_location,
            columns=get_column_info_list(model, by_alias, json_schema_mode),
            comment=comment,
            properties=properties,
        )
    )


async def get_table(
    model: Annotated[Type[BaseModelOrUCModel], Field(description="The table model")],
    tables_api: Annotated[TablesApi, Field(description="The TablesApi client")],
    catalog_name: Annotated[str, Field(description="The catalog name")],
    schema_name: Annotated[str, Field(description="The schema name")],
    alias: Annotated[
        Optional[str],
        Field(description="The table name alias."),
    ] = None,
) -> TableInfo:
    """
    Get the table from Unity Catalog.

    Args:
        model (Annotated[Type[BaseModelOrUCModel], Field(description="The table model")]): The table model.
        tables_api (Annotated[TablesApi, Field(description="The TablesApi client")]): The TablesApi client.
        catalog_name (Annotated[str, Field(description="The catalog name")]): The catalog name.
        schema_name (Annotated[str, Field(description="The schema name")]): The schema name.
        alias (Annotated[Optional[str], Field(description="The table name alias.")]): The table name alias. Defaults to None.

    Returns:
        TableInfo: The table information.
    """
    name = alias or model.__name__.lower()
    return await tables_api.get_table(f"{catalog_name}.{schema_name}.{name}")


async def delete_table(
    model: Annotated[Type[BaseModelOrUCModel], Field(description="The table model")],
    tables_api: Annotated[TablesApi, Field(description="The TablesApi client")],
    catalog_name: Annotated[str, Field(description="The catalog name")],
    schema_name: Annotated[str, Field(description="The schema name")],
    alias: Annotated[
        Optional[str],
        Field(description="The table name alias."),
    ] = None,
) -> None:
    """
    Delete the table from Unity Catalog.

    Args:
        model (Annotated[Type[BaseModelOrUCModel], Field(description="The table model")]): The table model.
        tables_api (Annotated[TablesApi, Field(description="The TablesApi client")]): The TablesApi client.
        catalog_name (Annotated[str, Field(description="The catalog name")]): The catalog name.
        schema_name (Annotated[str, Field(description="The schema name")]): The schema name.
        alias (Annotated[Optional[str], Field(description="The table name alias.")]): The table name alias. Defaults to None.

    Returns:
        None
    """
    name = alias or model.__name__.lower()
    await tables_api.delete_table(f"{catalog_name}.{schema_name}.{name}")
