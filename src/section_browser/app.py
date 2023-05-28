from typing import Optional
from dataclasses import dataclass
import json
import pathlib
import pandas as pd
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print
import typer
import section_browser.w_sections as wsec

DATA_STORE_FILE = pathlib.Path(__file__).parents[0] / "DATA_STORE.json"
ROW_SELECTIONS: list[int] = []
DATA_STORE: dict = {}

app = typer.Typer(add_completion=False)


@app.command(
    name="all", 
    short_help="Loads all AISC w-sections and applies filters",
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True}
    )
def all_sections(ctx: typer.Context) -> pd.DataFrame:
    """
    Clears the data store file and loads all rows from the
    aisc db into the data store.

    Applies initial filters supplied in kwargs.
    """
    kwargs = _parse_kwargs(ctx.args)
    _clear_data_store()
    aisc_full_df = wsec.load_aisc_w_sections()
    current_selection = _apply_all_filters(aisc_full_df, kwargs)
    _set_current_indexes(list(current_selection.index), kwargs)
    print(_table_output(current_selection, title="AISC W-Sections: Current selection", subtitle=str(kwargs)))


@app.command(
        name="filter", 
        short_help="Applies filters",
        context_settings={"allow_extra_args": True, "ignore_unknown_options": True}
        )
def filter_sections(ctx: typer.Context) -> pd.DataFrame:
    """
    Clears the data store file and loads all rows from the
    aisc db into the data store.

    Applies initial filters supplied in kwargs.
    """
    kwargs = _parse_kwargs(ctx.args)
    aisc_full_df = wsec.load_aisc_w_sections()
    current_indexes, prev_kwargs = _get_current_indexes()
    current_selection = aisc_full_df.iloc[current_indexes]
    current_selection = _apply_all_filters(current_selection, kwargs)
    prev_kwargs.update(kwargs)
    _set_current_indexes(list(current_selection.index), prev_kwargs)
    title = "AISC W-Sections: Current selection"
    subtitle = str(prev_kwargs)
    print(_table_output(current_selection, title=title, subtitle=subtitle))


def _apply_all_filters(current_selection: pd.DataFrame, kwargs: dict) -> None:
    """
    Returns None. Sets the indexes in the data store to the indexes remaining
    in the 'current_selection' once all of the filter terms in 'kwargs' have
    been applied.
    """
    for field, comparison_value in kwargs.items():
        current_selection = _apply_filter(current_selection, field, comparison_value)
    return current_selection


def _apply_filter(
        current_selection: pd.DataFrame, 
        field: str, 
        comparison_value: str
    ) -> pd.DataFrame:
    """
    Returns the indexes of the rows which pass the filter.

    'field' is one of the fields (column names) in the aisc db
    'comparison_value' is a str that may or may not contain both
    a numerical comparison operator (<, >, <=, >=, ==, !=) and a numerical
    value to compare against the records in the current rows of the
    aisc db
    """
    OPERATIONS = {
        "<": wsec.sections_less_than,
        "<=": wsec.sections_less_than_or_equal,
        ">": wsec.sections_greater_than,
        ">=": wsec.sections_greater_than,
    }
    operator, value = _parse_comparison_value(comparison_value)
    operation_function = OPERATIONS[operator]
    updated_selection = operation_function(current_selection, **{field: value})
    return updated_selection


def _parse_comparison_value(comparison_value: str) -> tuple[Optional[str], float]:
    """
    Returns a tuple containing a string of the comparison operator followed
    by the comparison value. If no comparison operator is present, then an
    empty string will occupy the first position of the tuple.

    Examples:
        _parse_comparison_value("<=234") # ("<=", 234.0)
        _parse_comparison_value("234") # (None, 234.0)
        _parse_comparison_value("==312") # ("==", 312.0)
    """
    comparison = ""
    value = ""
    OPERATORS = "<>=!"
    for char in comparison_value:
        if char in OPERATORS:
            comparison += char
        elif char.isnumeric():
            value += char
        else:
            raise ValueError(
                "The value passed as the comparison value is invalid. "
                "A valid value contains a comparison operator (<, >, <=, >=, !=, ==) "
                "followed by a number without any spaces. "
                f"\n'{comparison_value}' is invalid."
            )
    return comparison, float(value)


def _clear_data_store() -> None:
    """
    Removes all data in the data store file leaving an empty json file.
    """
    json_data = {"indexes": [], "filters": {}}
    with open(DATA_STORE_FILE, 'w') as file:
        json.dump(json_data, file)


def _set_current_indexes(indexes: list[int], filters: dict) -> None:
    """
    Stores the list of indexes into the data store file
    """
    json_data = {"indexes": indexes, "filters": filters}
    with open(DATA_STORE_FILE, 'w') as file:
        json.dump(json_data, file)


def _get_current_indexes() -> list[int]:
    """
    Returns the list of indexes currently in the data store.
    """
    with open(DATA_STORE_FILE, 'r') as file:
        json_data = json.load(file)
    return json_data['indexes'], json_data['filters']


def _create_table(
        df: pd.DataFrame,
        n_cols: Optional[int] = None,
        n_rows: Optional[int] = None,
        ) -> Table:
    """
    Returns a rich.table.Table representing the data in 'df'

    If the number of columns in 'df' is greater than 'n_cols', the last column
    will show "..."

    If the number of rows in 'df' is greater than 'n_rows', the last row will
    show "..."
    """
    table = Table()
    display_df = df.drop(['Type', 'W', 'kdes'], axis=1)
    # Columns
    column_names = display_df.columns
    if n_cols is not None and len(column_names) < n_cols:
        column_names = display_df.columns[:n_cols]
    table.add_column("index", justify="left")
    for column_name in display_df.columns[:n_cols]:
        table.add_column(column_name, justify="center")

    # Rows
    row_indexes = display_df.index
    if n_rows is not None and len(row_indexes) < n_rows:
        row_indexes = display_df.index[:n_rows]
    for record in display_df.itertuples():
        table.add_row(*[str(value) for value in record])

    return table


def _table_output(
        df: pd.DataFrame,
        n_cols: Optional[int] = None,
        n_rows: Optional[int] = None,
        title: Optional[str] = None,
        subtitle: Optional[str] = None,
        ) -> Panel:
    """
    Returns a rich.panel.Panel populated with a rich.table.Table
    containing the information within 'df'
    """
    panel = Panel(_create_table(df, n_cols, n_rows), title=title, subtitle=subtitle)
    return panel


def _parse_kwargs(extra_args: list[str]):
    kwargs = {}
    pair = []
    for idx, extra_arg in enumerate(extra_args):
        if idx % 2 == 0:
            pair.append(extra_arg)
        else:
            pair.append(extra_arg)
            kwargs.update({pair[0].replace("-",""): pair[1]})
            pair = []
    return kwargs

if __name__ == "__main__":
    app()