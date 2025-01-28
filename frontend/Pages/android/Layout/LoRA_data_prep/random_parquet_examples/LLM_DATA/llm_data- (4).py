import pandas as pd

# Example data for the conversation log with a focus on different tasks and scenarios
data = {
    'prompt': [
        "Create a zip archive named 'archive.zip' containing multiple text files.",
        "Create the zip archive named 'archive.zip' containing the created text files.",
        "Install the zip package since it was not found.",
        "Confirm the installation of the zip package.",
        "Retry creating the zip archive now that the zip package is installed."
    ],
    'agent_response': [
        """
        {
            "thoughts": [
                "The user has requested creating a zip archive named 'archive.zip' containing multiple text files.",
                "I will use the code_execution_tool to execute a terminal command to create the zip archive.",
                "First, I need to create the text files to be included in the archive."
            ],
            "tool_name": "code_execution_tool",
            "tool_args": {
                "runtime": "terminal",
                "code": "touch file1.txt file2.txt file3.txt"
            }
        }
        """,
        """
        {
            "thoughts": [
                "Now that the text files have been created, I will proceed to create the zip archive.",
                "I will use the code_execution_tool to execute a terminal command to zip the files."
            ],
            "tool_name": "code_execution_tool",
            "tool_args": {
                "runtime": "terminal",
                "code": "zip archive.zip file1.txt file2.txt file3.txt"
            }
        }
        """,
        """
        {
            "thoughts": [
                "The terminal command to create the zip archive failed because the 'zip' command is not found.",
                "I need to install the 'zip' package before creating the zip archive.",
                "I will use the package_management_tool to install the 'zip' package."
            ],
            "tool_name": "package_management_tool",
            "tool_args": {
                "runtime": "terminal",
                "code": "apt-get install zip"
            }
        }
        """,
        """
        {
            "thoughts": [
                "The installation of the 'zip' package is pending confirmation.",
                "I will confirm the installation by responding 'Y'."
            ],
            "tool_name": "code_execution_tool",
            "tool_args": {
                "runtime": "terminal",
                "code": "Y"
            }
        }
        """,
        """
        {
            "thoughts": [
                "The 'zip' package has been successfully installed.",
                "Now, I can use the code_execution_tool to create the zip archive containing the text files."
            ],
            "tool_name": "code_execution_tool",
            "tool_args": {
                "runtime": "terminal",
                "code": "zip archive.zip file1.txt file2.txt file3.txt"
            }
        }
        """
    ],
    'system_output': [
        "(No output, text files created successfully)",
        "-bash: zip: command not found",
        "(The system prompts for confirmation to install the zip package)",
        "(The zip package and dependencies are installed successfully)",
        "Files added to archive.zip successfully"
    ],
    'metadata': [
        "Create text files and prepare for zipping",
        "Attempt to create a zip archive",
        "Install the zip package",
        "Confirm installation of the zip package",
        "Retry creating the zip archive after installation"
    ]
}

# Create a DataFrame
df = pd.DataFrame(data)

# Save the DataFrame as a Parquet file
df.to_parquet('enhanced_llm_finetuning2.pq', engine='pyarrow', index=False)

print("Enhanced Parquet file with new prompts created successfully.")
