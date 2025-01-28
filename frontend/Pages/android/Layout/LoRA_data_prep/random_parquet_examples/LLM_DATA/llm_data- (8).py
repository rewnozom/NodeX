import pandas as pd

# Example data for the conversation log
data = {
    'prompt': [
        "Search for the keyword 'project' in all text files in the directory.",
        "Create a backup of the directory 'documents' and save it as 'documents_backup.zip'.",
        "Install the 'requests' package using pip.",
        "Check if the 'requests' package is installed.",
        "Fetch the latest news headlines and save them to 'headlines.txt'.",
        "Delete the backup file 'documents_backup.zip'.",
        "List the contents of the 'downloads' directory and count the number of files.",
        "Write a Python script that prints 'Hello, World!' to the console.",
        "Retrieve the weather forecast for the next 7 days.",
        "Update the 'requests' package to the latest version."
    ],
    'agent_response': [
        """
        {
            "thoughts": [
                "The user wants to search for the keyword 'project' in all text files.",
                "I will use the code_execution_tool to search through files."
            ],
            "tool_name": "code_execution_tool",
            "tool_args": {
                "runtime": "terminal",
                "code": "grep 'project' *.txt"
            }
        }
        """,
        """
        {
            "thoughts": [
                "The user wants to back up the 'documents' directory.",
                "I will use the code_execution_tool to zip the directory."
            ],
            "tool_name": "code_execution_tool",
            "tool_args": {
                "runtime": "terminal",
                "code": "zip -r documents_backup.zip documents"
            }
        }
        """,
        """
        {
            "thoughts": [
                "The user requested to install the 'requests' package.",
                "I will use the package_management_tool to install 'requests' via pip."
            ],
            "tool_name": "package_management_tool",
            "tool_args": {
                "runtime": "python",
                "code": "pip install requests"
            }
        }
        """,
        """
        {
            "thoughts": [
                "I need to verify if the 'requests' package is installed.",
                "I will use the code_execution_tool to check installed packages."
            ],
            "tool_name": "code_execution_tool",
            "tool_args": {
                "runtime": "python",
                "code": "pip show requests"
            }
        }
        """,
        """
        {
            "thoughts": [
                "The user wants to fetch the latest news headlines.",
                "I will use the knowledge_tool to get the headlines and save them to a file."
            ],
            "tool_name": "knowledge_tool",
            "tool_args": {
                "operation": "fetch_headlines",
                "duration": "7d"
            }
        }
        """,
        """
        {
            "thoughts": [
                "The user wants to delete the 'documents_backup.zip' file.",
                "I will use the code_execution_tool to remove the file."
            ],
            "tool_name": "code_execution_tool",
            "tool_args": {
                "runtime": "terminal",
                "code": "rm documents_backup.zip"
            }
        }
        """,
        """
        {
            "thoughts": [
                "The user wants to list and count files in the 'downloads' directory.",
                "I will use the code_execution_tool to list files and count them."
            ],
            "tool_name": "code_execution_tool",
            "tool_args": {
                "runtime": "terminal",
                "code": "ls downloads | wc -l"
            }
        }
        """,
        """
        {
            "thoughts": [
                "The user wants a Python script that prints 'Hello, World!'.",
                "I will write the script and save it to 'hello.py'."
            ],
            "tool_name": "code_execution_tool",
            "tool_args": {
                "runtime": "python",
                "code": "echo 'print(\"Hello, World!\")' > hello.py"
            }
        }
        """,
        """
        {
            "thoughts": [
                "The user wants the weather forecast for the next 7 days.",
                "I will use the knowledge_tool to fetch the forecast."
            ],
            "tool_name": "knowledge_tool",
            "tool_args": {
                "operation": "fetch_weather_forecast",
                "duration": "7d"
            }
        }
        """,
        """
        {
            "thoughts": [
                "The user wants to update the 'requests' package.",
                "I will use the package_management_tool to upgrade the package."
            ],
            "tool_name": "package_management_tool",
            "tool_args": {
                "runtime": "python",
                "code": "pip install --upgrade requests"
            }
        }
        """
    ],
    'system_output': [
        "Keyword 'project' found in files: file1.txt, file2.txt",
        "Backup 'documents_backup.zip' created successfully.",
        "Package 'requests' installed successfully.",
        "Package 'requests' is installed.",
        "Headlines saved to 'headlines.txt'.",
        "File 'documents_backup.zip' deleted successfully.",
        "Number of files in 'downloads': 12",
        "Python script 'hello.py' created successfully.",
        "Weather forecast for the next 7 days retrieved.",
        "Package 'requests' updated successfully."
    ],
    'metadata': [
        "Search for 'project' in text files",
        "Create a zip backup of 'documents'",
        "Install the 'requests' package",
        "Verify 'requests' package installation",
        "Fetch and save latest news headlines",
        "Delete the zip backup file",
        "List and count files in 'downloads' directory",
        "Write and save a 'Hello, World!' script",
        "Retrieve 7-day weather forecast",
        "Update 'requests' package to latest version"
    ]
}

# Verify that all lists have the same length
print("prompt length:", len(data['prompt']))
print("agent_response length:", len(data['agent_response']))
print("system_output length:", len(data['system_output']))
print("metadata length:", len(data['metadata']))

# Create a DataFrame
df = pd.DataFrame(data)

# Save the DataFrame as a Parquet file
df.to_parquet('finetuning6.pq', engine='pyarrow', index=False)

print("Enhanced Parquet file with new prompts created successfully.")
