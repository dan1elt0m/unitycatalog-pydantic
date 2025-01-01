from __future__ import annotations

import decimal
import inspect
import json
from typing import Any, get_origin, get_args, Type, Union, Dict, List, Optional, Tuple

from pydantic import BaseModel, AliasPath, AliasChoices
from pydantic.fields import FieldInfo
from unitycatalog.ai.core.utils.type_utils import PYTHON_TO_SQL_TYPE_MAPPING, UC_TYPE_JSON_MAPPING
from unitycatalog.client import ColumnInfo


def python_type_to_sql_type(py_type: Any) -> str:
    """
    Convert a Python type to its SQL equivalent. Handles nested types (e.g., List[Dict[str, int]])
    by recursively mapping the inner types using PYTHON_TO_SQL_TYPE_MAPPING.

    Args:
        py_type: The Python type to be converted (e.g., List[int], Dict[str, List[int]]).

    Returns:
        str: The corresponding SQL type (e.g., ARRAY<MAP<STRING, LONG>>).

    Raises:
        ValueError: If the type cannot be mapped to a SQL type.
    """
    if py_type is Any:
        raise ValueError(
            "Unsupported Python type: typing.Any is not allowed. Please specify a concrete type."
        )
    elif inspect.isclass(py_type) and issubclass(py_type, BaseModel):
        fields = []
        for field_name, field_type in py_type.__annotations__.items():
            field_sql_type = python_type_to_sql_type(field_type)
            fields.append(f"{field_name}:{field_sql_type}")
        return f"STRUCT<{', '.join(fields)}>"

    origin = get_origin(py_type)

    if origin is dict:
        if not get_args(py_type):
            raise ValueError(f"Unsupported Python type: typing.Dict requires key and value types.")

        key_type, value_type = get_args(py_type)
        key_sql_type = python_type_to_sql_type(key_type)
        value_sql_type = python_type_to_sql_type(value_type)
        return f"MAP<{key_sql_type}, {value_sql_type}>"

    elif origin in (list, tuple):
        if not get_args(py_type):
            raise ValueError(
                f"Unsupported Python type: typing.List or typing.Tuple requires an element type."
            )

        (element_type,) = get_args(py_type)
        element_sql_type = python_type_to_sql_type(element_type)
        return f"ARRAY<{element_sql_type}>"



    if sql_type := PYTHON_TO_SQL_TYPE_MAPPING.get(py_type):
        return sql_type

    raise ValueError(f"Unsupported Python type: {py_type}")


def pydantic_type_to_sql_type(
    py_type: Any, use_alias: bool = True, json_schema_mode: str = "validation"
) -> str:
    """
    Convert a Pydantic type to its SQL equivalent. Handles nested types (e.g., List[Dict[str, int]])
    by recursively mapping the inner types using PYTHON_TO_SQL_TYPE_MAPPING.

    Args:
        py_type (Any): The Pydantic type to be converted (e.g., List[int], Dict[str, List[int]]).
        use_alias (bool): Whether to use the alias or name for the column. Defaults to True.
        json_schema_mode (str): The mode in which to generate the schema. Defaults to "validation".

    Returns:
        str: The corresponding SQL type (e.g., ARRAY<MAP<STRING, LONG>>).

    Raises:
        ValueError: If the type cannot be mapped to a SQL type.
    """
    if py_type is Any:
        raise ValueError(
            "Unsupported Pydantic type: typing.Any is not allowed. Please specify a concrete type."
        )

    origin = get_origin(py_type)

    if origin is dict:
        if not get_args(py_type):
            raise ValueError(
                "Unsupported Pydantic type: typing.Dict requires key and value types."
            )

        key_type, value_type = get_args(py_type)
        if key_type is not str:
            raise TypeError(
                f"Only support STRING key type for MAP but got {key_type}."
            )
        key_sql_type = pydantic_type_to_sql_type(key_type, use_alias, json_schema_mode)
        value_sql_type = pydantic_type_to_sql_type(
            value_type, use_alias, json_schema_mode
        )
        return f"MAP<{key_sql_type}, {value_sql_type}>"

    elif origin in (list, tuple):
        if not get_args(py_type):
            raise ValueError(
                "Unsupported Pydantic type: typing.List or typing.Tuple requires an element type."
            )

        (element_type,) = get_args(py_type)
        element_sql_type = pydantic_type_to_sql_type(
            element_type, use_alias, json_schema_mode
        )
        return f"ARRAY<{element_sql_type}>"
    elif origin == Union:
        args = get_args(py_type)
        if len(args) == 2 and type(None) in args:
            # this is an optional column. Just return the non-optional type
            arg = args[0] if args[0] != type(None) else args[1]
            return pydantic_type_to_sql_type(arg, use_alias, json_schema_mode)
        elif len(args) == 2:
            # always cast to string for now
            return "STRING"

    if inspect.isclass(py_type) and issubclass(py_type, BaseModel):
        fields = []
        for field_name, field_type in py_type.__annotations__.items():
            if use_alias:
                field_name = _get_field_alias(
                    field_name, py_type.model_fields[field_name], json_schema_mode
                )
            field_sql_type = pydantic_type_to_sql_type(
                field_type, use_alias, json_schema_mode
            )
            fields.append(f"{field_name}:{field_sql_type}")
        return f"STRUCT<{', '.join(fields)}>"

    if sql_type := PYTHON_TO_SQL_TYPE_MAPPING.get(py_type):
        return sql_type

    raise ValueError(f"Unsupported Pydantic type: {py_type}")


def pydantic_type_to_uc_type_json(
    pydantic_type: Type[BaseModel],
    strict: bool = False,
    use_alias: bool = True,
    json_schema_mode: str = "validation",
) -> Union[str, Dict[str, Any]]:
    """
    Convert Pydantic type to Unity Catalog type JSON.

    Args:
        pydantic_type (Type[BaseModelOrUCModel]): The Pydantic type to convert.
        strict (bool): Whether the type strictly follows the JSON schema type. Defaults to False.
        use_alias (bool): Whether to use the alias or name for the column. Defaults to True.
        json_schema_mode (str): The mode in which to generate the schema. Defaults to "validation".

    Returns:
        Union[str, Dict[str, Any]]: The Unity Catalog type JSON.
    """
    if pydantic_type is int:
        # Always use long to prevent data loss
        return "long"
    elif pydantic_type in UC_TYPE_JSON_MAPPING.values():
        for key, value in UC_TYPE_JSON_MAPPING.items():
            if value == pydantic_type:
                return key.lower()
    elif pydantic_type in [decimal.Decimal, float]:
        return "decimal"
    elif hasattr(pydantic_type, "__origin__"):
        origin = pydantic_type.__origin__
        if origin is list or origin == List:
            element_type = pydantic_type.__args__[0]
            return {
                "type": "array",
                "elementType": pydantic_type_to_uc_type_json(
                    element_type,
                    strict=strict,
                    use_alias=use_alias,
                    json_schema_mode=json_schema_mode,
                ),
                "containsNull": element_type == Optional[element_type],
            }
        elif origin is dict or origin == Dict:
            key_type, value_type = pydantic_type.__args__
            if key_type is not str:
                raise TypeError(
                    f"Only support STRING key type for MAP but got {key_type}."
                )
            return {
                "type": "map",
                "keyType": "string",
                "valueType": pydantic_type_to_uc_type_json(
                    value_type,
                    strict=strict,
                    use_alias=use_alias,
                    json_schema_mode=json_schema_mode,
                ),
                "valueContainsNull": value_type == Optional[value_type],
            }
        elif origin == Union:
            args = get_args(pydantic_type)
            if len(args) == 2 and type(None) in args:
                # this is an optional column
                arg = args[0] if args[0] != type(None) else args[1]
                return pydantic_type_to_uc_type_json(arg, strict=strict)
            elif len(args) == 2:
                # always cast to string for now
                return pydantic_type_to_uc_type_json(str, strict=strict)

    elif inspect.isclass(pydantic_type) and issubclass(pydantic_type, BaseModel):
        fields = []
        for name, field in pydantic_type.model_fields.items():
            nullable, python_type = _is_nullable(field.annotation)
            if use_alias:
                name = _get_field_alias(name, field, json_schema_mode)
            field_type_json = pydantic_type_to_uc_type_json(
                python_type,
                strict=strict,
                use_alias=use_alias,
                json_schema_mode=json_schema_mode,
            )
            field_json = {
                "name": name,
                "type": field_type_json,
                "nullable": nullable,
                "metadata": {"comment": field.description},
            }
            fields.append(field_json)
        return {"type": "struct", "fields": fields}
    else:
        raise TypeError(f"Unknown type {pydantic_type}.")


def _get_field_alias(name: str, field_info: FieldInfo, mode: str = "validation") -> str:
    """
    Get the alias for a field based on the mode.

    Args:
        name (str): The field name.
        field_info (FieldInfo): The field information.
        mode (str): The mode in which to generate the alias. Defaults to "validation".

    Returns:
        str: The alias for the field.
    """
    alias = None
    if mode == "serialization":
        alias = field_info.serialization_alias or field_info.alias
    elif mode == "validation":
        validation_alias = field_info.validation_alias
        if validation_alias is None or isinstance(validation_alias, AliasPath):
            alias = field_info.alias
        elif isinstance(validation_alias, AliasChoices):
            alias = validation_alias.choices[0]
        else:
            alias = validation_alias
    return alias or name


def _is_nullable(t: Type) -> Tuple[bool, Type]:
    """
    Check if a type is nullable.

    Args:
        t (Type): The type to check.

    Returns:
        Tuple[bool, Type]: A tuple containing a boolean indicating if the type is nullable and the type itself.
    """
    if get_origin(t) == Union:
        type_args = get_args(t)
        if any([get_origin(arg) is None for arg in type_args]):
            t = type_args[0]
            return True, t
    return False, t


def get_column_info_list(
    columns: Type[BaseModel],
    by_alias: bool = True,
    json_schema_mode: str = "validation",
) -> List[ColumnInfo]:
    """
    Get a list of Unity Catalog ColumnInfo objects from a Pydantic model.

    Args:
        columns (Type[BaseModel]): The Pydantic model.
        by_alias (bool): Whether to use the alias or name for the column. Defaults to True.
        json_schema_mode (str): The mode in which to generate the schema. Defaults to "validation".

    Returns:
        List[ColumnInfo]: A list of column information.
    """
    column_info_list = []

    for index, (field_name, field_info) in enumerate(columns.model_fields.items()):
        if by_alias:
            field_name = _get_field_alias(field_name, field_info, json_schema_mode)
        nullable, python_type = _is_nullable(field_info.annotation)

        origin = get_origin(python_type)
        if not origin:
            origin = python_type

        if issubclass(origin, BaseModel):
            type_json = pydantic_type_to_uc_type_json(
                origin,
                strict=True,
                use_alias=by_alias,
                json_schema_mode=json_schema_mode,
            )
            type_text = pydantic_type_to_sql_type(origin)
            type_name = "STRUCT"
        else:
            type_name = PYTHON_TO_SQL_TYPE_MAPPING.get(origin)
            # Make sure unnecessary type information is removed from Type Name
            if "DECIMAL" in type_name:
                type_name = "DECIMAL"
            elif "INTERVAL" in type_name:
                type_name = "INTERVAL"
            type_text = python_type_to_sql_type(python_type)
            type_json = {"type": type_name.lower()}

        column_info = ColumnInfo(
            name=field_name,
            type_text=type_text,
            type_name=type_name,
            type_json=json.dumps(type_json),
            nullable=nullable,
            comment=field_info.description,
            position=index,
        )
        column_info_list.append(column_info)
    return column_info_list
