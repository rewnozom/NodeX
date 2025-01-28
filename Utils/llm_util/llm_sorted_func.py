# ./shared/src/llm_util/llm_sorted_func.py

import os
import re
import logging
import time
from typing import List, Tuple, Optional, Callable

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Directories (can be parameterized if needed)
DEFAULT_INPUT_DIR = './Sorted_func_markz/'
DEFAULT_OUTPUT_DIR = './llm_sorted_func/'

def get_md_files(directory: str) -> List[str]:
    """Retrieve all .md files in the specified directory."""
    md_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.md'):
                md_files.append(os.path.join(root, file))
    logging.info(f"Found {len(md_files)} Markdown files in {directory}.")
    return md_files

def parse_markdown_functions(file_path: str) -> List[Tuple[str, str]]:
    """
    Parse a Markdown file and extract Python function definitions.
    
    Args:
        file_path (str): Path to the Markdown file.
    
    Returns:
        List[Tuple[str, str]]: A list of tuples containing function names and their code.
    """
    functions = []
    in_code_block = False
    code_lines = []

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.rstrip()
                # Check for start of Python code block
                if line.startswith('```python'):
                    in_code_block = True
                    code_lines = []
                    continue
                # Check for end of code block
                if line.startswith('```') and in_code_block:
                    in_code_block = False
                    code_text = '\n'.join(code_lines)
                    # Extract function name using regex
                    func_match = re.search(r'def\s+(\w+)\s*\(', code_text)
                    if func_match:
                        func_name = func_match.group(1)
                        func_code = code_text.strip()
                        functions.append((func_name, func_code))
                    continue
                # Collect code lines within the code block
                if in_code_block:
                    code_lines.append(line)
        logging.info(f"Extracted {len(functions)} functions from {file_path}.")
        return functions
    except Exception as e:
        logging.error(f"Failed to parse Markdown file {file_path}: {e}")
        return []

def load_system_prompt(prompt_content: str) -> str:
    """
    Load the system prompt content.
    
    Args:
        prompt_content (str): The system prompt content as a string.
    
    Returns:
        str: The trimmed system prompt.
    """
    return prompt_content.strip()

def get_function_description(function_code: str, system_prompt: str, llm, retries: int = 3) -> str:
    """
    Send the function code to the LLM and get a one-sentence description, with retry logic.
    
    Args:
        function_code (str): The code of the function.
        system_prompt (str): The system prompt to initialize the LLM.
        llm: The Langchain LLM model object.
        retries (int): Number of retry attempts in case of failure.
    
    Returns:
        str: The description returned by the LLM.
    """
    user_message = function_code

    for attempt in range(retries):
        try:
            # Construct messages as per Langchain's expectations
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]
            # Get the response from the LLM
            response = llm(messages)
            
            # Extract the content from the response
            if hasattr(response, 'content'):
                description = response.content.strip()
            elif isinstance(response, str):
                description = response.strip()
            else:
                description = str(response).strip()
            
            if not description:
                raise ValueError("Received empty response from LLM")
            
            logging.info(f"Received description for function.")
            return description
        except Exception as e:
            logging.error(f"Attempt {attempt + 1} failed to get description: {e}")
            time.sleep(2 ** attempt)  # Exponential backoff
    logging.error("Failed to get description after multiple attempts.")
    return ""

def format_output(function_name: str, description: str, function_code: str) -> str:
    """
    Format the output in the specified markdown format.
    
    Args:
        function_name (str): Name of the function.
        description (str): Description of the function.
        function_code (str): The function's code.
    
    Returns:
        str: The formatted markdown string.
    """
    output_lines = [
        "## New Module (Single Responsibility)",
        "> ### 1. Function",
        f"> * **Logic description**: - `{function_name}`: {description}",
        ">   ```python"
    ]
    # Add code lines, each prefixed with '>   '
    code_lines = function_code.split('\n')
    output_lines.extend([f">   {line}" for line in code_lines])
    output_lines.append(">   ```")
    output = '\n'.join(output_lines)
    return output

def process_function(function_name: str, function_code: str, system_prompt: str, llm, 
                    progress_callback: Optional[Callable[[str, str], None]] = None) -> Optional[Tuple[str, str]]:
    """
    Process a single function: get description and format the output.
    
    Args:
        function_name (str): Name of the function.
        function_code (str): The function's code.
        system_prompt (str): The system prompt for the LLM.
        llm: The Langchain LLM model object.
        progress_callback (Callable, optional): Function to call with updates (e.g., function name and status).
    
    Returns:
        Optional[Tuple[str, str]]: Tuple of function name and formatted output, or None if failed.
    """
    description = get_function_description(function_code, system_prompt, llm)
    if not description:
        logging.warning(f"Skipping function '{function_name}' due to missing description.")
        if progress_callback:
            progress_callback(function_name, "Skipped due to error")
        return None
    output = format_output(function_name, description, function_code)
    if progress_callback:
        progress_callback(function_name, "Processed")
    return (function_name, output)

def process_file(file_path: str, system_prompt: str, llm, output_dir: str = DEFAULT_OUTPUT_DIR, 
                progress_callback: Optional[Callable[[str, str], None]] = None) -> bool:
    """
    Process a single Markdown file: parse functions, get descriptions, and save results.
    
    Args:
        file_path (str): Path to the Markdown file.
        system_prompt (str): The system prompt for the LLM.
        llm: The Langchain LLM model object.
        output_dir (str): Directory to save the processed outputs.
        progress_callback (Callable, optional): Function to call with updates (e.g., function name and status).
    
    Returns:
        bool: True if processing was successful, False otherwise.
    """
    logging.info(f"Processing file: {file_path}")
    functions = parse_markdown_functions(file_path)
    
    output_content = []
    for function_name, function_code in functions:
        result = process_function(function_name, function_code, system_prompt, llm, progress_callback)
        if result:
            _, function_output = result
            output_content.append(function_output)
    
    # Save all processed functions for this file
    if output_content:
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            logging.info(f"Created output directory: {output_dir}")
        
        output_file = os.path.join(output_dir, os.path.basename(file_path))
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write('\n\n'.join(output_content))
            logging.info(f"Saved processed functions to {output_file}")
            if progress_callback:
                progress_callback(os.path.basename(file_path), "Saved")
        except Exception as e:
            logging.error(f"Failed to save processed functions to {output_file}: {e}")
            if progress_callback:
                progress_callback(os.path.basename(file_path), f"Error: {e}")
            return False
    
    return True

def process_files(input_dir: str = DEFAULT_INPUT_DIR, output_dir: str = DEFAULT_OUTPUT_DIR, 
                 system_prompt: str = "", llm = None, 
                 progress_callback: Optional[Callable[[str, str], None]] = None) -> None:
    """
    Process all Markdown files in the input directory.
    
    Args:
        input_dir (str): Directory containing input Markdown files.
        output_dir (str): Directory to save processed outputs.
        system_prompt (str): The system prompt for the LLM.
        llm: The Langchain LLM model object.
        progress_callback (Callable, optional): Function to call with updates.
    """
    if not system_prompt:
        logging.error("System prompt is empty. Aborting processing.")
        if progress_callback:
            progress_callback("System Prompt", "Error: Empty")
        return
    
    if llm is None:
        logging.error("LLM model is not provided. Aborting processing.")
        if progress_callback:
            progress_callback("LLM Model", "Error: Not provided")
        return
    
    md_files = get_md_files(input_dir)
    
    for md_file in md_files:
        success = process_file(md_file, system_prompt, llm, output_dir, progress_callback)
        if not success:
            logging.warning(f"Processing failed for file: {md_file}")
            if progress_callback:
                progress_callback(md_file, "Failed")
    
    logging.info("Completed processing all files.")
    if progress_callback:
        progress_callback("All Files", "Completed")
