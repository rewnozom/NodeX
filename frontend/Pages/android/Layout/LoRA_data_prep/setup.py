import os
import sys
import venv
import platform
import subprocess
from setuptools import setup, find_packages, Command
from setuptools.command.install import install

def read_file(filename):
    with open(filename, "r", encoding="utf-8") as fh:
        return fh.read()

class CustomInstallCommand(install):
    """Custom installation class that creates and activates a virtual environment."""
    
    def create_virtual_env(self):
        venv_dir = "env"
        if not os.path.exists(venv_dir):
            print(f"Creating virtual environment in {venv_dir}...")
            venv.create(venv_dir, with_pip=True)
            return True
        return False

    def get_venv_python(self):
        """Get the path to the virtual environment's Python executable."""
        if platform.system().lower() == "windows":
            return os.path.join("env", "Scripts", "python.exe")
        return os.path.join("env", "bin", "python")

    def get_venv_pip(self):
        """Get the path to the virtual environment's pip executable."""
        if platform.system().lower() == "windows":
            return os.path.join("env", "Scripts", "pip.exe")
        return os.path.join("env", "bin", "pip")

    def get_activation_script(self):
        """Get the appropriate activation command based on the platform."""
        system = platform.system().lower()
        venv_dir = "env"
        
        if system == "windows":
            if os.environ.get("SHELL") and "powershell" in os.environ["SHELL"].lower():
                activate_script = os.path.join(venv_dir, "Scripts", "Activate.ps1")
                return f"PowerShell -ExecutionPolicy Bypass -File {activate_script}"
            else:
                return os.path.join(venv_dir, "Scripts", "activate.bat")
        else:
            return f"source {os.path.join(venv_dir, 'bin', 'activate')}"

    def run(self):
        # Create virtual environment if it doesn't exist
        created_new = self.create_virtual_env()
        
        # Get virtual environment executables
        venv_python = self.get_venv_python()
        venv_pip = self.get_venv_pip()
        activate_cmd = self.get_activation_script()

        if not os.path.exists(venv_python):
            print("Error: Virtual environment Python not found!")
            return

        # Upgrade pip in virtual environment
        print("Upgrading pip in virtual environment...")
        subprocess.check_call([venv_python, "-m", "pip", "install", "--upgrade", "pip"])

        # Install the package in development mode inside the virtual environment
        print("Installing package in virtual environment...")
        subprocess.check_call([venv_python, "-m", "pip", "install", "-e", "."])

        print("\nVirtual environment setup complete!")
        print("\nTo activate the virtual environment, run:")
        print(f"    {activate_cmd}")
        print("\nThen you can run the application with:")
        print("    lora_prep")

setup(
    name="lora_data_prep",
    version="0.1.0",
    author="Your Name",
    description="LoRA training data preparation tool",
    long_description=read_file("README.md"),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.10",
    install_requires=[
        "PySide6>=6.0.0",
        "pandas>=1.3.0",
        "pyarrow>=5.0.0",
        "python-docx>=0.8.11",
        "openpyxl>=3.0.7",
        "rich>=10.0.0",
        "matplotlib>=3.4.0",
        "seaborn>=0.11.0",
        "nltk>=3.6.0",
        "tiktoken>=0.3.0",
        "icecream>=2.1.0",
        "openai>=1.0.0"
    ],
    entry_points={
        "console_scripts": [
            "lora_prep=LoRA_data_prep_text_llm.main_lora_prep:main",
        ],
    },
    package_data={
        "LoRA_data_prep_text_llm": [
            "System_Prompts/*.md",
            "chat_history/*.md",
            "random_parquet_examples/*.py",
            "random_parquet_examples/*.md",
        ],
    },
    include_package_data=True,
    cmdclass={
        'install': CustomInstallCommand,
    },
)