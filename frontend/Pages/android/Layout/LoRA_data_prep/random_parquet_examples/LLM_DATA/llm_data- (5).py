import pandas as pd

# Example data for the conversation log with a focus on tool usage scenarios
data = {
    'prompt': [
        "Run the Python script 'calculate.py' to calculate the area of a rectangle.",
        "Check the available disk space on the system.",
        "Install the 'requests' package using pip.",
        "Update all system packages to their latest versions.",
        "Create a new file named 'notes.txt' and write 'Meeting at 10 AM' into it.",
        "Delete the file 'notes.txt'.",
        "Store the value of 'x' as 42 in memory for later use.",
        "Retrieve the value stored in memory under the key 'x'.",
        "Search for the latest Python release version.",
        "Retrieve the documentation for the 'requests' Python package."
    ],
    'agent_response': [
        # Scenario 1: Running a Python Script
        """
        {
            "thoughts": [
                "The user has requested to run the Python script 'calculate.py' to calculate the area of a rectangle.",
                "I will use the code_execution_tool to execute the Python script."
            ],
            "tool_name": "code_execution_tool",
            "tool_args": {
                "runtime": "python",
                "code": "python calculate.py"
            }
        }
        """,
        # Scenario 2: Checking Disk Space
        """
        {
            "thoughts": [
                "The user wants to check the available disk space on the system.",
                "I will use the code_execution_tool to execute the 'df -h' command."
            ],
            "tool_name": "code_execution_tool",
            "tool_args": {
                "runtime": "terminal",
                "code": "df -h"
            }
        }
        """,
        # Scenario 3: Installing a Python Package
        """
        {
            "thoughts": [
                "The user has requested to install the 'requests' package using pip.",
                "I will use the package_management_tool to install the package."
            ],
            "tool_name": "package_management_tool",
            "tool_args": {
                "runtime": "terminal",
                "code": "pip install requests"
            }
        }
        """,
        # Scenario 4: Updating System Packages
        """
        {
            "thoughts": [
                "The user wants to update all system packages to their latest versions.",
                "I will use the package_management_tool to update the packages using 'apt-get upgrade'."
            ],
            "tool_name": "package_management_tool",
            "tool_args": {
                "runtime": "terminal",
                "code": "apt-get update && apt-get upgrade -y"
            }
        }
        """,
        # Scenario 5: Creating a New File
        """
        {
            "thoughts": [
                "The user has requested to create a new file named 'notes.txt' and write 'Meeting at 10 AM' into it.",
                "I will use the file_management_tool to create the file and write the content."
            ],
            "tool_name": "file_management_tool",
            "tool_args": {
                "runtime": "python",
                "code": "with open('notes.txt', 'w') as f:\\n f.write('Meeting at 10 AM')"
            }
        }
        """,
        # Scenario 6: Deleting a File
        """
        {
            "thoughts": [
                "The user has requested to delete the file 'notes.txt'.",
                "I will use the file_management_tool to delete the file."
            ],
            "tool_name": "file_management_tool",
            "tool_args": {
                "runtime": "terminal",
                "code": "rm notes.txt"
            }
        }
        """,
        # Scenario 7: Storing a Variable in Memory
        """
        {
            "thoughts": [
                "The user wants to store the value of 'x' as 42 in memory for later use.",
                "I will use the memory_tool to store this value."
            ],
            "tool_name": "memory_tool",
            "tool_args": {
                "action": "store",
                "key": "x",
                "value": 42
            }
        }
        """,
        # Scenario 8: Retrieving a Value from Memory
        """
        {
            "thoughts": [
                "The user wants to retrieve the value stored in memory under the key 'x'.",
                "I will use the memory_tool to retrieve this value."
            ],
            "tool_name": "memory_tool",
            "tool_args": {
                "action": "retrieve",
                "key": "x"
            }
        }
        """,
        # Scenario 9: Searching for Information
        """
        {
            "thoughts": [
                "The user wants to know the latest Python release version.",
                "I will use the knowledge_tool to search for this information."
            ],
            "tool_name": "knowledge_tool",
            "tool_args": {
                "query": "latest Python release version"
            }
        }
        """,
        # Scenario 10: Getting Documentation
        """
        {
            "thoughts": [
                "The user wants the documentation for the 'requests' Python package.",
                "I will use the knowledge_tool to retrieve this documentation."
            ],
            "tool_name": "knowledge_tool",
            "tool_args": {
                "query": "requests Python package documentation"
            }
        }
        """
    ],
    'system_output': [
        # Outputs for the above responses
        "Area of the rectangle: 20",
        "Filesystem Size Used Avail Use% Mounted on ...",
        "Successfully installed requests",
        "System packages updated successfully",
        "File 'notes.txt' created successfully",
        "File 'notes.txt' deleted successfully",
        "Value 42 stored in memory under key 'x'",
        "Retrieved value: 42",
        "Python 3.10.4 is the latest release version",
        "The documentation for the 'requests' package is available at https://docs.python-requests.org/en/latest/"
    ],
    'metadata': [
        # Metadata descriptions for each scenario
        "Run a Python script",
        "Check disk space",
        "Install a Python package using pip",
        "Update all system packages",
        "Create a new file and write content",
        "Delete a file",
        "Store a value in memory",
        "Retrieve a value from memory",
        "Search for information",
        "Retrieve documentation"
    ]
}

# Create a DataFrame
df = pd.DataFrame(data)

# Save the DataFrame as a Parquet file
df.to_parquet('enhanced_llm_finetuning3.pq', engine='pyarrow', index=False)

print("Enhanced Parquet file with tool usage scenarios created successfully.")
