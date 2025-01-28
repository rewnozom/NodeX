import os
import pandas as pd
from collections import defaultdict
from icecream import ic
from typing import List, Tuple, Dict
import hashlib
import json

def get_file_headers(file_path: str) -> Tuple[str, ...]:
    """Read the headers of a .xlsx or .csv file."""
    file_ext = os.path.splitext(file_path)[1].lower()
    ic(f"Reading headers from: {file_path}")

    try:
        if file_ext == '.xlsx':
            df = pd.read_excel(file_path, nrows=0)
        elif file_ext == '.csv':
            df = pd.read_csv(file_path, nrows=0)
        else:
            ic(f"Unsupported file format: {file_ext}")
            return tuple()

        headers = tuple(df.columns)
        ic(f"Headers found: {headers}")
        return headers
    except Exception as e:
        ic(f"Error reading file {file_path}: {str(e)}")
        return tuple()

def hash_headers(headers: Tuple[str, ...]) -> str:
    """Create a unique hash for the headers."""
    return hashlib.md5(''.join(headers).encode()).hexdigest()

def format_json_string(json_str: str) -> str:
    """Format a JSON string with proper indentation."""
    try:
        # Parse the JSON string
        parsed = json.loads(json_str)
        # Re-format with indentation
        return json.dumps(parsed, indent=2)
    except json.JSONDecodeError:
        ic(f"Invalid JSON string: {json_str}")
        return json_str  # Return original string if it's not valid JSON

def combine_files_by_headers(directory: str, output_directory: str):
    """Combine all files with matching headers into separate DataFrames and save them."""
    grouped_files: Dict[str, List[str]] = defaultdict(list)
    ic(f"Processing directory: {directory}")

    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
        ic(f"Created output directory: {output_directory}")

    for filename in os.listdir(directory):
        if filename.lower().endswith(('.xlsx', '.csv')) and not filename.startswith('~$'):
            file_path = os.path.join(directory, filename)
            headers = get_file_headers(file_path)
            if headers:
                header_hash = hash_headers(headers)
                grouped_files[header_hash].append((file_path, headers))
                ic(f"Added {filename} to group with hash {header_hash}")

    for header_hash, file_info_list in grouped_files.items():
        combined_df = pd.DataFrame()
        first_file_headers = file_info_list[0][1]  # Get headers from the first file in the group

        for file_path, headers in file_info_list:
            ic(f"Processing file: {file_path}")
            file_ext = os.path.splitext(file_path)[1].lower()

            try:
                if file_ext == '.xlsx':
                    df = pd.read_excel(file_path)
                elif file_ext == '.csv':
                    df = pd.read_csv(file_path)
                else:
                    ic(f"Skipping unsupported file: {file_path}")
                    continue

                # Ensure all columns from the first file are present
                for col in first_file_headers:
                    if col not in df.columns:
                        df[col] = None  # Add missing columns with None values

                # Select only the columns present in the first file
                df = df[list(first_file_headers)]

                # Format JSON in 'agent_response' column if it exists
                if 'agent_response' in df.columns:
                    df['agent_response'] = df['agent_response'].apply(format_json_string)

                combined_df = pd.concat([combined_df, df], ignore_index=True, sort=False)
                ic(f"Combined {file_path}, current shape: {combined_df.shape}")
            except Exception as e:
                ic(f"Error processing file {file_path}: {str(e)}")

        if not combined_df.empty:
            output_file_name = '_'.join(first_file_headers).replace(' ', '_').replace(':', '').replace('/', '_')[:200]  # Limit filename length
            output_file_name += f"_{header_hash[:8]}"  # Add part of hash to ensure uniqueness
            output_path_xlsx = os.path.join(output_directory, f"{output_file_name}.xlsx")
            output_path_csv = os.path.join(output_directory, f"{output_file_name}.csv")

            combined_df.to_excel(output_path_xlsx, index=False)
            combined_df.to_csv(output_path_csv, index=False, line_terminator='\n')

            ic(f"Created Excel file: {output_path_xlsx}")
            ic(f"Created CSV file: {output_path_csv}")
        else:
            ic(f"No data to save for group with hash {header_hash}")

if __name__ == "__main__":
    data_directory = "./llm_data"
    output_directory = "./combined"

    ic("Starting file merging process")
    combine_files_by_headers(data_directory, output_directory)
    ic("File merging process completed")