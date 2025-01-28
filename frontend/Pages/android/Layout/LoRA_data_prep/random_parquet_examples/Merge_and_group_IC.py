import os
import pandas as pd
from collections import defaultdict
from icecream import ic

def get_file_headers(file_path):
    """Read the headers of a .xlsx or .csv file."""
    file_ext = os.path.splitext(file_path)[1].lower()

    if file_ext == '.xlsx':
        df = pd.read_excel(file_path, nrows=0)
    elif file_ext == '.csv':
        df = pd.read_csv(file_path, nrows=0)
    else:
        ic(f"Unsupported file format: {file_ext}")
        return None

    headers = tuple(df.columns)
    ic(file_path, headers)
    return headers

def combine_files_by_headers(directory, output_directory):
    """Combine all files with matching headers into separate DataFrames and save them in a new directory."""
    grouped_files = defaultdict(list)

    # Ensure the output directory exists
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    # Group files by their headers
    for filename in os.listdir(directory):
        if filename.lower().endswith(('.xlsx', '.csv')) and not filename.startswith('~$'):
            file_path = os.path.join(directory, filename)
            headers = get_file_headers(file_path)
            if headers:
                grouped_files[headers].append(file_path)

    # Combine files with matching headers and save them as new files
    for headers, files in grouped_files.items():
        combined_df = pd.DataFrame()

        for file_path in files:
            file_ext = os.path.splitext(file_path)[1].lower()

            if file_ext == '.xlsx':
                df = pd.read_excel(file_path)
            elif file_ext == '.csv':
                df = pd.read_csv(file_path)
            else:
                continue

            ic(f"Combining file: {file_path}")
            # Concatenate the dataframes while ignoring index
            combined_df = pd.concat([combined_df, df], ignore_index=True, sort=False)

        # Define output path based on the headers
        output_file_name = '_'.join(headers).replace(' ', '_').replace(':', '').replace('/', '_')
        output_path_xlsx = os.path.join(output_directory, output_file_name + '.xlsx')
        output_path_csv = os.path.join(output_directory, output_file_name + '.csv')
        
        # Save combined DataFrame as .xlsx and .csv files
        combined_df.to_excel(output_path_xlsx, index=False)
        combined_df.to_csv(output_path_csv, index=False, line_terminator='\n')
        
        ic(f"Created Excel file: {output_path_xlsx}")
        ic(f"Created CSV file: {output_path_csv}")

if __name__ == "__main__":
    # Directory containing the files to process
    data_directory = "./llm_data"  # Update this path as per your directory structure
    
    # Directory to save the combined files
    output_directory = "./combined"  # Update this path as per your directory structure

    # Combine files with matching headers
    combine_files_by_headers(data_directory, output_directory)
