"""Basic data profiling plugin for Santiq.

This plugin performs fundamental data quality analysis including null value detection,
duplicate row identification, and data type analysis. It provides actionable insights
and fix suggestions for common data quality issues.
"""

from typing import Any, Dict, List

import pandas as pd

from santiq.plugins.base.profiler import ProfileResult, ProfilerPlugin


class BasicProfiler(ProfilerPlugin):
    """Basic data profiler plugin for Santiq.

    Performs comprehensive data quality analysis to identify common issues
    such as null values, duplicate rows, and type mismatches. Provides
    detailed statistics and actionable fix suggestions.

    Detected Issues:
        - null_values: Missing data in columns with severity levels
        - duplicate_rows: Duplicate records in the dataset
        - type_mismatch: Columns that could benefit from type conversion

    Output Summary:
        - total_rows: Total number of rows in the dataset
        - total_columns: Total number of columns
        - null_percentage: Overall percentage of null values
        - duplicate_rows: Count of duplicate rows
        - memory_usage_mb: Estimated memory usage in MB
    """

    __plugin_name__ = "Basic Profiler"
    __version__ = "0.1.0"
    __description__ = "Performs basic profiling on data"
    __api_version__ = "1.0"

    def profile(self, data: pd.DataFrame) -> ProfileResult:
        """Profile the data for basic quality issues.

        Analyzes the input DataFrame for common data quality problems
        and generates a comprehensive report with issues, statistics,
        and fix suggestions.

        Args:
            data: DataFrame to profile

        Returns:
            ProfileResult containing issues, summary, and suggestions
        """
        issues = []
        suggestions = []

        # Check for null values
        null_counts = data.isnull().sum()
        for column, null_count in null_counts.items():
            if null_count > 0:
                null_percentage = (null_count / len(data)) * 100

                # Determine severity based on null percentage
                if null_percentage > 50:
                    severity = "high"
                elif null_percentage > 10:
                    severity = "medium"
                else:
                    severity = "low"

                issues.append(
                    {
                        "type": "null_values",
                        "column": column,
                        "count": int(null_count),
                        "percentage": round(null_percentage, 2),
                        "severity": severity,
                    }
                )

                suggestions.append(
                    {
                        "fix_type": "drop_nulls",
                        "column": column,
                        "description": f"Drop {null_count} null values from column {column}",
                        "impact": f"Will remove {null_count} rows ({null_percentage:.1f}%)",
                    }
                )

        # Check for duplicate rows
        duplicate_count = data.duplicated().sum()
        if duplicate_count > 0:
            duplicate_percentage = (duplicate_count / len(data)) * 100
            issues.append(
                {
                    "type": "duplicate_rows",
                    "count": int(duplicate_count),
                    "percentage": round(duplicate_percentage, 2),
                    "severity": "medium",
                }
            )

            suggestions.append(
                {
                    "fix_type": "drop_duplicates",
                    "description": f"Remove {duplicate_count} duplicate rows",
                    "impact": f"Will remove {duplicate_count} rows ({duplicate_percentage:.1f}%)",
                }
            )

        # Check for data type mismatches
        for column in data.columns:
            if data[column].dtype == "object":
                # Check if object column could be numeric
                try:
                    pd.to_numeric(data[column].dropna(), errors="raise")
                    issues.append(
                        {
                            "type": "type_mismatch",
                            "column": column,
                            "current_type": "object",
                            "suggested_type": "numeric",
                            "severity": "low",
                        }
                    )

                    suggestions.append(
                        {
                            "fix_type": "convert_type",
                            "column": column,
                            "target_type": "numeric",
                            "description": f"Convert column '{column}' to numeric type",
                            "impact": "May improve performance and enable numeric operations",
                        }
                    )
                except (ValueError, TypeError):
                    # Column contains non-numeric data, skip
                    pass

        # Generate comprehensive summary
        summary = {
            "total_rows": len(data),
            "total_columns": len(data.columns),
            "null_percentage": round((data.isnull().sum().sum() / data.size) * 100, 2),
            "duplicate_rows": int(duplicate_count),
            "memory_usage_mb": round(
                data.memory_usage(deep=True).sum() / 1024 / 1024, 2
            ),
        }

        return ProfileResult(issues, summary, suggestions)
