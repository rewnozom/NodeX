import os
import pyarrow.parquet as pq
import json
import numpy as np

input_path = r't'
output_path = r''

# Ensure the output directory exists
if not os.path.exists(output_path):
    os.makedirs(output_path)

# Iterate over all files in the input directory
for filename in os.listdir(input_path):
    if filename.endswith('.parquet'):
        # Construct the full file paths
        input_file = os.path.join(input_path, filename)
        output_file = os.path.join(output_path, filename.replace('.parquet', '.json'))
        
        # Check if the output file already exists
        if not os.path.exists(output_file):
            # Read the Parquet file
            table = pq.read_table(input_file)
            
            # Initialize an empty list to hold the JSON objects
            json_objects = []
            
            # Iterate through the rows of the table
            for row in table.to_pandas().iterrows():
                # Convert each row to a dictionary
                row_dict = row[1].to_dict()
                
                # Convert NumPy arrays to lists
                for key, value in row_dict.items():
                    if isinstance(value, np.ndarray):
                        row_dict[key] = value.tolist()
                
                # Append the dictionary to the list
                json_objects.append(row_dict)
            
            # Convert the list of dictionaries to a JSON string
            json_data = json.dumps(json_objects, indent=4)
            
            # Write the JSON data to a file
            with open(output_file, 'w') as f:
                f.write(json_data)
                
            print(f'Converted {filename} to JSON.')
        else:
            print(f'Skipped {filename} as JSON already exists.')
