import os
import sys

import pytest

sys.path.append(os.path.join(os.path.dirname(__file__), "../../src"))

from slashgpt.manifest import Manifest  # noqa: E402


@pytest.fixture
def manifest_none():
    manifest_data = {
        "title": "Function Test",
    }
    return Manifest(manifest_data, "./", "ai-agent")


@pytest.fixture
def manifest_string():
    manifest_data = {
        "title": "Function Test",
        "functions": "./resources/functions/graphql.json",
    }
    return Manifest(manifest_data, ".", "ai-agent")


@pytest.fixture
def manifest_list():
    manifest_data = {
        "title": "Function Test",
        "functions": [
            {
                "name": "visit_web",
                "description": "Visit web page",
            }
        ],
    }
    return Manifest(manifest_data, "", "ai-agent")


def test_title(manifest_string):
    assert manifest_string.title() == "Function Test"


def test_function_none(manifest_none):
    assert manifest_none.functions() is None


def test_function_string(manifest_string):
    assert isinstance(manifest_string.functions(), list)


def test_function_list(manifest_list):
    assert isinstance(manifest_list.functions(), list)
