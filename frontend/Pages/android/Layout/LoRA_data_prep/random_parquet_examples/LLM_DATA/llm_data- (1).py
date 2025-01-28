import pandas as pd

# Enhanced and concise example data for the conversation log
data = {
    'prompt': [
        "Setup Python env",
        "Install and verify Node.js",
        "Navigate to 'Vartan_Auto/step3', read 'perform_ocr.py', and analyze the code for improvements.",
        "Read 'perform_ocr.py' and analyze the code.",
        "Write a Python script 'sum.py' that takes two numbers as input and prints their sum.",
        "Modify 'sum.py' to read the numbers from the command line arguments.",
        "Create a file named 'numbers.txt' and write two numbers, each on a new line.",
        "Modify 'sum.py' to read the numbers from 'numbers.txt' and print their sum.",
        "Delete the file 'numbers.txt'.",
        "Create a text file named 'hello.txt' and write 'Hello, World!' into it.",
        "Create another file named 'example.txt' and write 'Example text' into it.",
        "Read the contents of 'hello.txt' and display it.",
        "Delete the file 'hello.txt'.",
        "Verify the deletion of 'hello.txt'.",
        "cd \"project1\" and python -m unittest test_shapes2.py, report the results"
    ],
    'agent_response': [
        """
        {
            "thoughts": [
                "I'll start by checking the Python installation and then proceed to set up the environment.",
                "If Python is installed, I'll set up a virtual environment and install necessary packages."
            ],
            "tool_name": "code_execution_tool",
            "tool_args": {
                "runtime": "terminal",
                "code": "python3 --version"
            }
        }
        """,
        """
        {
            "thoughts": [
                "I'll install Node.js and npm, then verify their installation.",
                "First, I'll update the package list and add the NodeSource repository."
            ],
            "tool_name": "code_execution_tool",
            "tool_args": {
                "runtime": "terminal",
                "code": "sudo apt-get update && curl -sL https://deb.nodesource.com/setup_14.x | sudo -E bash - && sudo apt-get install -y nodejs"
            }
        }
        """,
        """
        {
            "thoughts": [
                "Let's break down the task into manageable steps:",
                "1. Navigate to the Directory: Change the directory to `Vartan_Auto/step3`.",
                "2. Read the `perform_ocr.py` File: Open and read the contents of the `perform_ocr.py` file.",
                "3. Analyze the Code: Understand the current implementation and identify areas for improvement.",
                "4. Make Improvements: Implement the identified improvements in the code."
            ],
            "tool_name": "code_execution_tool",
            "tool_args": {
                "runtime": "terminal",
                "code": "cd Vartan_Auto/step3"
            }
        }
        """,
        """
        {
            "thoughts": [
                "Reading the contents of the 'perform_ocr.py' file to analyze the current implementation."
            ],
            "tool_name": "code_execution_tool",
            "tool_args": {
                "runtime": "terminal",
                "code": "cat perform_ocr.py"
            }
        }
        """,
        """
        {
            "thoughts": [
                "The user has requested a Python script that takes two numbers as input and prints their sum.",
                "I will use the code_execution_tool to create and execute the script.",
                "First, I will create the script with the necessary code.",
                "Then, I will execute the script with sample inputs to verify its correctness."
            ],
            "tool_name": "code_execution_tool",
            "tool_args": {
                "runtime": "python",
                "code": "with open('sum.py', 'w') as f:\\n f.write(\"\"\"\\nimport sys\\nif len(sys.argv) != 3:\\n print('Usage: python sum.py <num1> <num2>')\\n sys.exit(1)\\nnum1 = int(sys.argv[1])\\nnum2 = int(sys.argv[2])\\nprint(num1 + num2)\\n\"\"\")"
            }
        }
        """,
        """
        {
            "thoughts": [
                "The user wants the script 'sum.py' to read numbers directly from the command line arguments.",
                "I will modify the existing script to achieve this."
            ],
            "tool_name": "code_execution_tool",
            "tool_args": {
                "runtime": "python",
                "code": "with open('sum.py', 'w') as f:\\n f.write(\"\"\"\\nimport sys\\nif len(sys.argv) != 3:\\n print('Usage: python sum.py <num1> <num2>')\\n sys.exit(1)\\nnum1 = int(sys.argv[1])\\nnum2 = int(sys.argv[2])\\nprint(num1 + num2)\\n\"\"\")"
            }
        }
        """,
        """
        {
            "thoughts": [
                "The user has requested to create a file named 'numbers.txt' and write two numbers, each on a new line.",
                "I will create the file and write the numbers into it."
            ],
            "tool_name": "code_execution_tool",
            "tool_args": {
                "runtime": "python",
                "code": "with open('numbers.txt', 'w') as f:\\n f.write('10\\n20')"
            }
        }
        """,
        """
        {
            "thoughts": [
                "The user wants the script 'sum.py' to read numbers from 'numbers.txt' instead of command line arguments.",
                "I will modify the script to read the file and compute the sum."
            ],
            "tool_name": "code_execution_tool",
            "tool_args": {
                "runtime": "python",
                "code": "with open('sum.py', 'w') as f:\\n f.write(\"\"\"\\nwith open('numbers.txt') as file:\\n nums = file.readlines()\\n num1 = int(nums[0])\\n num2 = int(nums[1])\\n print(num1 + num2)\\n\"\"\")"
            }
        }
        """,
        """
        {
            "thoughts": [
                "The user has requested to delete the file 'numbers.txt'.",
                "I will remove the file from the system."
            ],
            "tool_name": "code_execution_tool",
            "tool_args": {
                "runtime": "terminal",
                "code": "rm numbers.txt"
            }
        }
        """,
        """
        {
            "thoughts": [
                "The user has requested creating a text file and writing a message into it.",
                "I will use the code_execution_tool to execute a Python script that creates the file and writes the message.",
                "First, I need to write the Python code that accomplishes this task."
            ],
            "tool_name": "code_execution_tool",
            "tool_args": {
                "runtime": "python",
                "code": "with open('hello.txt', 'w') as f:\\n f.write('Hello, World!')\\nprint('File created and message written successfully.')"
            }
        }
        """,
        """
        {
            "thoughts": [
                "The user has requested to create another text file named 'example.txt' and write 'Example text' into it.",
                "I will again use the code_execution_tool to execute the necessary Python code."
            ],
            "tool_name": "code_execution_tool",
            "tool_args": {
                "runtime": "python",
                "code": "with open('example.txt', 'w') as f:\\n f.write('Example text')\\nprint('File created and text written successfully.')"
            }
        }
        """,
        """
        {
            "thoughts": [
                "The user has asked me to read and display the contents of the 'hello.txt' file.",
                "I will use the code_execution_tool to execute a Python command that reads and prints the file's content."
            ],
            "tool_name": "code_execution_tool",
            "tool_args": {
                "runtime": "python",
                "code": "with open('hello.txt', 'r') as f:\\n content = f.read()\\nprint(content)"
            }
        }
        """,
        """
        {
            "thoughts": [
                "The user has requested to delete the 'hello.txt' file.",
                "I will use the code_execution_tool to execute a terminal command that deletes the file."
            ],
            "tool_name": "code_execution_tool",
            "tool_args": {
                "runtime": "terminal",
                "code": "rm hello.txt"
            }
        }
        """,
        """
        {
            "thoughts": [
                "The user wants to verify that 'hello.txt' has been deleted.",
                "I will use the code_execution_tool to check if the file still exists."
            ],
            "tool_name": "code_execution_tool",
            "tool_args": {
                "runtime": "terminal",
                "code": "ls | grep hello.txt"
            }
        }
        """,
        """
        {
            "thoughts": [
                "The user has requested to run a unit test for the shapes2 module.",
                "First, I need to navigate to the project directory.",
                "Then, I will execute the unit test using the python -m unittest command."
            ],
            "tool_name": "code_execution_tool",
            "tool_args": {
                "runtime": "terminal",
                "code": "cd project1 && python -m unittest test_shapes2.py"
            }
        }
        """
    ],
    'system_output': [
        "(Output of Python version check)",
        "(Output of Node.js and npm installation)",
        "Navigation to 'Vartan_Auto/step3' directory successful.",
        "Contents of 'perform_ocr.py' displayed successfully.",
        "The script 'sum.py' has been created successfully.",
        "The script 'sum.py' has been modified to read numbers from command line arguments.",
        "The file 'numbers.txt' has been created and the numbers have been written to it.",
        "The script 'sum.py' has been modified to read numbers from 'numbers.txt' and print their sum.",
        "The file 'numbers.txt' has been deleted.",
        "File created and message written successfully.",
        "File created and text written successfully.",
        "Hello, World!",
        "The file 'hello.txt' has been deleted.",
        "No output, indicating the file has been deleted successfully.",
        "Testing circle_area function:\nRadius: 1, Calculated Area: 3.141592653589793\nRadius: 2.5, Calculated Area: 19.634954084936208\n.\nTesting circle_perimeter function:\nRadius: 1, Calculated Perimeter: 6.283185307179586\nRadius: 2.5, Calculated Perimeter: 15.707963267948966\n.\nTesting rectangle_area function:\nLength: 2, Width: 3, Calculated Area: 6\nLength: 4, Width: 5, Calculated Area: 20\n.\nTesting rectangle_perimeter function:\nLength: 2, Width: 3, Calculated Perimeter: 10\nLength: 4, Width: 5, Calculated Perimeter: 18\n\n----------------------------------------------------------------------\nRan 4 tests in 0.001s\n\nOK"
    ],
    'metadata': [
        "Python environment setup",
        "Node.js installation and testing",
        "Navigate to directory and analyze Python script",
        "Read and analyze Python script",
        "Create and execute a Python script that sums two numbers",
        "Modify Python script to read command line arguments",
        "Create a text file and write numbers into it",
        "Modify Python script to read numbers from a file",
        "Delete a text file",
        "Create a text file and write a message into it",
        "Create another text file and write content into it",
        "Read and display contents of a text file",
        "Delete a text file",
        "Verify file deletion",
        "Run unit tests for shapes2 module and report results"
    ]
}

print("prompt length:", len(data['prompt']))
print("agent_response length:", len(data['agent_response']))
print("system_output length:", len(data['system_output']))
print("metadata length:", len(data['metadata']))

# Create a DataFrame
df = pd.DataFrame(data)

# Save the DataFrame as a Parquet file
df.to_parquet('enhanced_llm_finetuning.pq', engine='pyarrow', index=False)

print("Enhanced Parquet file with concise prompts created successfully.")
