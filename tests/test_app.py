import pathlib
import json
from section_browser import main

TEST_DATA_STORE_FILE = pathlib.Path(__file__).parents[0] / "TEST_DATA_STORE.json"


def test_parse_kwargs():
    assert main._parse_kwargs(["1", "2", "3", "4"]) == {"1": "2", "3": "4"}
    assert main._parse_kwargs(["--d", "<=304", "--Ix", ">503"]) == {
        "d": "<=304",
        "Ix": ">503",
    }


def test_clear_data_store():
    main._clear_data_store(TEST_DATA_STORE_FILE)
    with open(TEST_DATA_STORE_FILE, "r") as test_file:
        test_data = json.load(test_file)
    assert test_data == {"indexes": [], "filters": {}, "loads": {}}


def test_set_current_indexes():
    main._set_current_indexes(
        [1, 2, 3], {"B": "cat"}, {"C": "scarf"}, TEST_DATA_STORE_FILE
    )
    with open(TEST_DATA_STORE_FILE, "r") as test_file:
        test_data = json.load(test_file)
    assert test_data == {
        "indexes": [1, 2, 3],
        "filters": {"B": "cat"},
        "loads": {"C": "scarf"},
    }


def test_get_current_indexes():
    test_data = main._get_current_indexes(TEST_DATA_STORE_FILE)
    assert test_data == ([1, 2, 3], {"B": "cat"}, {"C": "scarf"})


def test_parse_slice():
    slice0 = "0"
    slice1 = "0:1"
    slice2 = "0:5:2"
    slice3 = "-1:4:-1"
    assert main._parse_slice(slice0) == slice(0, 0, None)
    assert main._parse_slice(slice1) == slice(0, 1, None)
    assert main._parse_slice(slice2) == slice(0, 5, 2)
    assert main._parse_slice(slice3) == slice(-1, 4, -1)


def test_parse_comparison_value():
    cv0 = "<234"
    cv1 = ">93.0"
    cv2 = "~=34.5"
    cv3 = "@43.5e6"
    assert main._parse_comparison_value(cv0) == ("<", 234.0)
    assert main._parse_comparison_value(cv1) == (">", 93.0)
    assert main._parse_comparison_value(cv2) == ("~=", 34.5)
    assert main._parse_comparison_value(cv3) == ("@", 43.5e6)
