import pandas as pd

# Example data for the conversation log
data = {
    'prompt': [
        "List all files in the current directory.",
        "Create a new directory named 'project'.",
        "Generate a summary of the latest 10 email messages.",
        "Retry zipping files after installing the zip package.",
        "List all installed packages."
    ],
    'agent_response': [
        """
        {
            "thoughts": [
                "The user requested a list of all files in the directory.",
                "I will use the code_execution_tool to execute a 'ls' command."
            ],
            "tool_name": "code_execution_tool",
            "tool_args": {
                "runtime": "terminal",
                "code": "ls"
            }
        }
        """,
        """
        {
            "thoughts": [
                "The user wants to create a new directory.",
                "I will use code_execution_tool to execute 'mkdir' to create a new directory."
            ],
            "tool_name": "code_execution_tool",
            "tool_args": {
                "runtime": "terminal",
                "code": "mkdir project"
            }
        }
        """,
        """
        {
            "thoughts": [
                "The user wants a summary of the latest 10 emails.",
                "I will fetch the emails and then summarize them."
            ],
            "tool_name": "email_tool",
            "tool_args": {
                "operation": "fetch_emails",
                "count": 10
            }
        }
        """,
        """
        {
            "thoughts": [
                "The zip package installation failed previously.",
                "I will retry the zipping command now."
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
                "The user requested a list of installed packages.",
                "I will use the code_execution_tool to execute a 'dpkg --list' command."
            ],
            "tool_name": "code_execution_tool",
            "tool_args": {
                "runtime": "terminal",
                "code": "dpkg --list"
            }
        }
        """
    ],
    'system_output': [
        "file1.txt\nfile2.txt\nfile3.txt",
        "Directory 'project' created successfully.",
        "Summary of latest 10 emails generated.",
        "Files zipped into 'archive.zip' successfully.",
        "List of installed packages displayed."
    ],
    'metadata': [
        "List files in the directory",
        "Create a new directory",
        "Fetch and summarize the latest 10 emails",
        "Retry zipping files after package installation",
        "List all installed packages"
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
df.to_parquet('finetuning5.pq', engine='pyarrow', index=False)

print("Enhanced Parquet file with new prompts created successfully.")
