import os
import tempfile
from decimal import Decimal

import pytest
from polyfactory.factories.pydantic_factory import ModelFactory
from pydantic import BaseModel, Field
from typing import List, Dict

from pyspark.sql import SparkSession
from unitycatalog.client import ApiClient, TablesApi, DataSourceFormat
from unitycatalog.client.exceptions import NotFoundException

from unitycatalog_pydantic import UCModel


class NestedColumn(BaseModel):
    col1: str
    col2: Decimal = Field(..., max_digits=10, decimal_places=2)


class NestedTable(UCModel):
    """Table with nested columns"""

    col1: str
    col2: int
    nested: List[Dict[str, int]]
    nested_model_col: NestedColumn


class FlatTable(UCModel):
    col1: str
    col2: int
    col3: Decimal = Field(..., max_digits=10, decimal_places=2)


class ParquetTable(UCModel):
    """Table with columns"""

    col1: str
    col2: str


class ParquetTableFactory(ModelFactory[ParquetTable]):
    __model__ = ParquetTable


class NestedTableFactory(ModelFactory[NestedTable]):
    __model__ = NestedTable

    @classmethod
    def build(cls, **kwargs):
        instance = super().build(**kwargs)
        # Ensure the nested field has multiple entries
        instance.nested = [{"key1": 1}, {"key2": 2}, {"key3": 3}]
        return instance


class FlatTableFactory(ModelFactory[FlatTable]):
    __model__ = FlatTable


@pytest.mark.asyncio
async def test_create_table(catalog_client: ApiClient):
    tables_api = TablesApi(catalog_client)
    table_info = await NestedTable.create(
        tables_api=tables_api,
        catalog_name="unity",
        schema_name="default",
        storage_location="s3://test_bucket/test_path",
    )

    assert table_info.name == "nestedtable"
    assert table_info.catalog_name == "unity"
    assert table_info.schema_name == "default"
    assert table_info.table_type == "EXTERNAL"
    assert table_info.data_source_format == DataSourceFormat.DELTA
    assert table_info.comment == "Table with nested columns"
    assert len(table_info.columns) == 4
    assert table_info.columns[0].name == "col1"
    assert table_info.columns[0].type_name == "STRING"
    assert table_info.columns[1].name == "col2"
    assert table_info.columns[1].type_name == "LONG"
    assert table_info.columns[2].name == "nested"
    assert table_info.columns[2].type_name == "ARRAY"
    assert table_info.columns[3].name == "nested_model_col"
    assert table_info.columns[3].type_name == "STRUCT"


@pytest.mark.asyncio
async def test_create_table_by_alias(catalog_client: ApiClient):
    tables_api = TablesApi(catalog_client)
    table_info = await NestedTable.create(
        tables_api=tables_api,
        catalog_name="unity",
        schema_name="default",
        storage_location="s3://test_bucket/test_path",
        alias="nested_table",
    )

    assert table_info.name == "nested_table"


@pytest.mark.asyncio
async def test_delete_table(catalog_client: ApiClient):
    tables_api = TablesApi(catalog_client)
    await NestedTable.create(
        tables_api=tables_api,
        catalog_name="unity",
        schema_name="default",
        storage_location="s3://test_bucket/test_path",
        alias="table_to_delete"
    )

    await NestedTable.delete(
        tables_api=tables_api, catalog_name="unity", schema_name="default", alias="table_to_delete"
    )

    # Try to get the deleted table and expect an error or None
    with pytest.raises(NotFoundException):
        await NestedTable.get(tables_api, catalog_name="unity", schema_name="default", alias="table_to_delete")


@pytest.mark.asyncio
async def test_create_parquet_table(catalog_client: ApiClient, spark: SparkSession):
    tables_api = TablesApi(catalog_client)
    fake_data = ParquetTableFactory.batch(size=10)

    df = spark.createDataFrame([data.dict() for data in fake_data])

    with tempfile.TemporaryDirectory() as temp_dir:
        parquet_path = os.path.join(temp_dir, "data.parquet")
        df.write.format("parquet").save(parquet_path)

        table_info = await ParquetTable.create(
            tables_api=tables_api,
            catalog_name="unity",
            schema_name="default",
            storage_location=parquet_path,
            data_source_format=DataSourceFormat.PARQUET,
        )

        assert table_info.name == "parquettable"
        assert table_info.data_source_format == DataSourceFormat.PARQUET

        rows = spark.table("default.parquettable").collect()
        rows = sorted(rows, key=lambda x: x.col1)
        expected_rows = sorted(df.collect(), key=lambda x: x.col1)
        assert len(rows) == 10

        assert rows[0].col1 == expected_rows[0].col1
        assert rows[0].col2 == expected_rows[0].col2


@pytest.mark.asyncio
async def test_create_csv_table(catalog_client: ApiClient, spark: SparkSession):
    tables_api = TablesApi(catalog_client)
    fake_data = FlatTableFactory.batch(size=10)
    df = spark.createDataFrame([data.dict() for data in fake_data])

    with tempfile.TemporaryDirectory() as temp_dir:
        csv_path = os.path.join(temp_dir, "data.csv")
        df.write.format("csv").save(csv_path)

        table_info = await FlatTable.create(
            tables_api=tables_api,
            catalog_name="unity",
            schema_name="default",
            storage_location=csv_path,
            data_source_format=DataSourceFormat.CSV,
        )

        assert table_info.name == "flattable"
        assert table_info.data_source_format == DataSourceFormat.CSV

        rows = spark.table("default.flattable").collect()
        rows = sorted(rows, key=lambda x: x.col1)
        assert len(rows) == 10
        expected_rows = sorted(df.collect(), key=lambda x: x.col1)
        assert rows[0].col1 == expected_rows[0].col1
        assert rows[0].col2 == expected_rows[0].col2
        assert rows[0].col3 == expected_rows[0].col3


@pytest.mark.asyncio
async def test_create_delta_table(catalog_client: ApiClient, spark: SparkSession):
    tables_api = TablesApi(catalog_client)
    fake_data = NestedTableFactory.batch(size=10)
    df = spark.createDataFrame([data.dict() for data in fake_data])

    with tempfile.TemporaryDirectory() as temp_dir:
        delta_path = os.path.join(temp_dir, "delta_table")

        df.write.format("delta").save(delta_path)
        table_info = await NestedTable.create(
            tables_api=tables_api,
            catalog_name="unity",
            schema_name="default",
            storage_location=delta_path,
            alias="deltatable"
        )

        assert table_info.name == "deltatable"
        assert table_info.data_source_format == DataSourceFormat.DELTA

        rows = sorted(spark.table("default.deltatable").collect(), key=lambda x: x.col1)
        expected_rows = sorted(df.collect(), key=lambda x: x.col1)
        assert len(rows) == 10
        assert rows[0].col1 == expected_rows[0].col1
        assert rows[0].nested_model_col['col2'] == expected_rows[0].nested_model_col['col2']
