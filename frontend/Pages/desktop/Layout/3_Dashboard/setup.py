import os
import sys
import venv
import platform
import subprocess
from setuptools import setup, find_packages
from setuptools.command.install import install

# Read README.md for the long description
with open("README.md", encoding="utf-8") as f:
    long_description = f.read()

class CustomInstallCommand(install):
    def run(self):
        # Create virtual environment if it doesn't exist
        venv_dir = "env"
        if not os.path.exists(venv_dir):
            print(f"Creating virtual environment in {venv_dir}...")
            venv.create(venv_dir, with_pip=True)
            
            # Get the path to the Python executable in the virtual environment
            if platform.system() == "Windows":
                python_executable = os.path.join(venv_dir, "Scripts", "python.exe")
                pip_executable = os.path.join(venv_dir, "Scripts", "pip.exe")
                activate_cmd = f".\\{venv_dir}\\Scripts\\activate"
                ps_cmd = f".\\{venv_dir}\\Scripts\\Activate.ps1"
            else:
                python_executable = os.path.join(venv_dir, "bin", "python")
                pip_executable = os.path.join(venv_dir, "bin", "pip")
                activate_cmd = f"source {venv_dir}/bin/activate"

            # Install dependencies in the virtual environment
            print("Installing dependencies in virtual environment...")
            subprocess.check_call([pip_executable, "install", "PySide6>=6.0.0"])
            
            # Print activation instructions
            if platform.system() == "Windows":
                print("\nVirtual environment created! To activate it:")
                print(f"- Command Prompt: {activate_cmd}")
                print(f"- PowerShell: {ps_cmd}")
            else:
                print("\nVirtual environment created! To activate it:")
                print(f"Run: {activate_cmd}")

        # Run the standard install
        install.run(self)

setup(
    name="search-dashboard",
    version="1.0.0",
    author="Tobias R",
    description="A customizable search dashboard with AI prompt management",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "PySide6>=6.0.0",
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    cmdclass={
        'install': CustomInstallCommand,
    },
    entry_points={
        'console_scripts': [
            'search-dashboard=Dashboard.main_dashboard:main',
        ],
    }
)