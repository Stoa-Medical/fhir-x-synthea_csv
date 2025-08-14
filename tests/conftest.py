from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Callable, Dict, List

import pytest


@pytest.fixture(scope="session")
def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def tests_dir(project_root: Path) -> Path:
    return project_root / "tests"


@pytest.fixture(scope="session")
def data_dir(tests_dir: Path) -> Path:
    return tests_dir / "data"


@pytest.fixture(scope="session")
def fhir_data_dir(data_dir: Path) -> Path:
    return data_dir / "fhir"


@pytest.fixture(scope="session")
def csv_data_dir(data_dir: Path) -> Path:
    return data_dir / "csv"


@pytest.fixture(scope="session")
def fhir_bundle_paths(fhir_data_dir: Path) -> List[Path]:
    return sorted(fhir_data_dir.glob("*.json"))


@pytest.fixture(scope="session")
def example_fhir_bundle_path(fhir_bundle_paths: List[Path]) -> Path | None:
    return fhir_bundle_paths[0] if fhir_bundle_paths else None


@pytest.fixture
def read_json() -> Callable[[Path | str], Dict[str, Any]]:
    def _read_json(path: Path | str) -> Dict[str, Any]:
        p = Path(path)
        with p.open("r", encoding="utf-8") as f:
            return json.load(f)

    return _read_json


@pytest.fixture
def read_csv() -> Callable[[Path | str], List[Dict[str, str]]]:
    def _read_csv(path: Path | str) -> List[Dict[str, str]]:
        p = Path(path)
        with p.open("r", encoding="utf-8", newline="") as f:
            return list(csv.DictReader(f))

    return _read_csv
