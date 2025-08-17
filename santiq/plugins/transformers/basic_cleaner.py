"""Basic data cleaning transformer plugin for Santiq.

This plugin provides fundamental data cleaning operations including null value
handling, duplicate removal, and data type conversions. It's designed to be
a starting point for data quality improvement workflows.
"""

from typing import Any, Dict, List

import pandas as pd

from santiq.plugins.base.transformer import TransformerPlugin, TransformResult


class BasicCleaner(TransformerPlugin):
    """Basic data cleaning transformer for Santiq.

    Performs fundamental data cleaning operations including null value removal,
    duplicate row elimination, and data type conversions. This transformer
    is designed to handle common data quality issues encountered in ETL workflows.

    Configuration Parameters:
        drop_nulls (bool|list): Whether to drop null values
            - True: Drop rows with nulls in any column
            - List: Drop rows with nulls in specific columns
        drop_duplicates (bool): Whether to remove duplicate rows
        duplicate_subset (list): Columns to consider for duplicate detection
        convert_types (dict): Type conversions for specific columns
            - "numeric": Convert to numeric (handles errors gracefully)
            - "datetime": Convert to datetime (handles errors gracefully)
            - "category": Convert to categorical type

    Example Configuration:
        {
            "drop_nulls": ["customer_id", "email"],
            "drop_duplicates": True,
            "duplicate_subset": ["customer_id"],
            "convert_types": {
                "age": "numeric",
                "signup_date": "datetime",
                "category": "category"
            }
        }
    """

    __plugin_name__ = "Basic Cleaner"
    __version__ = "0.1.0"
    __description__ = (
        "Basic data cleaning: drop nulls, remove duplicates, type conversions"
    )
    __api_version__ = "1.0"

    def transform(self, data: pd.DataFrame) -> TransformResult:
        """Apply basic cleaning transformations to the data.

        Processes the input DataFrame according to the configured cleaning
        operations and returns the cleaned data along with a record of
        applied fixes.

        Args:
            data: Input DataFrame to clean

        Returns:
            TransformResult containing cleaned data and applied fixes
        """
        cleaned_data = data.copy()
        applied_fixes = []

        # Drop nulls if configured
        if self.config.get("drop_nulls", False):
            initial_rows = len(cleaned_data)
            if isinstance(self.config["drop_nulls"], list):
                # Drop nulls from specific columns
                columns = self.config["drop_nulls"]
                cleaned_data = cleaned_data.dropna(subset=columns)
            else:
                # Drop nulls from any column
                cleaned_data = cleaned_data.dropna()

            rows_dropped = initial_rows - len(cleaned_data)
            if rows_dropped > 0:
                applied_fixes.append(
                    {
                        "fix_type": "drop_nulls",
                        "rows_affected": rows_dropped,
                        "description": f"Dropped {rows_dropped} rows with null values",
                    }
                )

        # Remove duplicates if configured
        if self.config.get("drop_duplicates", False):
            initial_rows = len(cleaned_data)
            subset = self.config.get("duplicate_subset")
            cleaned_data = cleaned_data.drop_duplicates(subset=subset)

            rows_dropped = initial_rows - len(cleaned_data)
            if rows_dropped > 0:
                applied_fixes.append(
                    {
                        "fix_type": "drop_duplicates",
                        "rows_affected": rows_dropped,
                        "description": f"Removed {rows_dropped} duplicate rows",
                    }
                )

        # Type conversions if configured
        type_conversions = self.config.get("convert_types", {})
        for column, target_type in type_conversions.items():
            if column in cleaned_data.columns:
                try:
                    if target_type == "numeric":
                        cleaned_data[column] = pd.to_numeric(
                            cleaned_data[column], errors="coerce"
                        )
                    elif target_type == "datetime":
                        cleaned_data[column] = pd.to_datetime(
                            cleaned_data[column], errors="coerce"
                        )
                    elif target_type == "category":
                        cleaned_data[column] = cleaned_data[column].astype("category")

                    applied_fixes.append(
                        {
                            "fix_type": "convert_type",
                            "column": column,
                            "target_type": target_type,
                            "description": f"Converted column '{column}' to {target_type}",
                        }
                    )
                except Exception as e:
                    # Log but don't fail the entire transformation
                    print(
                        f"Warning: Failed to convert column '{column}' to {target_type}: {e}"
                    )

        return TransformResult(cleaned_data, applied_fixes)

    def can_handle_issue(self, issue_type: str) -> bool:
        """Check if this transformer can handle specific issue types.

        Args:
            issue_type: Type of data quality issue

        Returns:
            True if the transformer can handle the issue type
        """
        return issue_type in ["null_values", "duplicate_rows", "type_mismatch"]

    def suggest_fixes(
        self, data: pd.DataFrame, issues: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Suggest fixes for detected issues.

        Analyzes the detected issues and provides configuration suggestions
        for the BasicCleaner transformer to resolve them.

        Args:
            data: DataFrame containing the data
            issues: List of detected data quality issues

        Returns:
            List of fix suggestions with configuration details
        """
        suggestions = []

        for issue in issues:
            if issue["type"] == "null_values":
                suggestions.append(
                    {
                        "fix_type": "drop_nulls",
                        "column": issue["column"],
                        "config": {"drop_nulls": [issue["column"]]},
                        "description": f"Drop null values from column '{issue['column']}'",
                        "impact": f"Will remove {issue['count']} rows",
                    }
                )

            elif issue["type"] == "duplicate_rows":
                suggestions.append(
                    {
                        "fix_type": "drop_duplicates",
                        "config": {"drop_duplicates": True},
                        "description": "Remove duplicate rows",
                        "impact": f"Will remove {issue['count']} duplicate rows",
                    }
                )

            elif issue["type"] == "type_mismatch":
                suggestions.append(
                    {
                        "fix_type": "convert_type",
                        "column": issue["column"],
                        "config": {
                            "convert_types": {issue["column"]: issue["suggested_type"]}
                        },
                        "description": f"Convert column '{issue['column']}' to {issue['suggested_type']}",
                        "impact": "May improve performance and enable type-specific operations",
                    }
                )

        return suggestions
