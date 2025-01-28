import pandas as pd
import os

# Specify the directory containing the .pq files
directory = './pq/'  # Adjust this path to where your files are located

# List all .pq files in the directory
parquet_files = [
    os.path.join(directory, f) for f in os.listdir(directory) if f.endswith('.pq')
]

# Iterate over each file and print the lengths of each column
for file in parquet_files:
    df = pd.read_parquet(file)
    
    print(f"\nFile: {file}")
    if 'prompt' in df.columns:
        print("prompt length:", len(df['prompt']))
    if 'agent_response' in df.columns:
        print("agent_response length:", len(df['agent_response']))
    if 'system_output' in df.columns:
        print("system_output length:", len(df['system_output']))
    if 'metadata' in df.columns:
        print("metadata length:", len(df['metadata']))

# You can also continue with the merging process after verifying the lengths
dataframes = [pd.read_parquet(file) for file in parquet_files]
combined_df = pd.concat(dataframes, ignore_index=True)

# Save the combined DataFrame to a new .pq file
combined_df.to_parquet('combined_finetuning.pq', engine='pyarrow', index=False)

print("All files have been successfully merged into 'combined_finetuning.pq'.")
