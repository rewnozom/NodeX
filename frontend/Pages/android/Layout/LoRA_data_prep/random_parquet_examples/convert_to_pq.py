import os
import pandas as pd
from docx import Document
import pyarrow as pa
import pyarrow.parquet as pq

def read_docx(file_path):
    """Reads a .docx file and returns a pandas DataFrame based on detected table headers."""
    doc = Document(file_path)
    
    data = {}
    table = doc.tables[0]
    
    # Get headers from the first row
    headers = [cell.text.strip() for cell in table.rows[0].cells]
    for header in headers:
        data[header] = []
    
    # Fill data according to headers
    for row in table.rows[1:]:
        for idx, header in enumerate(headers):
            data[header].append(row.cells[idx].text.strip())
    
    return pd.DataFrame(data)

def convert_file_to_parquet(file_path):
    """Converts a .xlsx, .csv, or .docx file to a .pq file based on detected columns."""
    file_ext = os.path.splitext(file_path)[1].lower()
    
    if file_ext == '.xlsx':
        df = pd.read_excel(file_path)
    elif file_ext == '.csv':
        df = pd.read_csv(file_path)
    elif file_ext == '.docx':
        df = read_docx(file_path)
    else:
        print(f"Unsupported file format: {file_ext}")
        return
    
    # Define output path
    output_path = os.path.splitext(file_path)[0] + '.pq'
    
    # Convert to Parquet
    table = pa.Table.from_pandas(df)
    pq.write_table(table, output_path)
    print(f"Converted {file_path} to {output_path}")

def convert_directory(directory):
    """Converts all .xlsx, .csv, and .docx files in a directory to .pq."""
    for filename in os.listdir(directory):
        if filename.lower().endswith(('.xlsx', '.csv', '.docx')):
            file_path = os.path.join(directory, filename)
            convert_file_to_parquet(file_path)

if __name__ == "__main__":
    # Directory containing the files to convert
    data_directory = "./llm_data"
    
    # Convert all files in the directory
    convert_directory(data_directory)
