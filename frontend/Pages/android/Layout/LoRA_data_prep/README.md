# README.md
# LoRA Data Preparation Tool

A tool for preparing and processing training data for LoRA fine-tuning. This tool provides a graphical interface for managing and preprocessing data files with features for data validation, conversion, and analysis.

## Requirements

- Python 3.10 or higher
- Virtual environment (automatically created during installation)

## Installation

1. Install the package:
```bash
python setup.py install
```

The installation process will automatically:
- Create a virtual environment named 'env'
- Install all required dependencies
- Provide activation commands for your specific platform

2. Activate the virtual environment:

For Linux/Unix:
```bash
source env/bin/activate
```

For Windows PowerShell:
```powershell
.\env\Scripts\Activate.ps1
```

For Windows CMD:
```cmd
.\env\Scripts\activate.bat
```

## Features

- Data validation and preprocessing
- Format conversion (JSON/JSONL to Parquet)
- File management and organization
- Progress tracking and logging
- Interactive GUI interface
- Data analysis and visualization

## Usage

After installation and activating the virtual environment, start the application:

```bash
python main_lora_prep.py
```
