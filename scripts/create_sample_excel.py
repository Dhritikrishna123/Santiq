#!/usr/bin/env python3
"""Script to create sample Excel data for testing Excel plugins."""

import pandas as pd
from pathlib import Path

def create_sample_excel():
    """Create sample Excel file with test data."""
    
    # Create sample data
    data = pd.DataFrame({
        "id": [1, 2, 3, 4, 5],
        "name": ["Alice Johnson", "Bob Smith", "Charlie Brown", "Diana Prince", "Eve Wilson"],
        "email": [
            "alice.johnson@example.com",
            "bob.smith@example.com", 
            "charlie.brown@example.com",
            "diana.prince@example.com",
            "eve.wilson@example.com"
        ],
        "age": [28, 32, 25, 29, 31],
        "signup_date": ["2023-01-15", "2023-02-20", "2023-03-10", "2023-04-05", "2023-05-12"],
        "department": ["Engineering", "Marketing", "Sales", "Engineering", "HR"],
        "salary": [75000, 65000, 55000, 80000, 60000],
        "is_active": [True, True, False, True, True]
    })
    
    # Ensure output directory exists
    output_dir = Path("examples/sample_data")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create Excel file
    output_path = output_dir / "sample_data.xlsx"
    
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        # Write main data
        data.to_excel(writer, sheet_name='Sheet1', index=False)
        
        # Create a second sheet with different data
        summary_data = pd.DataFrame({
            "department": ["Engineering", "Marketing", "Sales", "HR"],
            "count": [2, 1, 1, 1],
            "avg_salary": [77500, 65000, 55000, 60000]
        })
        summary_data.to_excel(writer, sheet_name='Summary', index=False)
    
    print(f"Created sample Excel file: {output_path}")
    print(f"File size: {output_path.stat().st_size} bytes")
    print(f"Sheets: Sheet1 ({len(data)} rows), Summary ({len(summary_data)} rows)")

if __name__ == "__main__":
    create_sample_excel()
