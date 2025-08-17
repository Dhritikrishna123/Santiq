"""Utility functions for data processing."""

import tempfile
from pathlib import Path
from typing import Optional

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq


class DataManager:
    """Manages data storage and retrieval for pipeline execution."""

    def __init__(
        self, temp_dir: Optional[Path] = None, memory_threshold_mb: int = 100
    ) -> None:
        self.temp_dir = temp_dir or Path(tempfile.gettempdir())
        self.memory_threshold_mb = memory_threshold_mb
        self._temp_files: list[Path] = []

    def should_use_disk(self, data: pd.DataFrame) -> bool:
        """Determine if data should be stored on disk vs memory."""
        memory_usage_mb = float(data.memory_usage(deep=True).sum()) / 1024 / 1024
        return memory_usage_mb > self.memory_threshold_mb

    def save_temp_data(self, data: pd.DataFrame, name: str) -> Path:
        """Save data to temporary file and return path."""
        temp_file = (
            self.temp_dir
            / f"{name}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.parquet"
        )

        # Use Parquet for efficient storage
        table = pa.Table.from_pandas(data)
        pq.write_table(table, temp_file)

        self._temp_files.append(temp_file)
        return temp_file

    def load_temp_data(self, path: Path) -> pd.DataFrame:
        """Load data from temporary file."""
        table = pq.read_table(path)
        return table.to_pandas()

    def cleanup(self) -> None:
        """Clean up all temporary files."""
        for temp_file in self._temp_files:
            if temp_file.exists():
                temp_file.unlink()
        self._temp_files.clear()


def validate_dataframe_schema(
    data: pd.DataFrame, expected_schema: Optional[dict[str, str]] = None
) -> list[str]:
    """Validate DataFrame against expected schema."""
    issues = []

    if expected_schema:
        expected_columns = set(expected_schema.keys())
        actual_columns = set(data.columns)

        missing_columns = expected_columns - actual_columns
        extra_columns = actual_columns - expected_columns

        if missing_columns:
            issues.append(f"Missing expected columns: {', '.join(missing_columns)}")

        if extra_columns:
            issues.append(f"Unexpected columns found: {', '.join(extra_columns)}")

        # Check data types for common columns
        for column in expected_columns & actual_columns:
            expected_type = expected_schema[column]
            actual_type = str(data[column].dtype)

            if not _types_compatible(actual_type, expected_type):
                issues.append(
                    f"Column '{column}' type mismatch: expected {expected_type}, got {actual_type}"
                )

    return issues


def _types_compatible(actual: str, expected: str) -> bool:
    """Check if actual data type is compatible with expected type."""
    type_mappings = {
        "int": ["int64", "int32", "Int64"],
        "float": ["float64", "float32"],
        "string": ["object", "string"],
        "datetime": ["datetime64[ns]", "datetime64"],
        "bool": ["bool", "boolean"],
    }

    for expected_family, compatible_types in type_mappings.items():
        if expected == expected_family and actual in compatible_types:
            return True

    return actual == expected
