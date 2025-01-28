# ..\json_to_parquet.py
import os
import json
import pyarrow as pa
import pyarrow.parquet as pq

def load_entries(input_dir: str, filenames: list):
    for filename in filenames:
        filepath = os.path.join(input_dir, filename)
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                if filename.endswith('.json'):
                    return json.load(f)
                elif filename.endswith('.jsonl'):
                    return [json.loads(line) for line in f if line.strip()]
                else:
                    raise ValueError("Unsupported file format. Use .json or .jsonl.")
    raise FileNotFoundError(f"None of the files {filenames} exist in {input_dir}.")

def convert_to_parquet(entries: list, output_file: str):
    table = pa.Table.from_pylist(entries)
    pq.write_table(table, output_file)
    print(f"Data successfully written to {output_file}")

def main():
    input_dir = os.path.join(os.getcwd(), "1")
    filenames = ["training_data.json", "training_data.jsonl"]  # Check for both JSON and JSONL files
    output_dir = os.path.join(os.getcwd(), "1")
    output_file = None
    
    try:
        entries = load_entries(input_dir, filenames)
        for filename in filenames:
            if filename.endswith('.json') and os.path.exists(os.path.join(input_dir, filename)):
                output_file = os.path.join(output_dir, filename.replace('.json', '.parquet'))
            elif filename.endswith('.jsonl') and os.path.exists(os.path.join(input_dir, filename)):
                output_file = os.path.join(output_dir, filename.replace('.jsonl', '.parquet'))
    except Exception as e:
        print(f"Error loading entries: {e}")
        return
    
    if output_file:
        convert_to_parquet(entries, output_file)
    else:
        print("Error: No valid JSON or JSONL files found to convert.")

if __name__ == "__main__":
    main()
