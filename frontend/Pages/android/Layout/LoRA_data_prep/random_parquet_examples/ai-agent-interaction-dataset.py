import json
import pandas as pd

data = {
    'prompt': [
        "Create a Python script that calculates the Fibonacci sequence up to the 10th number.",
        "What's the capital of France? After answering, store this information in your memory.",
        "Compress all .txt files in the current directory into a zip archive named 'documents.zip'.",
        "Retrieve information about climate change from your knowledge base.",
        "Create a simple HTML page with a header and a paragraph about AI.",
        "Install the 'requests' library for Python and use it to fetch the content of 'https://example.com'.",
        "Analyze the following code snippet for potential improvements:\n\ndef factorial(n):\n    if n == 0:\n        return 1\n    else:\n        return n * factorial(n-1)",
        "Create a bar chart using matplotlib to visualize monthly sales data.",
        "What information do you have stored in your memory about world capitals?",
        "Execute a long-running task that simulates data processing. Show how you'd handle waiting for the result.",
        "Generate a secure random password with at least one uppercase letter, one lowercase letter, one number, and one special character.",
        "Create a simple Node.js server that responds with 'Hello, World!' on the root route.",
        "Calculate the sum of all even numbers between 1 and 100 using Python.",
        "Forget all information in your memory related to world capitals.",
        "Use a subordinate agent to brainstorm ideas for a science fiction story set in the year 3000."
    ],
    'agent_response': [
        json.dumps({
            "thoughts": [
                "The user wants a Python script for Fibonacci sequence calculation.",
                "I'll use the code_execution_tool to write and run the script.",
                "The script will use a loop to calculate the sequence up to the 10th number."
            ],
            "tool_name": "code_execution_tool",
            "tool_args": {
                "runtime": "python",
                "code": """
def fibonacci(n):
    fib = [0, 1]
    for i in range(2, n):
        fib.append(fib[i-1] + fib[i-2])
    return fib

result = fibonacci(10)
print(f"Fibonacci sequence up to the 10th number: {result}")
"""
            }
        }, indent=2),
        json.dumps({
            "thoughts": [
                "The user asked about the capital of France.",
                "I'll use the knowledge_tool to retrieve this information.",
                "After answering, I'll store this in memory using the memory_tool."
            ],
            "tool_name": "knowledge_tool",
            "tool_args": {
                "question": "What is the capital of France?"
            }
        }, indent=2),
        json.dumps({
            "thoughts": [
                "The user wants to compress all .txt files into a zip archive.",
                "I'll use the code_execution_tool with terminal runtime to accomplish this.",
                "First, I'll check if the zip command is available."
            ],
            "tool_name": "code_execution_tool",
            "tool_args": {
                "runtime": "terminal",
                "code": "which zip"
            }
        }, indent=2),
        json.dumps({
            "thoughts": [
                "The user wants information about climate change.",
                "I'll use the knowledge_tool to retrieve this information."
            ],
            "tool_name": "knowledge_tool",
            "tool_args": {
                "question": "Provide a summary of current understanding on climate change."
            }
        }, indent=2),
        json.dumps({
            "thoughts": [
                "The user wants a simple HTML page about AI.",
                "I'll use the code_execution_tool to create an HTML file."
            ],
            "tool_name": "code_execution_tool",
            "tool_args": {
                "runtime": "terminal",
                "code": """
cat << EOF > ai_page.html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI: A Brief Introduction</title>
</head>
<body>
    <h1>Artificial Intelligence: Shaping Our Future</h1>
    <p>Artificial Intelligence (AI) is a rapidly evolving field of computer science focused on creating intelligent machines that can perform tasks that typically require human intelligence. From machine learning to natural language processing, AI is transforming industries and opening new frontiers in technology.</p>
</body>
</html>
EOF

echo "HTML file created: ai_page.html"
"""
            }
        }, indent=2),
        json.dumps({
            "thoughts": [
                "The user wants to install 'requests' library and use it to fetch content.",
                "I'll first use code_execution_tool to install the library.",
                "Then, I'll use it again to run a Python script that uses requests."
            ],
            "tool_name": "code_execution_tool",
            "tool_args": {
                "runtime": "terminal",
                "code": "pip install requests"
            }
        }, indent=2),
        json.dumps({
            "thoughts": [
                "The user wants an analysis of the factorial function.",
                "I'll review the code and provide suggestions for improvement."
            ],
            "tool_name": "response",
            "tool_args": {
                "text": "The factorial function provided is a correct recursive implementation. However, it can be improved in the following ways:\n\n1. Add input validation to handle negative numbers and non-integer inputs.\n2. Use iteration instead of recursion to avoid potential stack overflow for large inputs.\n3. Consider using memoization to optimize performance for repeated calls.\n\nHere's an improved version:\n\n```python\nfrom functools import lru_cache\n\n@lru_cache(maxsize=None)\ndef factorial(n):\n    if not isinstance(n, int) or n < 0:\n        raise ValueError(\"Input must be a non-negative integer\")\n    result = 1\n    for i in range(1, n + 1):\n        result *= i\n    return result\n```\n\nThis version includes input validation, uses iteration to avoid recursion, and applies memoization using the `lru_cache` decorator for improved performance on repeated calls."
            }
        }, indent=2),
        json.dumps({
            "thoughts": [
                "The user wants a bar chart of monthly sales data using matplotlib.",
                "I'll create a Python script to generate this chart.",
                "First, I'll check if matplotlib is installed."
            ],
            "tool_name": "code_execution_tool",
            "tool_args": {
                "runtime": "terminal",
                "code": "pip list | grep matplotlib"
            }
        }, indent=2),
        json.dumps({
            "thoughts": [
                "The user is asking about stored information on world capitals.",
                "I'll use the memory_tool to query for this information."
            ],
            "tool_name": "memory_tool",
            "tool_args": {
                "query": "world capitals"
            }
        }, indent=2),
        json.dumps({
            "thoughts": [
                "The user wants to simulate a long-running task and demonstrate waiting for results.",
                "I'll use the code_execution_tool to run a Python script with a sleep function.",
                "Then I'll use the output runtime to check for completion."
            ],
            "tool_name": "code_execution_tool",
            "tool_args": {
                "runtime": "python",
                "code": """
import time
import threading

def long_running_task():
    print("Starting long-running task...")
    time.sleep(10)
    print("Long-running task completed!")

thread = threading.Thread(target=long_running_task)
thread.start()
print("Task started in background. Use 'output' runtime to check progress.")
"""
            }
        }, indent=2),
        json.dumps({
            "thoughts": [
                "The user wants a secure random password with specific requirements.",
                "I'll use Python's random and string modules to generate this password."
            ],
            "tool_name": "code_execution_tool",
            "tool_args": {
                "runtime": "python",
                "code": """
import random
import string

def generate_password(length=12):
    lowercase = string.ascii_lowercase
    uppercase = string.ascii_uppercase
    digits = string.digits
    symbols = string.punctuation
    
    # Ensure we have at least one of each required character type
    password = [
        random.choice(lowercase),
        random.choice(uppercase),
        random.choice(digits),
        random.choice(symbols)
    ]
    
    # Fill the rest of the password length with random characters
    for _ in range(length - 4):
        password.append(random.choice(lowercase + uppercase + digits + symbols))
    
    # Shuffle the password characters
    random.shuffle(password)
    
    return ''.join(password)

secure_password = generate_password(16)
print(f"Generated secure password: {secure_password}")
"""
            }
        }, indent=2),
        json.dumps({
            "thoughts": [
                "The user wants a simple Node.js server that responds with 'Hello, World!'",
                "I'll create a JavaScript file with the server code and run it using Node.js."
            ],
            "tool_name": "code_execution_tool",
            "tool_args": {
                "runtime": "terminal",
                "code": """
cat << EOF > server.js
const http = require('http');

const server = http.createServer((req, res) => {
  res.statusCode = 200;
  res.setHeader('Content-Type', 'text/plain');
  res.end('Hello, World!');
});

const port = 3000;
server.listen(port, () => {
  console.log(`Server running at http://localhost:${port}/`);
});
EOF

node server.js
"""
            }
        }, indent=2),
        json.dumps({
            "thoughts": [
                "The user wants to calculate the sum of even numbers between 1 and 100.",
                "I'll use Python to write a simple script for this calculation."
            ],
            "tool_name": "code_execution_tool",
            "tool_args": {
                "runtime": "python",
                "code": """
even_sum = sum(num for num in range(2, 101, 2))
print(f"The sum of all even numbers between 1 and 100 is: {even_sum}")
"""
            }
        }, indent=2),
        json.dumps({
            "thoughts": [
                "The user wants to forget all information related to world capitals.",
                "I'll use the memory_tool with the 'forget' argument to remove this information."
            ],
            "tool_name": "memory_tool",
            "tool_args": {
                "forget": "world capitals"
            }
        }, indent=2),
        json.dumps({
            "thoughts": [
                "The user wants to use a subordinate agent for brainstorming story ideas.",
                "I'll use the call_subordinate tool to delegate this task."
            ],
            "tool_name": "call_subordinate",
            "tool_args": {
                "message": "Brainstorm 5 unique ideas for a science fiction story set in the year 3000. Focus on themes of technological advancement, social change, and environmental challenges. Provide a brief one-sentence pitch for each idea.",
                "reset": "true"
            }
        }, indent=2)
    ],
    'system_output': [
        "Fibonacci sequence up to the 10th number: [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]",
        "The capital of France is Paris.",
        "/usr/bin/zip",
        "Climate change is a long-term shift in global or regional climate patterns. Key points: 1) Global temperatures are rising due to human activities, primarily the burning of fossil fuels. 2) This leads to more frequent extreme weather events, rising sea levels, and disruptions to ecosystems. 3) Mitigation efforts focus on reducing greenhouse gas emissions and adapting to changes already underway.",
        "HTML file created: ai_page.html",
        "Requirement already satisfied: requests in /usr/local/lib/python3.8/site-packages (2.25.1)",
        "Analysis provided in the response.",
        "matplotlib 3.3.4",
        "Memory query for 'world capitals' returned: Paris is the capital of France.",
        "Starting long-running task...\nTask started in background. Use 'output' runtime to check progress.",
        "Generated secure password: P9#mK2xL$fGh3Nj",
        "Server running at http://localhost:3000/",
        "The sum of all even numbers between 1 and 100 is: 2550",
        "Memories related to 'world capitals' have been removed.",
        "Subordinate agent response:\n1. \"The Last Oasis\": In a world of extreme desertification, humanity's last hope lies in a newly discovered underground ecosystem.\n2. \"Neural Netizens\": A society where human consciousness can be uploaded to a global network faces its first digital pandemic.\n3. \"Gravity's Revenge\": As Earth's gravity becomes unpredictable, a team of scientists races to prevent the planet's core from collapsing.\n4. \"The Empathy Engine\": An AI designed to feel human emotions becomes the key to preventing an interstellar war.\n5. \"Chronos Unbound\": Time itself begins to unravel, and a group of temporal engineers must reset the universe's clock."
    ],
    'metadata': [
        "Generate Fibonacci sequence using Python",
        "Retrieve and store information about France's capital",
        "Compress text files into a zip archive",
        "Retrieve information about climate change",
        "Create a simple HTML page about AI",
        "Install Python library and use it to fetch web content",
        "Analyze and improve a recursive factorial function",
        "Create a bar chart using matplotlib",
        "Query memory for information about world capitals",
        "Simulate and handle a long-running task",
        "Generate a secure random password",
        "Create a simple Node.js server",
        "Calculate sum of even numbers using Python",
        "Remove specific information from memory",
        "Use subordinate for creative brainstorming"
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
df.to_parquet('finetuning.pq', engine='pyarrow', index=False)

print("Enhanced Parquet file with new prompts created successfully.")