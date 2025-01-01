from __future__ import annotations

from typing import Annotated, Optional, Union

from pydantic import BaseModel, ConfigDict, Field
from unitycatalog.client import TablesApi, TableType, DataSourceFormat, TableInfo

from unitycatalog_pydantic.operations import create_table, get_table, delete_table


class UCModel(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, use_enum_values=True)

    @classmethod
    async def create(
        cls,
        tables_api: Annotated[TablesApi, Field(description="The TablesApi client")],
        catalog_name: Annotated[str, Field(description="The catalog name")],
        schema_name: Annotated[str, Field(description="The schema name")],
        storage_location: Annotated[str, Field(description="The storage location")],
        table_type: Annotated[
            TableType, Field(default=TableType.EXTERNAL, description="The table type")
        ] = TableType.EXTERNAL,
        data_source_format: Annotated[
            DataSourceFormat,
            Field(
                default=DataSourceFormat.DELTA, description="The data source format"
            ),
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
            Field(description="The table alias."),
        ] = None,
    ) -> TableInfo:
        """
        Create the table in Unity Catalog.

        Args:
            tables_api (Annotated[TablesApi, Field(description="The TablesApi client")]): The TablesApi client.
            catalog_name (Annotated[str, Field(description="The catalog name")]): The catalog name.
            schema_name (Annotated[str, Field(description="The schema name")]): The schema name.
            storage_location (Annotated[str, Field(description="The storage location")]): The storage location.
            table_type (Annotated[TableType, Field(default=TableType.EXTERNAL, description="The table type")]): The table type. Defaults to TableType.EXTERNAL.
            data_source_format (Annotated[DataSourceFormat, Field(default=DataSourceFormat.PARQUET, description="The data source format")]): The data source format. Defaults to DataSourceFormat.PARQUET.
            comment (Annotated[Optional[str], Field(description="A comment of the table")]): A comment of the table. Defaults to None.
            properties (Annotated[Optional[dict], Field(description="The properties of the table")]): The properties of the table. Defaults to None.
            by_alias (Annotated[bool, Field(description="Whether to use the alias or name for the column")]): Whether to use the alias or name for the column. Defaults to False.
            json_schema_mode (Annotated[str, Field(description="The mode in which to generate the schema")]): The mode in which to generate the schema. Defaults to "validation".
            alias (Annotated[Optional[str], Field(description="The table alias.")]): The table alias. Defaults to None.

        Returns:
            TableInfo: The table information.
        """
        return await create_table(
            cls,
            tables_api,
            catalog_name,
            schema_name,
            storage_location,
            table_type,
            data_source_format,
            comment,
            properties,
            by_alias,
            json_schema_mode,
            alias,
        )

    @classmethod
    async def get(
        cls,
        tables_api: Annotated[TablesApi, Field(description="The TablesApi client")],
        catalog_name: Annotated[str, Field(description="The catalog name")],
        schema_name: Annotated[str, Field(description="The schema name")],
        alias: Annotated[
            Optional[str],
            Field(description="The table alias"),
        ] = None,
    ) -> TableInfo:
        """
        Get the table from Unity Catalog.

        Args:
            tables_api (Annotated[TablesApi, Field(description="The TablesApi client")]): The TablesApi client.
            catalog_name (Annotated[str, Field(description="The catalog name")]): The catalog name.
            schema_name (Annotated[str, Field(description="The schema name")]): The schema name.
            alias (Annotated[Optional[str], Field(description="The table alias")]): The table alias. Defaults to None.

        Returns:
            TableInfo: The table information.
        """
        return await get_table(cls, tables_api, catalog_name, schema_name, alias)

    @classmethod
    async def delete(
        cls,
        tables_api: Annotated[TablesApi, Field(description="The TablesApi client")],
        catalog_name: Annotated[str, Field(description="The catalog name")],
        schema_name: Annotated[str, Field(description="The schema name")],
        alias: Annotated[
            Optional[str],
            Field(description="The table alias."),
        ] = None,
    ) -> None:
        """
        Delete the table from Unity Catalog.

        Args:
            tables_api (Annotated[TablesApi, Field(description="The TablesApi client")]): The TablesApi client.
            catalog_name (Annotated[str, Field(description="The catalog name")]): The catalog name.
            schema_name (Annotated[str, Field(description="The schema name")]): The schema name.
            alias (Annotated[Optional[str], Field(description="The table alias.")]): The table alias. Defaults to None.

        Returns:
            None
        """
        return await delete_table(cls, tables_api, catalog_name, schema_name, alias)




