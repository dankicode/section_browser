
from typing import Optional
from dataclasses import dataclass
import json
import pathlib
import pandas as pd
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import print
import typer
import section_browser.w_sections as wsec

DATA_STORE_FILE = pathlib.Path(__file__).parents[0] / "DATA_STORE.json"
ROW_SELECTIONS: list[int] = []
DATA_STORE: dict = {}

APP_INTRO = typer.style("""
AISC sections database W-section selection tool (2023-05-28)
""", fg=typer.colors.BRIGHT_YELLOW, bold=True)

app = typer.Typer(
    add_completion=False, 
    no_args_is_help=True,
    help=APP_INTRO,
    )


@app.command(
    name="all", 
    short_help="Loads all AISC w-sections and applies filters",
    help="Starts with a new database and applies optional filters based on column names",
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
    loads = {}
    current_selection = _apply_all_filters(aisc_full_df, kwargs)
    _set_current_indexes(list(current_selection.index), kwargs, loads)
    print(
        _table_output(
            current_selection, 
            title="AISC W-Sections: Current selection", 
            filters=kwargs,
            loads=loads,
        )
    )


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
    current_indexes, prev_kwargs, loads = _get_current_indexes()
    current_selection = aisc_full_df.iloc[current_indexes]
    current_selection = _apply_all_filters(current_selection, kwargs)
    prev_kwargs.update(kwargs)
    _set_current_indexes(list(current_selection.index), prev_kwargs, loads)
    title = "AISC W-Sections: Current selection"
    subtitle = str(prev_kwargs)
    print(
        _table_output(
            current_selection, 
            title=title, 
            filters=prev_kwargs,
            loads=loads
        )
    )


@app.command(
    name="apply",
    short_help="Apply loads to sections: N, Vx, Vy, Mx, My, T (scale to N, N-mm)",
)
def apply_loads(
    n: Optional[float] = None,
    mx: Optional[float] = None,
    my: Optional[float] = None,
    vx: Optional[float] = None,
    vy: Optional[float] = None,
    t: Optional[float] = None,
    ) -> None:
    """
    Returns None, adds the loads supplied to the data store
    """
    actions = ["N", "Mx", "My", "Vx", "Vy", "T"]
    args = locals()
    loads = {}
    for action in actions:
        if args[action.lower()] is not None:
            loads[action] = args[action.lower()]
    indexes, filters, prev_loads = _get_current_indexes()
    aisc_full_df = wsec.load_aisc_w_sections()
    current_selection = aisc_full_df.iloc[indexes]
    _set_current_indexes(indexes, filters, loads)
    title = "AISC W-Sections: Current selection"
    print(
        _table_output(
            current_selection, 
            title=title, 
            filters=filters,
            loads=loads
        )
    )


@app.command(
    name="maxvm",
    short_help="Calculate maximum von Mises stress on selected sections resulting from applied loads",
)
def calculate_max_vm(subslice: str) -> None:
    """
    Returns None, calculates the max von Mises stress for the selected sections resulting from applied
    loads. 
    'sub_slice' is a str that represents a Python numeric index slice of rows, i.e. "start:stop:step" that,
    if present, will be applied to the selection prior to calculating the stress.
    """
    aisc_full_df = wsec.load_aisc_w_sections()
    current_indexes, filters, loads = _get_current_indexes()
    current_selection = aisc_full_df.iloc[current_indexes]
    parsed_slice = _parse_slice(subslice)
    print(parsed_slice)
    analysis_selection = current_selection.loc[parsed_slice]
    analyzed_selection = wsec.calculate_section_stresses(analysis_selection, fy=350, **loads)
    title = "AISC W-Sections: Current selection with analysis"
    print(
        _table_output(
            analyzed_selection, 
            title=title, 
            filters=filters,
            loads=loads
        )
    )
    

@app.command(
    name="status",
    short_help="Display the current selection",
)
def display_table() -> None:
    """
    Returns None, calculates the max von Mises stress for the selected sections resulting from applied
    loads. 
    'sub_slice' is a str that represents a Python numeric index slice of rows, i.e. "start:stop:step" that,
    if present, will be applied to the selection prior to calculating the stress.
    """
    aisc_full_df = wsec.load_aisc_w_sections()
    current_indexes, filters, loads = _get_current_indexes()
    current_selection = aisc_full_df.iloc[current_indexes]
    title = "AISC W-Sections: Current selection"
    print(
        _table_output(
            current_selection, 
            title=title, 
            filters=filters,
            loads=loads
        )
    )


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
        "@": wsec.sections_approx_equal,
        "==": wsec.sections_equal,
        "!=": wsec.sections_not_equal,
    }
    operator, value = _parse_comparison_value(comparison_value)
    operation_function = OPERATIONS[operator]
    updated_selection = operation_function(current_selection, **{field: value})
    return updated_selection


def _parse_comparison_value(comparison_value: str) -> tuple[str, float]:
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
    OPERATORS = "<>=!@"
    VALID_SYMBOLS = ".-eE"
    for char in comparison_value:
        if char in OPERATORS:
            comparison += char
        elif char.isnumeric() or char in VALID_SYMBOLS:
            value += char
        else:
            raise ValueError(
                "The value passed as the comparison value is invalid. "
                "A valid value contains a comparison operator (<, >, <=, >=, !=, ==) "
                "followed by a number without any spaces. "
                f"\n'{comparison_value}' is invalid."
            )
    return comparison, float(value)


def _parse_slice(slice_arg: str) -> slice:
    """
    Returns a tuple representing the components of a Python slice: start, stop, step.

    _parse_slice("2") # slice(2)
    _parse_slice("2:") # slice(2, None)
    """
    slice_components = slice_arg.split(":")
    if len(slice_components) == 1:
        start = int(slice_components[0])
        stop = start
        return slice(start, stop)
    elif len(slice_components) == 2:
        start, stop = None, None
        start_str, stop_str = slice_components
        if start_str.replace("-", "").isnumeric():
            start = int(start_str)
        if stop_str.replace("-", "").isnumeric():
            stop = int(stop_str)
        return slice(start, stop)
    elif len(slice_components) == 3:
        start, stop, step = None, None, None
        start_str, stop_str, step_str = slice_components
        if start_str.replace("-", "").isnumeric():
            start = int(start_str)
        if stop_str.replace("-", "").isnumeric():
            stop = int(stop_str)
        if step_str.replace("-", "").isnumeric():
            step = int(step_str)
        return slice(start, stop, step)
    else:
        raise ValueError(
            "The subslice argument must be a str in the form 'start[:stop[:step]].\n"
            f"A value of {slice_arg} is not valid."
        )


def _parse_kwargs(extra_args: list[str]):
    """
    Returns a dictionary representing the key, value pairs contained
    in 'extra_args' where 'extra_args' is an ordered stream of key, value
    pairs: [key1, value1, key2, value2, etc.]
    """
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


def _clear_data_store(path: pathlib.Path = DATA_STORE_FILE) -> None:
    """
    Removes all data in the data store file leaving an empty json file.
    """
    json_data = {"indexes": [], "filters": {}, "loads": {}}
    with open(path, 'w') as file:
        json.dump(json_data, file)


def _set_current_indexes(indexes: list[int], filters: dict, loads: dict, path: pathlib.Path = DATA_STORE_FILE) -> None:
    """
    Stores the list of indexes into the data store file
    """
    json_data = {"indexes": indexes, "filters": filters, "loads": loads}
    with open(path, 'w') as file:
        json.dump(json_data, file)


def _get_current_indexes(path: pathlib.Path = DATA_STORE_FILE) -> list[int]:
    """
    Returns the list of indexes currently in the data store.
    """
    with open(path, 'r') as file:
        json_data = json.load(file)
    return json_data['indexes'], json_data['filters'], json_data['loads']




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
    display_df = wsec.sort_by_weight(df.drop(['Type', 'kdes'], axis=1))
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
        filters: Optional[str] = None,
        loads: Optional[str] = None,
        ) -> Panel:
    """
    Returns a rich.panel.Panel populated with a rich.table.Table
    containing the information within 'df'
    """
    subtitle_filters = Text(f"{filters}")
    subtitle_loads = Text(f"{loads}", style="bold red")
    if subtitle_loads != "":
        subtitle = subtitle_filters + " | " + subtitle_loads 
    panel = Panel(
        _create_table(df, n_cols, n_rows), 
        title=title, 
        subtitle=subtitle
        )
    return panel

if __name__ == "__main__":
    app()