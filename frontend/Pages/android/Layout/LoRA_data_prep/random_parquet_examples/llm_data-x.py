import json
import pandas as pd

# Original data
data = {
    'prompt': [
        "seeing a spike in CPU usage on our main server. Investigate the cause, provide a detailed analysis, and recommend solutions to optimize performance.",
        "Create a Python script that processes our customer feedback data, performs sentiment analysis, and generates a visual report of the results.",
        "Develop a machine learning model to predict customer churn based on our historical data. Train the model, evaluate its performance, and prepare it for deployment."
    ],
    'agent_response': [
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
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from collections import Counter
import matplotlib.pyplot as plt
import seaborn as sns
from wordcloud import WordCloud
from flask import Flask, render_template_string
import base64
import io

# Ladda ner nödvändig NLTK-data
nltk.download('vader_lexicon')
nltk.download('punkt')
nltk.download('stopwords')

def preprocess_text(text):
    # Tokenisera och ta bort stopwords
    tokens = word_tokenize(text.lower())
    stop_words = set(stopwords.words('english'))
    return [word for word in tokens if word.isalnum() and word not in stop_words]

def analyze_sentiment(df):
    sia = SentimentIntensityAnalyzer()
    df['sentiment_scores'] = df['feedback'].apply(lambda x: sia.polarity_scores(x)['compound'])
    df['sentiment'] = df['sentiment_scores'].apply(lambda score: 'Positive' if score > 0.05 else ('Negative' if score < -0.05 else 'Neutral'))
    return df

def generate_visualizations(df):
    plt.figure(figsize=(12, 6))
    
    # Sentiment distribution
    plt.subplot(2, 2, 1)
    sns.countplot(x='sentiment', data=df)
    plt.title('Sentiment Distribution')
    
    # Sentiment scores histogram
    plt.subplot(2, 2, 2)
    sns.histplot(df['sentiment_scores'], kde=True)
    plt.title('Sentiment Scores Distribution')
    
    # Word cloud
    all_words = ' '.join([' '.join(preprocess_text(text)) for text in df['feedback']])
    wordcloud = WordCloud(width=800, height=400, background_color='white').generate(all_words)
    plt.subplot(2, 2, 3)
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    plt.title('Word Cloud of Feedback')
    
    # Top words bar chart
    word_freq = Counter([word for text in df['feedback'] for word in preprocess_text(text)])
    top_words = dict(sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10])
    plt.subplot(2, 2, 4)
    sns.barplot(x=list(top_words.values()), y=list(top_words.keys()))
    plt.title('Top 10 Words in Feedback')
    
    plt.tight_layout()
    
    # Save plot to a base64 encoded string
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    plot_data = base64.b64encode(buffer.getvalue()).decode()
    
    return plot_data

def create_app(df, plot_data):
    app = Flask(__name__)
    
    @app.route('/')
    def index():
        sentiment_counts = df['sentiment'].value_counts().to_dict()
        avg_score = df['sentiment_scores'].mean()
        
        html = f'''
        <html>
            <head>
                <title>Sentiment Analysis Report</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; }}
                    .container {{ max-width: 800px; margin: 0 auto; }}
                    h1 {{ color: #333; }}
                    .summary {{ background-color: #f0f0f0; padding: 15px; border-radius: 5px; }}
                    img {{ max-width: 100%; height: auto; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>Customer Feedback Sentiment Analysis</h1>
                    <div class="summary">
                        <h2>Summary</h2>
                        <p>Total feedbacks: {len(df)}</p>
                        <p>Positive: {sentiment_counts.get('Positive', 0)}</p>
                        <p>Neutral: {sentiment_counts.get('Neutral', 0)}</p>
                        <p>Negative: {sentiment_counts.get('Negative', 0)}</p>
                        <p>Average sentiment score: {avg_score:.2f}</p>
                    </div>
                    <h2>Visualizations</h2>
                    <img src="data:image/png;base64,{plot_data}" alt="Sentiment Analysis Visualizations">
                </div>
            </body>
        </html>
        '''
        return render_template_string(html)
    
    return app

def main():
    try:
        # Ladda data
        df = pd.read_csv('customer_feedback.csv')
        
        # Utför sentimentanalys
        df = analyze_sentiment(df)
        
        # Generera visualiseringar
        plot_data = generate_visualizations(df)
        
        # Skapa och kör Flask-app
        app = create_app(df, plot_data)
        print("Starting web server. Open a browser and navigate to http://127.0.0.1:5000/ to view the report.")
        app.run(debug=True)
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()
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
import numpy as np
from sklearn.model_selection import train_test_split, GridSearchCV, cross_val_score
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, roc_curve, auc
import matplotlib.pyplot as plt
import seaborn as sns
from imblearn.over_sampling import SMOTE
from sklearn.feature_selection import SelectFromModel

def load_and_preprocess_data(file_path):
    # Ladda data
    df = pd.read_csv(file_path)
    
    # Identifiera numeriska och kategoriska kolumner
    numeric_features = df.select_dtypes(include=['int64', 'float64']).columns
    categorical_features = df.select_dtypes(include=['object']).columns
    
    # Skapa preprocessing pipeline
    numeric_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', StandardScaler())
    ])
    
    categorical_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='constant', fill_value='missing')),
        ('onehot', OneHotEncoder(handle_unknown='ignore'))
    ])
    
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', numeric_transformer, numeric_features),
            ('cat', categorical_transformer, categorical_features)
        ])
    
    # Förbered X och y
    X = df.drop('churn', axis=1)
    y = df['churn']
    
    return X, y, preprocessor

def perform_feature_selection(X, y, preprocessor):
    # Skapa en pipeline med preprocessor och RandomForest
    pipeline = Pipeline([
        ('preprocessor', preprocessor),
        ('classifier', RandomForestClassifier(n_estimators=100, random_state=42))
    ])
    
    # Anpassa modellen och utför feature selection
    pipeline.fit(X, y)
    model = pipeline.named_steps['classifier']
    
    # Välj features baserat på importance
    selector = SelectFromModel(model, prefit=True
"""
            }
        })
    ],
    'system_output': [
        "top - 14:23:45 up 7 days, 2:03, 1 user, load average: 2.15, 2.30, 2.24\nTasks: 128 total, 1 running, 127 sleeping, 0 stopped, 0 zombie\n%Cpu(s): 75.2 us, 15.3 sy, 0.0 ni, 9.1 id, 0.0 wa, 0.0 hi, 0.4 si, 0.0 st\nMiB Mem : 16384.0 total, 2467.2 free, 10236.4 used, 3680.4 buff/cache\nMiB Swap: 8192.0 total, 8192.0 free, 0.0 used. 5147.6 avail Mem \n\n  PID USER PR NI VIRT RES SHR S %CPU %MEM TIME+ COMMAND\n 1518 root 20 0 4270716 1.2g 29292 S 157.0 7.6 908:47.25 java\n 3721 mysql 20 0 1329936 387768 37696 S 12.3 2.3 89:22.33 mysqld\n 1891 www-data 20 0 213944 20944 6756 S 0.3 0.1 0:45.01 apache2",
        "Sentiment analysis complete. Visual report generated as 'sentiment_analysis_report.png'.",
        "Model Accuracy: 0.85\n\nClassification Report:\n              precision    recall  f1-score   support\n\n           0       0.87      0.89      0.88       150\n           1       0.82      0.79      0.80       100\n\n    accuracy                           0.85       250\n   macro avg       0.84      0.84      0.84       250\nweighted avg       0.85      0.85      0.85       250\n\nMachine learning model for customer churn prediction has been trained and evaluated."
    ],
    'metadata': [
        "Server performance investigation scenario, demonstrating system diagnostics and analysis.",
        "Data processing task involving sentiment analysis of customer feedback and visualization of results.",
        "Machine learning model development for predicting customer churn, including training and evaluation."
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
df.to_parquet('advanced_finetuning8_modified.pq', engine='pyarrow', index=False)

print("Modified Parquet file created successfully.")
