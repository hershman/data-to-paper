from typing import Any, Optional

import numpy as np
from pandas import DataFrame, Series

from data_to_paper.run_gpt_code.overrides.dataframes.utils import to_string_with_format_value


def describe_value(value: Any) -> str:
    """
    Describe the value in a way that can be used as a short string.
    """
    if value is None:
        return 'None'
    if isinstance(value, str):
        return f"'{value}'"
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, list):
        return f'[{", ".join(describe_value(v) for v in value)}]'
    if isinstance(value, dict):
        return f'{{{", ".join(f"{describe_value(k)}: {describe_value(v)}" for k, v in value.items())}}}'
    if isinstance(value, tuple):
        return f'({", ".join(describe_value(v) for v in value)})'
    if isinstance(value, DataFrame):
        return f'DataFrame(shape={value.shape}, columns={value.columns})'
    if isinstance(value, Series):
        return f'Series(shape={value.shape}, type={value.dtype})'
    if isinstance(value, np.ndarray):
        return f'np.ndarray(shape={value.shape}, dtype={value.dtype})'
    return str(value)


def describe_df(df: DataFrame, max_rows: Optional[int] = 25, max_columns: Optional[int] = 10) -> str:
    """
    Describe the DataFrame in a way that can be used as a short string.
    """
    num_lines = len(df)
    num_columns = len(df.columns)
    if max_columns is not None and num_columns > max_columns:
        return f'DataFrame(shape={df.shape})'
    if max_rows is not None and num_lines > max_rows:
        df = df.head(3)
    s = to_string_with_format_value(df)
    if num_lines > max_rows:
        s += f'\n... total {num_lines} rows'
    return s
