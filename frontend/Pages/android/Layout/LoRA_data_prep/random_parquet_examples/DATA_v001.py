import pandas as pd

# Enhanced and concise example data for the conversation log
data = {
    'prompt': [
        "Setup Python env",
        "Install and verify Node.js"
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
        """
    ],
    'system_output': [
        "(Output of Python version check)",
        "(Output of Node.js and npm installation)"
    ],
    'metadata': [
        "Python environment setup",
        "Node.js installation and testing"
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
