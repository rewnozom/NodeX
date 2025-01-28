import os
import re
from openpyxl import Workbook
from openai import OpenAI

def read_system_prompt(filename='system_prompt.md'):
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        print(f"Warning: {filename} not found. Using default system message.")
        return "You are a helpful assistant that provides information in table format."

def parse_tables(text):
    tables = []
    current_table = []
    for line in text.split('\n'):
        if line.strip() == '---':
            if current_table:
                tables.append(current_table)
                current_table = []
        elif line.strip().startswith('|'):
            current_table.append([cell.strip() for cell in line.split('|')[1:-1]])
    if current_table:
        tables.append(current_table)
    return tables

def save_to_excel(tables):
    base_path = './auto_llm_data_'
    index = 1
    while os.path.exists(f'{base_path}{index:03d}.xlsx'):
        index += 1
    filename = f'{base_path}{index:03d}.xlsx'

    wb = Workbook()
    wb.remove(wb.active)  # Remove default sheet

    for i, table in enumerate(tables):
        ws = wb.create_sheet(title=f'Table {i+1}')
        for row in table:
            ws.append(row)

    wb.save(filename)
    print(f"Data saved to {filename}")

def process_llm_output(output):
    # Remove the code block markers if present
    output = re.sub(r'```python\n|```', '', output)
    
    # Parse the tables from the output
    tables = parse_tables(output)
    
    # Save the tables to an Excel file
    save_to_excel(tables)

# Set up the OpenAI client for LM Studio
client = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")

# Read the system prompt from file
system_message = read_system_prompt()

# Your user prompt
user_prompt = "Generate 5 examples of AI agent interactions in the specified table format."

# Make the API call
completion = client.chat.completions.create(
    model="AgentZero/AgentZero",  # Update this with the correct model name if different
    messages=[
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_prompt}
    ],
    temperature=0.7,
)

# Get the response content
response_content = completion.choices[0].message.content

# Process the LLM output
process_llm_output(response_content)