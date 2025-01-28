import pandas as pd
import os

# Specify the directory containing the .pq files
directory = './pq/'  # Adjust this path to where your files are located

# List all .pq files in the directory
parquet_files = [
    os.path.join(directory, f) for f in os.listdir(directory) if f.endswith('.pq')
]

# Initialize a list to hold all dataframes
dataframes = []

# Load each Parquet file, and verify columns are consistent
for file in parquet_files:
    df = pd.read_parquet(file)
    print(f"File: {file}, Columns: {df.columns.tolist()}, Shape: {df.shape}")
    dataframes.append(df)

# Concatenate all the DataFrames
combined_df = pd.concat(dataframes, ignore_index=True)

# Save the combined DataFrame to a new .pq file
combined_df.to_parquet('combined_finetuning.pq', engine='pyarrow', index=False)

print(f"All files have been successfully merged into 'combined_finetuning.pq'. Size: {os.path.getsize('combined_finetuning.pq')} bytes")
