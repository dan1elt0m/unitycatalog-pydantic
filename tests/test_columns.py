import json
import datetime
import os
import tempfile
from decimal import Decimal
from typing import List, Dict, Optional, Type, Tuple, Union, Any

import pytest
from polyfactory.factories.pydantic_factory import ModelFactory
from pydantic import BaseModel, Field
from unitycatalog.client import ColumnInfo, ColumnTypeName, TablesApi, DataSourceFormat
from unitycatalog_pydantic import UCModel, create_table
from unitycatalog_pydantic.map import get_column_info_list, pydantic_type_to_sql_type, pydantic_type_to_uc_type_json


def factory(model):
    class TableFactory(ModelFactory[model]):
        __model__ = model

    return TableFactory


class StringCol(BaseModel):
    col_str: str


class IntCol(BaseModel):
    col_int: int


class FloatCol(BaseModel):
    col_float: float


class BoolCol(BaseModel):
    col_bool: bool


class DateCol(BaseModel):
    col_date: datetime.date


class DateTimeCol(BaseModel):
    col_datetime: datetime.datetime


class TimeDeltaCol(BaseModel):
    col_timedelta: datetime.timedelta


class DecimalCol(BaseModel):
    col_decimal: Decimal = Field(..., max_digits=38, decimal_places=18)

class ListCol(BaseModel):
    col_list: List[int]


class TupleCol(BaseModel):
    col_tuple: Tuple[int]


class DictCol(BaseModel):
    col_dict: Dict[str, int]


class BytesCol(BaseModel):
    col_bytes: bytes


class NoneCol(BaseModel):
    col_none: Optional[str] = None


class NestedCol(BaseModel):
    col_nested: List[Dict[str, int]]


class AliasCol(BaseModel):
    col_alias: str = Field(alias="col_alias_name")


class DescriptionCol(BaseModel):
    col_description: str = Field(description="Column description")


class NestedBaseModel(BaseModel):
    nested_col: int


class NestedBaseModelColumn(BaseModel):
    col_nested: NestedBaseModel


class NestedUCModel(UCModel):
    nested_col: int


class NestedUCModelColumn(UCModel):
    col_nested: NestedUCModel


class NestedDeepUCModel(UCModel):
    deep_nested_col: NestedUCModel


class NestedDeepUCModelColumn(UCModel):
    col_nested: NestedDeepUCModel


class NestedAliasModel(BaseModel):
    nested_col: int = Field(alias="nested_alias_col")


class NestedAliasModelColumn(BaseModel):
    col_nested: NestedAliasModel

class NestedListUCModel(UCModel):
    nested_col: int


class NestedListUCModelColumn(UCModel):
    col_nested: List[NestedUCModel]

class NestedUCModelWithList(UCModel):
    nested_col: List[str]

class NestedUCModelWithListColumn(UCModel):
    col_nested: NestedUCModelWithList

class NestedUCModelWithDict(UCModel):
    nested_col: Dict[str, int]

class NestedUCModelWithDictColumn(UCModel):
    col_nested: NestedUCModelWithDict

class NestedUCModelWithOptional(BaseModel):
    optional_field: Optional[int]

class NestedUCModelWithOptionalColumn(UCModel):
    col_nested: NestedUCModelWithOptional

class NestedUCModelWithUnion(UCModel):
    col_nested: Union[str, int]

class NestedUCModelWithUnionColumn(UCModel):
    col_nested: NestedUCModelWithUnion

@pytest.mark.parametrize(
    "columns, expected",
    [
        (
            StringCol,
            ColumnInfo(
                name="col_str",
                type_text="STRING",
                type_name=ColumnTypeName.STRING.value,
                type_json=json.dumps({"type": "string"}),
                nullable=False,
                position=0,
            ),
        ),
        (
            IntCol,
            ColumnInfo(
                name="col_int",
                type_text="LONG",
                type_name=ColumnTypeName.LONG.value,
                type_json=json.dumps({"type": "long"}),
                nullable=False,
                position=0,
            ),
        ),
        (
            FloatCol,
            ColumnInfo(
                name="col_float",
                type_text="DOUBLE",
                type_name=ColumnTypeName.DOUBLE.value,
                type_json=json.dumps({"type": "double"}),
                nullable=False,
                position=0,
            ),
        ),
        (
            BoolCol,
            ColumnInfo(
                name="col_bool",
                type_text="BOOLEAN",
                type_name=ColumnTypeName.BOOLEAN.value,
                type_json=json.dumps({"type": "boolean"}),
                nullable=False,
                position=0,
            ),
        ),
        (
            DateCol,
            ColumnInfo(
                name="col_date",
                type_text="DATE",
                type_name=ColumnTypeName.DATE.value,
                type_json=json.dumps({"type": "date"}),
                nullable=False,
                position=0,
            ),
        ),
        (
            DateTimeCol,
            ColumnInfo(
                name="col_datetime",
                type_text="TIMESTAMP",
                type_name=ColumnTypeName.TIMESTAMP.value,
                type_json=json.dumps({"type": "timestamp"}),
                nullable=False,
                position=0,
            ),
        ),
        (
            TimeDeltaCol,
            ColumnInfo(
                name="col_timedelta",
                type_text="INTERVAL DAY TO SECOND",
                type_name=ColumnTypeName.INTERVAL.value,
                type_json=json.dumps({"type": "interval"}),
                nullable=False,
                position=0,
            ),
        ),
        (
            DecimalCol,
            ColumnInfo(
                name="col_decimal",
                type_text="DECIMAL(38, 18)",
                type_name=ColumnTypeName.DECIMAL.value,
                type_json=json.dumps({"type": "decimal"}),
                nullable=False,
                position=0,
            ),
        ),
        (
            ListCol,
            ColumnInfo(
                name="col_list",
                type_text="ARRAY<LONG>",
                type_name=ColumnTypeName.ARRAY.value,
                type_json=json.dumps({"type": "array"}),
                nullable=False,
                position=0,
            ),
        ),
        (
            TupleCol,
            ColumnInfo(
                name="col_tuple",
                type_text="ARRAY<LONG>",
                type_name=ColumnTypeName.ARRAY.value,
                type_json=json.dumps({"type": "array"}),
                nullable=False,
                position=0,
            ),
        ),
        (
            DictCol,
            ColumnInfo(
                name="col_dict",
                type_text="MAP<STRING, LONG>",
                type_name=ColumnTypeName.MAP.value,
                type_json=json.dumps({"type": "map"}),
                nullable=False,
                position=0,
            ),
        ),
        (
            BytesCol,
            ColumnInfo(
                name="col_bytes",
                type_text="BINARY",
                type_name=ColumnTypeName.BINARY.value,
                type_json=json.dumps({"type": "binary"}),
                nullable=False,
                position=0,
            ),
        ),
        (
            NoneCol,
            ColumnInfo(
                name="col_none",
                type_text="STRING",
                type_name=ColumnTypeName.STRING.value,
                type_json=json.dumps({"type": "string"}),
                nullable=True,
                position=0,
            ),
        ),
        (
            NestedCol,
            ColumnInfo(
                name="col_nested",
                type_text="ARRAY<MAP<STRING, LONG>>",
                type_name=ColumnTypeName.ARRAY.value,
                type_json=json.dumps({"type": "array"}),
                nullable=False,
                position=0,
            ),
        ),
        (
            AliasCol,
            ColumnInfo(
                name="col_alias_name",
                type_text="STRING",
                type_name=ColumnTypeName.STRING.value,
                type_json=json.dumps({"type": "string"}),
                nullable=False,
                position=0,
            ),
        ),
        (
            DescriptionCol,
            ColumnInfo(
                name="col_description",
                type_text="STRING",
                type_name=ColumnTypeName.STRING.value,
                type_json=json.dumps({"type": "string"}),
                nullable=False,
                comment="Column description",
                position=0,
            ),
        ),
        (
            NestedBaseModelColumn,
            ColumnInfo(
                name="col_nested",
                type_text="STRUCT<nested_col:LONG>",
                type_name=ColumnTypeName.STRUCT.value,
                type_json=json.dumps(
                    {
                        "type": "struct",
                        "fields": [
                            {
                                "name": "nested_col",
                                "type": "long",
                                "nullable": False,
                                "metadata": {"comment": None},
                            }
                        ],
                    }
                ),
                nullable=False,
                position=0,
            ),
        ),
        (
            NestedUCModelColumn,
            ColumnInfo(
                name="col_nested",
                type_text="STRUCT<nested_col:LONG>",
                type_name=ColumnTypeName.STRUCT.value,
                type_json=json.dumps(
                    {
                        "type": "struct",
                        "fields": [
                            {
                                "name": "nested_col",
                                "type": "long",
                                "nullable": False,
                                "metadata": {"comment": None},
                            }
                        ],
                    }
                ),
                nullable=False,
                position=0,
            ),
        ),
        (
            NestedDeepUCModelColumn,
            ColumnInfo(
                name="col_nested",
                type_text="STRUCT<deep_nested_col:STRUCT<nested_col:LONG>>",
                type_name=ColumnTypeName.STRUCT.value,
                type_json=json.dumps(
                    {
                        "type": "struct",
                        "fields": [
                            {
                                "name": "deep_nested_col",
                                "type": {
                                    "type": "struct",
                                    "fields": [
                                        {
                                            "name": "nested_col",
                                            "type": "long",
                                            "nullable": False,
                                            "metadata": {"comment": None},
                                        }
                                    ],
                                },
                                "nullable": False,
                                "metadata": {"comment": None},
                            }
                        ],
                    }
                ),
                nullable=False,
                position=0,
            ),
        ),
        (
            NestedAliasModelColumn,
            ColumnInfo(
                name="col_nested",
                type_text="STRUCT<nested_alias_col:LONG>",
                type_name=ColumnTypeName.STRUCT.value,
                type_json=json.dumps(
                    {
                        "type": "struct",
                        "fields": [
                            {
                                "name": "nested_alias_col",
                                "type": "long",
                                "nullable": False,
                                "metadata": {"comment": None},
                            }
                        ],
                    }
                ),
                nullable=False,
                position=0,
            ),
        ),
        (
                NestedListUCModelColumn,
                ColumnInfo(
                    name="col_nested",
                    type_text="ARRAY<STRUCT<nested_col:LONG>>",
                    type_name=ColumnTypeName.ARRAY.value,
                    type_json=json.dumps(
                        {"type": "array"},
                    ),
                    nullable=False,
                    position=0,
                ),
        ),
        (
                NestedUCModelWithListColumn,
                ColumnInfo(
                    name="col_nested",
                    type_text='STRUCT<nested_col:ARRAY<STRING>>',
                    type_json='{"type": "struct", "fields": [{"name": "nested_col", "type": {"type": "array", "elementType": "char", "containsNull": false}, "nullable": false, "metadata": {"comment": null}}]}',
                    type_name=ColumnTypeName.STRUCT.value,
                    nullable=False,
                    position=0,
                ),
        ),
        (
                NestedUCModelWithDictColumn,
                ColumnInfo(
                    name="col_nested",
                    type_text='STRUCT<nested_col:MAP<STRING, LONG>>',
                    type_json='{"type": "struct", "fields": [{"name": "nested_col", "type": {"type": "map", "keyType": "string", "valueType": "long", "valueContainsNull": false}, "nullable": false, "metadata": {"comment": null}}]}',
                    type_name= ColumnTypeName.STRUCT.value,
                    nullable=False,
                    position=0,
                ),
        ),
        (
                NestedUCModelWithOptionalColumn,
                ColumnInfo(
                    name="col_nested",
                    type_text='STRUCT<optional_field:LONG>',
                    type_json='{"type": "struct", "fields": [{"name": "optional_field", "type": "long", "nullable": true, "metadata": {"comment": null}}]}',                    type_name= ColumnTypeName.STRUCT.value,
                    nullable=False,
                    position=0,
                ),
        ),
        (
                NestedUCModelWithUnionColumn,
                ColumnInfo(
                    name="col_nested",
                    type_text='STRUCT<col_nested:STRING>',
                    type_json='{"type": "struct", "fields": [{"name": "col_nested", "type": "char", "nullable": true, "metadata": {"comment": null}}]}',
                    type_name=ColumnTypeName.STRUCT.value,
                    nullable=False,
                    position=0,
                ),
        ),
    ],
)
@pytest.mark.asyncio
async def test_get_column_info_list(columns: Type[BaseModel], expected: ColumnInfo, spark, catalog_client):
    column_info_list = get_column_info_list(columns)
    assert column_info_list[0] == expected
    if columns.__name__ in ["TimeDeltaCol", "NoneCol", "NestedUCModelWithOptionalColumn"]:
        # Writing IntervalType and None is not supported in PySpark
        return


    tables_api = TablesApi(catalog_client)
    fake_data = factory(columns).batch(size=1)

    df = spark.createDataFrame([data.dict() for data in fake_data])

    with tempfile.TemporaryDirectory() as temp_dir:
        delta_path = os.path.join(temp_dir, "delta_table")

        df.write.format("delta").save(delta_path)
        await create_table(
            model=columns,
            tables_api=tables_api,
            catalog_name="unity",
            schema_name="default",
            storage_location=delta_path,
        )

        rows = spark.table(f"default.{columns.__name__.lower()}").collect()
        expected_rows = df.collect()
        assert len(rows) == 1
        assert rows[0] == expected_rows[0]


def test_get_column_info_list_no_alias():
    class AliasCol(BaseModel):
        col: str = Field(alias="col_alias_name")

    column_info_list = get_column_info_list(AliasCol, by_alias=False)
    assert column_info_list[0].name == "col"

def test_get_column_info_alias_serialization():
    class AliasCol(BaseModel):
        col: str = Field(alias="col_alias_name")

    column_info_list = get_column_info_list(AliasCol, json_schema_mode="serialization")
    assert column_info_list[0].name == "col_alias_name"

def test_unsupported_type():
    class UnionCol(BaseModel):
        # Union col with more than 2 types is not supported
        col: Union[str, int, Decimal]

    class NestedCol(BaseModel):
        nested_col: UnionCol

    with pytest.raises(ValueError, match="Unsupported"):
        get_column_info_list(NestedCol)


class ModelWithAny(BaseModel):
    any_field: Any

class ModelWithEmptyDict(BaseModel):
    empty_dict_field: Dict

class ModelWithEmptyList(BaseModel):
    empty_list_field: List

class ModelWithNonStringKeyDict(BaseModel):
    non_string_key_dict: Dict[int, str]

class ModelWithUnionNone(BaseModel):
    union_none_field: Union[None, int]

class ModelWithUnion(BaseModel):
    union_none_field: Union[str, int]

class ModelWithUnknownType(BaseModel):
    unknown_field: "UnknownType"

def test_pydantic_type_to_sql_type_any():
    with pytest.raises(ValueError, match="Unsupported Pydantic type: typing.Any is not allowed. Please specify a concrete type."):
        pydantic_type_to_sql_type(ModelWithAny.__annotations__['any_field'])

def test_pydantic_type_to_sql_type_empty_dict():
    with pytest.raises(ValueError, match="Unsupported Pydantic type: typing.Dict requires key and value types."):
        pydantic_type_to_sql_type(ModelWithEmptyDict.__annotations__['empty_dict_field'])

def test_pydantic_type_to_sql_type_empty_list():
    with pytest.raises(ValueError, match="Unsupported Pydantic type: typing.List or typing.Tuple requires an element type."):
        pydantic_type_to_sql_type(ModelWithEmptyList.__annotations__['empty_list_field'])

def test_pydantic_type_to_sql_type_non_string_key_dict():
    with pytest.raises(TypeError, match="Only support STRING key type"):
        pydantic_type_to_sql_type(ModelWithNonStringKeyDict.__annotations__['non_string_key_dict'])

def test_pydantic_type_to_sql_type_union_none():
    sql_type = pydantic_type_to_sql_type(ModelWithUnionNone.__annotations__['union_none_field'])
    assert sql_type == "LONG"  # Assuming the function maps Union[None, int] to LONG

def test_pydantic_type_to_sql_type_unknown_type():
    with pytest.raises(ValueError, match="Unsupported Pydantic type: UnknownType"):
        pydantic_type_to_sql_type(ModelWithUnknownType.__annotations__['unknown_field'])

def test_pydantic_type_to_json_type_union_none():
    json_type = pydantic_type_to_uc_type_json(ModelWithUnionNone.__annotations__['union_none_field'])
    assert json_type == "long"

def test_pydantic_type_to_json_type_union():
    json_type = pydantic_type_to_uc_type_json(ModelWithUnion.__annotations__['union_none_field'])
    assert json_type == "char"

def test_pydantic_type_to_json_type_unknown_type():
    with pytest.raises(TypeError, match="Unknown type UnknownType."):
        pydantic_type_to_uc_type_json(ModelWithUnknownType.__annotations__['unknown_field'])

def test_pydantic_type_to_json_non_string_key_dict():
    with pytest.raises(TypeError, match="Only support STRING key type"):
        pydantic_type_to_uc_type_json(ModelWithNonStringKeyDict.__annotations__['non_string_key_dict'])

def test_python_type_to_sql_type_any():
    with pytest.raises(ValueError, match="Unsupported Pydantic type: typing.Any is not allowed. Please specify a concrete type."):
        pydantic_type_to_sql_type(Any)

def test_python_type_to_sql_type_empty_dict():
    with pytest.raises(ValueError, match="Unsupported Pydantic type: typing.Dict requires key and value types."):
        pydantic_type_to_sql_type(Dict)