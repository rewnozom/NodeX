import pandas as pd

# Example data for the conversation log
data = {
    'prompt': [
        "Analyze the log file 'system.log' for error messages and summarize the top 5 most frequent errors.",
        "Create a new Python virtual environment, install the 'flask' package, and write a basic Flask app.",
        "Merge multiple CSV files in the 'data' directory into a single file named 'combined_data.csv'.",
        "Check the disk usage of the system and alert if usage exceeds 80%.",
        "Fetch user details from an API, and if any user has an inactive status, send a reminder email.",
        "Generate a performance report from the latest data in 'sales_data.xlsx' and export it as a PDF.",
        "Update the local Git repository with the latest changes from the remote repository and handle any merge conflicts.",
        "Set up a cron job to back up the 'project' directory daily and verify its execution.",
        "Retrieve the latest blog posts from the company website and generate a summary of the top 3 posts.",
        "Configure a firewall rule to block incoming traffic from a specific IP address and verify the rule is active."
    ],
    'agent_response': [
        """
        {
            "thoughts": [
                "The user wants to analyze 'system.log' for errors.",
                "I will use the code_execution_tool to grep error messages and summarize them."
            ],
            "tool_name": "code_execution_tool",
            "tool_args": {
                "runtime": "terminal",
                "code": "grep 'ERROR' system.log | sort | uniq -c | sort -nr | head -n 5"
            }
        }
        """,
        """
        {
            "thoughts": [
                "The user requests a new Python environment and Flask installation.",
                "I will create a virtual environment, install Flask, and then write a simple app."
            ],
            "tool_name": "code_execution_tool",
            "tool_args": {
                "runtime": "terminal",
                "code": "python3 -m venv venv && source venv/bin/activate && pip install flask && echo 'from flask import Flask; app = Flask(__name__); @app.route("/") def hello(): return "Hello, World!"; if __name__ == "__main__": app.run()' > app.py"
            }
        }
        """,
        """
        {
            "thoughts": [
                "The user wants to merge CSV files in the 'data' directory.",
                "I will use the code_execution_tool to concatenate CSV files into one."
            ],
            "tool_name": "code_execution_tool",
            "tool_args": {
                "runtime": "python",
                "code": "import pandas as pd; import glob; all_files = glob.glob('data/*.csv'); df = pd.concat((pd.read_csv(f) for f in all_files), ignore_index=True); df.to_csv('combined_data.csv', index=False)"
            }
        }
        """,
        """
        {
            "thoughts": [
                "The user requests checking disk usage and alerting if over 80%.",
                "I will use the code_execution_tool to check disk usage and evaluate."
            ],
            "tool_name": "code_execution_tool",
            "tool_args": {
                "runtime": "terminal",
                "code": "df -h | awk '$5 > 80 {print $0}'"
            }
        }
        """,
        """
        {
            "thoughts": [
                "Fetch user details from an API and send reminder emails for inactive users.",
                "I will first use the knowledge_tool to fetch user details and then process each user."
            ],
            "tool_name": "knowledge_tool",
            "tool_args": {
                "operation": "fetch_user_details"
            }
        }
        """,
        """
        {
            "thoughts": [
                "The user requests a performance report from 'sales_data.xlsx'.",
                "I will process the data and generate a PDF report."
            ],
            "tool_name": "code_execution_tool",
            "tool_args": {
                "runtime": "python",
                "code": "import pandas as pd; import matplotlib.pyplot as plt; df = pd.read_excel('sales_data.xlsx'); report = df.describe(); report.to_pdf('performance_report.pdf')"
            }
        }
        """,
        """
        {
            "thoughts": [
                "Update the Git repository with the latest changes and resolve conflicts.",
                "I will use the code_execution_tool to pull changes and handle conflicts."
            ],
            "tool_name": "code_execution_tool",
            "tool_args": {
                "runtime": "terminal",
                "code": "git pull origin main && git mergetool"
            }
        }
        """,
        """
        {
            "thoughts": [
                "Set up a daily cron job for backing up the 'project' directory.",
                "I will add the cron job and then verify its setup."
            ],
            "tool_name": "code_execution_tool",
            "tool_args": {
                "runtime": "terminal",
                "code": "echo '0 2 * * * tar -czf /backup/project_$(date +\\%F).tar.gz /path/to/project' | crontab - && crontab -l"
            }
        }
        """,
        """
        {
            "thoughts": [
                "Retrieve and summarize the latest blog posts from the company website.",
                "I will use the knowledge_tool to fetch and process blog posts."
            ],
            "tool_name": "knowledge_tool",
            "tool_args": {
                "operation": "fetch_blog_posts",
                "count": 3
            }
        }
        """,
        """
        {
            "thoughts": [
                "Configure and verify a new firewall rule to block a specific IP.",
                "I will use the code_execution_tool to configure the rule and then check it."
            ],
            "tool_name": "code_execution_tool",
            "tool_args": {
                "runtime": "terminal",
                "code": "sudo iptables -A INPUT -s 192.168.1.100 -j DROP && sudo iptables -L"
            }
        }
        """
    ],
    'system_output': [
        "Top 5 errors: [Error A: 12 occurrences, Error B: 9 occurrences, ...]",
        "Virtual environment created and Flask app 'app.py' written successfully.",
        "CSV files merged into 'combined_data.csv'.",
        "Disk usage is at 85%, alert triggered.",
        "Reminder emails sent to users with inactive status.",
        "Performance report generated and saved as 'performance_report.pdf'.",
        "Local repository updated with remote changes. Merge conflicts resolved.",
        "Cron job set up for daily backups. Verification successful.",
        "Top 3 blog posts summarized and saved.",
        "Firewall rule configured to block IP 192.168.1.100. Rule is active."
    ],
    'metadata': [
        "Analyze and summarize errors from log file",
        "Set up Python environment and create a Flask app",
        "Merge multiple CSV files into one",
        "Check disk usage and alert if over threshold",
        "Fetch user details and handle inactive users",
        "Generate and export a performance report",
        "Update and manage Git repository",
        "Set up and verify daily backup cron job",
        "Summarize latest blog posts",
        "Configure and verify firewall rule"
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
df.to_parquet('advanced_finetuning7.pq', engine='pyarrow', index=False)

print("Advanced Parquet file with new prompts created successfully.")
