import pandas as pd
import glob
import os

def merge_parquet_files(input_path, output_file):
    # Get all .pq files in the specified directory
    all_files = glob.glob(os.path.join(input_path, "*.pq"))
    
    # Sort the files to ensure consistent ordering
    all_files.sort()
    
    # List to hold all dataframes
    df_list = []
    
    # Read each parquet file and append to the list
    for filename in all_files:
        df = pd.read_parquet(filename)
        df_list.append(df)
        print(f"Read file: {filename}, shape: {df.shape}")
    
    # Concatenate all dataframes
    combined_df = pd.concat(df_list, ignore_index=True)
    
    # Remove any duplicate rows if they exist
    combined_df.drop_duplicates(inplace=True)
    
    # Save the combined dataframe to a new parquet file
    combined_df.to_parquet(output_file, index=False)
    
    print(f"\nCombined {len(all_files)} files.")
    print(f"Total rows in combined file: {combined_df.shape[0]}")
    print(f"Total columns in combined file: {combined_df.shape[1]}")
    print(f"Output saved to: {output_file}")

# Example usage
input_path = "./"  # Directory containing your .pq files
output_file = "combined_scenarios.pq"  # Name of the output file

merge_parquet_files(input_path, output_file)

# Optionally, verify the contents of the merged file
df_combined = pd.read_parquet(output_file)
print("\nContents of the merged file:")
print(df_combined.head())
print(f"\nColumns: {df_combined.columns.tolist()}")