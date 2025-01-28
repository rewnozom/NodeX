import pandas as pd
import json

# Define the data for our scenarios
data = {
    'prompt': [
        "Analyze the sales data in 'sales.csv', create a visualization of the top 5 products, and email the results to the marketing team.",
        "Create a zip archive named 'archive.zip' containing multiple text files.",
        "Review the Python code in 'app.py', identify any security vulnerabilities, and suggest improvements. Then, apply the improvements and run the tests.",
        "Our web server is running slow. Investigate the issue, provide a diagnosis, and take necessary actions to improve performance.",
    ],
    'agent_response': [
        json.dumps({
            "thoughts": [
                "This task requires multiple steps: data analysis, visualization, and sending an email.",
                "I'll need to use the code_execution_tool for data analysis and visualization.",
                "Then, I'll use the email_tool to send the results.",
                "Let's break this down into subtasks."
            ],
            "tool_name": "code_execution_tool",
            "tool_args": {
                "runtime": "python",
                "code": "import pandas as pd\nimport matplotlib.pyplot as plt\n\n# Read and analyze data\ndf = pd.read_csv('sales.csv')\ntop_5_products = df.groupby('product')['sales'].sum().nlargest(5)\n\n# Create visualization\nplt.figure(figsize=(10, 6))\ntop_5_products.plot(kind='bar')\nplt.title('Top 5 Products by Sales')\nplt.xlabel('Product')\nplt.ylabel('Total Sales')\nplt.savefig('top_5_products.png')\nplt.close()\n\nprint(top_5_products)"
            }
        }),
        json.dumps({
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
        }),
        json.dumps({
            "thoughts": [
                "This task involves code review, security analysis, and code improvement.",
                "I'll need to use the code_execution_tool to read and analyze the code.",
                "Then, I'll use my knowledge_tool to identify vulnerabilities and suggest improvements.",
                "Finally, I'll apply the improvements and run the tests."
            ],
            "tool_name": "code_execution_tool",
            "tool_args": {
                "runtime": "python",
                "code": "with open('app.py', 'r') as file:\n    code = file.read()\nprint(code)"
            }
        }),
        json.dumps({
            "thoughts": [
                "This task requires system investigation and potentially multiple actions.",
                "I'll start by checking system resources and logs.",
                "Then, based on the findings, I'll take appropriate actions."
            ],
            "tool_name": "code_execution_tool",
            "tool_args": {
                "runtime": "terminal",
                "code": "top -bn1 | head -n 20\ndf -h\ntail -n 100 /var/log/apache2/error.log"
            }
        })
    ],
    'system_output': [
        "Product A    1000000\nProduct B     750000\nProduct C     500000\nProduct D     400000\nProduct E     300000\nName: sales, dtype: int64",
        "(No output, text files created successfully)",
        "import os\nfrom flask import Flask, request\n\napp = Flask(__name__)\n\n@app.route('/upload', methods=['POST'])\ndef upload_file():\n    if 'file' not in request.files:\n        return 'No file part', 400\n    file = request.files['file']\n    filename = file.filename\n    file.save(os.path.join('/uploads', filename))\n    return 'File uploaded successfully', 200\n\nif __name__ == '__main__':\n    app.run(debug=True)",
        "top - 14:30:22 up 15 days,  3:56,  1 user,  load average: 2.15, 2.30, 2.25\nTasks: 128 total,   1 running, 127 sleeping,   0 stopped,   0 zombie\n%Cpu(s): 70.2 us, 20.1 sy,  0.0 ni,  9.5 id,  0.0 wa,  0.0 hi,  0.2 si,  0.0 st\nMiB Mem :   3940.7 total,    236.1 free,   3290.5 used,    414.1 buff/cache\nMiB Swap:   2048.0 total,    689.2 free,   1358.8 used.    394.5 avail Mem \n\n    PID USER      PR  NI    VIRT    RES    SHR S  %CPU  %MEM     TIME+ COMMAND\n   1256 www-data  20   0  741480 631292  23728 S  65.0  15.6   2:32.25 apache2\n   1257 www-data  20   0  741736 631548  23728 S  64.8  15.6   2:32.20 apache2\n   1258 www-data  20   0  741224 631036  23728 S  64.5  15.6   2:32.15 apache2\n   \nFilesystem      Size  Used Avail Use% Mounted on\n/dev/sda1        30G   28G  0.5G  98% /\n/dev/sdb1       100G   50G   50G  50% /data\n\n[Thu Aug 15 14:30:22.759144 2024] [mpm_prefork:error] [pid 1234] AH00161: server reached MaxRequestWorkers setting, consider raising the MaxRequestWorkers setting"
    ],
    'metadata': [
        "Complex task involving data analysis, visualization, and email communication, demonstrating use of multiple tools and task decomposition.",
        "Task demonstrating file operations and use of system commands.",
        "Complex code review task involving security analysis, code improvement, and testing, demonstrating use of multiple tools and programming skills.",
        "Complex system maintenance task involving performance investigation, diagnosis, and optimization, demonstrating use of system administration tools and problem-solving skills."
    ]
}

# Create a DataFrame
df = pd.DataFrame(data)

# Verify that all lists have the same length
print("prompt length:", len(data['prompt']))
print("agent_response length:", len(data['agent_response']))
print("system_output length:", len(data['system_output']))
print("metadata length:", len(data['metadata']))

# Save the DataFrame as a Parquet file
df.to_parquet('advanced_ai_scenarios.pq', engine='pyarrow', index=False)

print("Advanced AI scenarios Parquet file created successfully.")

# Optional: Read back the Parquet file to verify its contents
df_read = pd.read_parquet('advanced_ai_scenarios.pq')
print("\nParquet file contents:")
print(df_read)