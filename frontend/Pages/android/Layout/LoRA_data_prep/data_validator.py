# ..\data_validator.py
import os
import json

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

def validate_entries(entries: list):
    valid_count = 0
    invalid_count = 0
    for entry in entries:
        # Basic validation: check if 'code' key is present and non-empty
        if isinstance(entry, dict) and entry.get('code'):
            valid_count += 1
        else:
            invalid_count += 1
    return valid_count, invalid_count

def main():
    input_dir = os.path.join(os.getcwd(), "1")
    filenames = ["training_data.json", "training_data.jsonl"]  # Check for both JSON and JSONL files
    try:
        entries = load_entries(input_dir, filenames)
    except Exception as e:
        print(f"Error loading entries: {e}")
        return
    
    valid, invalid = validate_entries(entries)
    total = valid + invalid
    print(f"Total entries: {total}")
    print(f"Valid entries: {valid}")
    print(f"Invalid entries: {invalid}")

if __name__ == "__main__":
    main()
