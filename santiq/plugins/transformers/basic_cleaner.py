"""basic data cleaning transformer"""

from typing import Any, Dict, List

import pandas as pd

from santiq.plugins.base.transformer import TransformerPlugin, TransformResult


class BasicCleaner(TransformerPlugin):
    """Perform basic data cleaning operations"""
    __plugin_name__ = "Basic Cleaner"
    __version__ = "0.1.0"
    __description__ = "Basic data cleaning: drop nulls, remove duplicates, type conversions"
    __api_version__ = "1.0"
    
    def transform(self, data: pd.DataFrame) -> TransformResult:
        """Apply basic cleaning transformations"""
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
                applied_fixes.append({
                    "fix_type": "drop_nulls",
                    "rows_affected": rows_dropped,
                    "description": f"Dropped {rows_dropped} rows with null values"
                })
        
        # Remove duplicates if configured
        if self.config.get("drop_duplicates", False):
            initial_rows = len(cleaned_data)
            subset = self.config.get("duplicate_subset")
            cleaned_data = cleaned_data.drop_duplicates(subset=subset)
            
            rows_dropped = initial_rows - len(cleaned_data)
            if rows_dropped > 0:
                applied_fixes.append({
                    "fix_type": "drop_duplicates",
                    "rows_affected": rows_dropped,
                    "description": f"Removed {rows_dropped} duplicate rows"
                })
        
        # Type conversions if configured
        type_conversions = self.config.get("convert_types", {})
        for column, target_type in type_conversions.items():
            if column in cleaned_data.columns:
                try:
                    if target_type == "numeric":
                        cleaned_data[column] = pd.to_numeric(cleaned_data[column], errors='coerce')
                    elif target_type == "datetime":
                        cleaned_data[column] = pd.to_datetime(cleaned_data[column], errors='coerce')
                    elif target_type == "category":
                        cleaned_data[column] = cleaned_data[column].astype('category')
                    
                    applied_fixes.append({
                        "fix_type": "convert_type",
                        "column": column,
                        "target_type": target_type,
                        "description": f"Converted column '{column}' to {target_type}"
                    })
                except Exception as e:
                    # Log but don't fail the entire transformation
                    print(f"Warning: Failed to convert column '{column}' to {target_type}: {e}")
        
        return TransformResult(cleaned_data, applied_fixes)
    
    def can_handle_issue(self, issue_type: str) -> bool:
        """Check if this transformer can handle specific issue types."""
        return issue_type in ["null_values", "duplicate_rows", "type_mismatch"]
    
    def suggest_fixes(self, data: pd.DataFrame, issues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Suggest fixes for detected issues."""
        suggestions = []
        
        for issue in issues:
            if issue["type"] == "null_values":
                suggestions.append({
                    "fix_type": "drop_nulls",
                    "column": issue["column"],
                    "config": {"drop_nulls": [issue["column"]]},
                    "description": f"Drop null values from column '{issue['column']}'",
                    "impact": f"Will remove {issue['count']} rows"
                })
            
            elif issue["type"] == "duplicate_rows":
                suggestions.append({
                    "fix_type": "drop_duplicates",
                    "config": {"drop_duplicates": True},
                    "description": "Remove duplicate rows",
                    "impact": f"Will remove {issue['count']} duplicate rows"
                })
            
            elif issue["type"] == "type_mismatch":
                suggestions.append({
                    "fix_type": "convert_type",
                    "column": issue["column"],
                    "config": {
                        "convert_types": {
                            issue["column"]: issue["suggested_type"]
                        }
                    },
                    "description": f"Convert column '{issue['column']}' to {issue['suggested_type']}",
                    "impact": "May improve performance and enable type-specific operations"
                })
        
        return suggestions