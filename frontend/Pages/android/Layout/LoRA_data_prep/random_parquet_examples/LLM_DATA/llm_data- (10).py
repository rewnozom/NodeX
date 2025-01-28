import json

data = {
    'prompt': [
        "Analyze the performance of our e-commerce website over the past quarter. Generate a report with key metrics, identify areas for improvement, and suggest optimizations.",
        "seeing a spike in CPU usage on our main server. Investigate the cause, provide a detailed analysis, and recommend solutions to optimize performance.",
        "Create a Python script that processes our customer feedback data, performs sentiment analysis, and generates a visual report of the results.",
        "Our API is returning inconsistent results. Debug the issue, fix the code, and implement proper error handling and logging.",
        "Develop a machine learning model to predict customer churn based on our historical data. Train the model, evaluate its performance, and prepare it for deployment."
    ],
    'agent_response': [
        json.dumps({
            "thoughts": [
                "This is a complex task requiring multiple steps and tools.",
                "I'll need to gather data, perform analysis, and generate a report.",
                "I'll use the knowledge_tool to access relevant information and the code_execution_tool for data processing and visualization."
            ],
            "tool_name": "knowledge_tool",
            "tool_args": {
                "query": "e-commerce website performance metrics and KPIs"
            }
        }),
        json.dumps({
            "thoughts": [
                "This requires system investigation and performance analysis.",
                "I'll use the code_execution_tool to run diagnostics and gather data.",
                "Then, I'll analyze the results and propose optimizations."
            ],
            "tool_name": "code_execution_tool",
            "tool_args": {
                "runtime": "terminal",
                "code": "top -b -n 1 | head -n 20"
            }
        }),
        json.dumps({
            "thoughts": [
                "This task involves data processing, sentiment analysis, and visualization.",
                "I'll need to use Python libraries for NLP and data visualization.",
                "I'll create a script using the code_execution_tool and then run it."
            ],
            "tool_name": "code_execution_tool",
            "tool_args": {
                "runtime": "python",
                "code": """
import pandas as pd
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
import matplotlib.pyplot as plt

# Download necessary NLTK data
nltk.download('vader_lexicon')

# Load data (assuming it's in a CSV file)
df = pd.read_csv('customer_feedback.csv')

# Perform sentiment analysis
sia = SentimentIntensityAnalyzer()
df['sentiment_scores'] = df['feedback'].apply(lambda x: sia.polarity_scores(x)['compound'])

# Categorize sentiments
df['sentiment'] = df['sentiment_scores'].apply(lambda score: 'Positive' if score > 0 else ('Negative' if score < 0 else 'Neutral'))

# Generate visualization
plt.figure(figsize=(10, 6))
df['sentiment'].value_counts().plot(kind='bar')
plt.title('Customer Feedback Sentiment Analysis')
plt.xlabel('Sentiment')
plt.ylabel('Count')
plt.savefig('sentiment_analysis_report.png')
plt.close()

print("Sentiment analysis complete. Visual report generated as 'sentiment_analysis_report.png'.")
"""
            }
        }),
        json.dumps({
            "thoughts": [
                "This task involves debugging, code fixing, and implementing error handling.",
                "I'll first need to examine the API code and its logs.",
                "Then, I'll make necessary modifications and implement proper error handling."
            ],
            "tool_name": "code_execution_tool",
            "tool_args": {
                "runtime": "python",
                "code": """
import logging

logging.basicConfig(filename='api.log', level=logging.DEBUG)

def api_function(param):
    try:
        # Simulating the problematic part of the API
        result = some_operation(param)
        return result
    except Exception as e:
        logging.error(f"Error in api_function: {str(e)}")
        raise

def some_operation(param):
    # Implementation of the operation
    pass

# Test the API function
try:
    result = api_function("test_param")
    print(f"API returned: {result}")
except Exception as e:
    print(f"API call failed: {str(e)}")

print("API code updated with error handling and logging.")
"""
            }
        }),
        json.dumps({
            "thoughts": [
                "This task involves machine learning model development, training, and evaluation.",
                "I'll need to use Python with libraries like scikit-learn for this task.",
                "I'll create a script to load data, preprocess it, train a model, and evaluate its performance."
            ],
            "tool_name": "code_execution_tool",
            "tool_args": {
                "runtime": "python",
                "code": """
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
from sklearn.preprocessing import StandardScaler

# Load the data (assuming it's in a CSV file)
df = pd.read_csv('customer_data.csv')

# Preprocess the data
X = df.drop('churn', axis=1)
y = df['churn']

# Split the data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Scale the features
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# Train the model
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train_scaled, y_train)

# Make predictions
y_pred = model.predict(X_test_scaled)

# Evaluate the model
accuracy = accuracy_score(y_test, y_pred)
print(f"Model Accuracy: {accuracy:.2f}")
print("\nClassification Report:")
print(classification_report(y_test, y_pred))

print("Machine learning model for customer churn prediction has been trained and evaluated.")
"""
            }
        })
    ],
    'system_output': [
        "Retrieved information on e-commerce KPIs including conversion rate, average order value, customer acquisition cost, and customer lifetime value.",
        "top - 14:23:45 up 7 days, 2:03, 1 user, load average: 2.15, 2.30, 2.24\nTasks: 128 total, 1 running, 127 sleeping, 0 stopped, 0 zombie\n%Cpu(s): 75.2 us, 15.3 sy, 0.0 ni, 9.1 id, 0.0 wa, 0.0 hi, 0.4 si, 0.0 st\nMiB Mem : 16384.0 total, 2467.2 free, 10236.4 used, 3680.4 buff/cache\nMiB Swap: 8192.0 total, 8192.0 free, 0.0 used. 5147.6 avail Mem \n\n  PID USER PR NI VIRT RES SHR S %CPU %MEM TIME+ COMMAND\n 1518 root 20 0 4270716 1.2g 29292 S 157.0 7.6 908:47.25 java\n 3721 mysql 20 0 1329936 387768 37696 S 12.3 2.3 89:22.33 mysqld\n 1891 www-data 20 0 213944 20944 6756 S 0.3 0.1 0:45.01 apache2",
        "Sentiment analysis complete. Visual report generated as 'sentiment_analysis_report.png'.",
        "API code updated with error handling and logging.",
        "Model Accuracy: 0.85\n\nClassification Report:\n              precision    recall  f1-score   support\n\n           0       0.87      0.89      0.88       150\n           1       0.82      0.79      0.80       100\n\n    accuracy                           0.85       250\n   macro avg       0.84      0.84      0.84       250\nweighted avg       0.85      0.85      0.85       250\n\nMachine learning model for customer churn prediction has been trained and evaluated."
    ],
    'metadata': [
        "Complex task involving data analysis, report generation, and optimization suggestions for an e-commerce website.",
        "Server performance investigation scenario, demonstrating system diagnostics and analysis.",
        "Data processing task involving sentiment analysis of customer feedback and visualization of results.",
        "Debugging and error handling implementation for an inconsistent API.",
        "Machine learning model development for predicting customer churn, including training and evaluation."
    ]
}

# Verify that all lists have the same length
print("prompt length:", len(data['prompt']))
print("agent_response length:", len(data['agent_response']))
print("system_output length:", len(data['system_output']))
print("metadata length:", len(data['metadata']))

# Create a DataFrame
import pandas as pd
df = pd.DataFrame(data)

# Save the DataFrame as a Parquet file
df.to_parquet('advanced_finetuning8.pq', engine='pyarrow', index=False)

print("Advanced scenarios Parquet file created successfully.")