import pandas as pd

# Load the Parquet file
file_path = './combined_finetuning.pq'  # Update this path to the location of your file
df = pd.read_parquet(file_path)

# Check the length of each column
column_lengths = {
    'prompt': len(df['prompt']) if 'prompt' in df.columns else None,
    'agent_response': len(df['agent_response']) if 'agent_response' in df.columns else None,
    'system_output': len(df['system_output']) if 'system_output' in df.columns else None,
    'metadata': len(df['metadata']) if 'metadata' in df.columns else None
}

print(column_lengths)
