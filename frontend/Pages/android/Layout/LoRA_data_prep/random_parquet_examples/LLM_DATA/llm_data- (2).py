import pandas as pd

# Enhanced and concise example data for the conversation log
data = {
    'prompt': [
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
        """,
        """
        {
            "thoughts": [
                "The unit test has completed successfully.",
                "All 4 tests passed, with no errors or failures.",
                "The output shows the calculated values for circle area, circle perimeter, rectangle area, and rectangle perimeter.",
                "I will report the results to the user."
            ],
            "tool_name": "response",
            "tool_args": {
                "text": "Unit test results: All 4 tests passed successfully. Circle area, circle perimeter, rectangle area, and rectangle perimeter functions are working correctly."
            }
        }
        """
    ],
    'system_output': [
        "File created and message written successfully.",
        "File created and text written successfully.",
        "Hello, World!",
        "The file 'hello.txt' has been deleted.",
        "No output, indicating the file has been deleted successfully.",
        "Testing circle_area function:\nRadius: 1, Calculated Area: 3.141592653589793\nRadius: 2.5, Calculated Area: 19.634954084936208\n.\nTesting circle_perimeter function:\nRadius: 1, Calculated Perimeter: 6.283185307179586\nRadius: 2.5, Calculated Perimeter: 15.707963267948966\n.\nTesting rectangle_area function:\nLength: 2, Width: 3, Calculated Area: 6\nLength: 4, Width: 5, Calculated Area: 20\n.\nTesting rectangle_perimeter function:\nLength: 2, Width: 3, Calculated Perimeter: 10\nLength: 4, Width: 5, Calculated Perimeter: 18\n\n----------------------------------------------------------------------\nRan 4 tests in 0.001s\n\nOK"
    ],
    'metadata': [
        "Create a text file and write a message into it",
        "Create another text file and write content into it",
        "Read and display contents of a text file",
        "Delete a text file",
        "Verify file deletion",
        "Run unit tests for shapes2 module and report results"
    ]
}

# Create a DataFrame
df = pd.DataFrame(data)

# Save the DataFrame as a Parquet file
df.to_parquet('enhanced_llm_finetuning1.pq', engine='pyarrow', index=False)

print("Enhanced Parquet file with new prompts created successfully.")
