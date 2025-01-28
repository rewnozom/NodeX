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

def read_requirements(category):
    """Read requirements from specific category file"""
    try:
        filepath = os.path.join("Config", "setup", f"{category}.txt")
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                return [line.strip() for line in f if line.strip() and not line.startswith("#")]
    except Exception as e:
        print(f"Warning: Could not read {category} requirements: {e}")
    return []

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

        # Read all requirements from category files
        requirement_categories = ['ai', 'gui', 'data', 'web', 'dev', 'text']
        all_requirements = []
        for category in requirement_categories:
            reqs = read_requirements(category)
            print(f"\nInstalling {category.upper()} dependencies...")
            for req in reqs:
                try:
                    subprocess.check_call([venv_pip, "install", req])
                except subprocess.CalledProcessError as e:
                    print(f"Warning: Failed to install {req}. Error: {e}")
                all_requirements.extend(reqs)

        # Install the package in development mode
        print("\nInstalling package in development mode...")
        subprocess.check_call([venv_python, "-m", "pip", "install", "-e", "."])

        print("\nVirtual environment setup complete!")
        print("\nTo activate the virtual environment, run:")
        print(f"    {activate_cmd}")
        print("\nThen you can run the application with:")
        print("    python -m your_main_module")

# Collect all requirements for setup
all_requirements = []
requirement_categories = ['ai', 'gui', 'data', 'web', 'dev', 'text']
for category in requirement_categories:
    all_requirements.extend(read_requirements(category))

setup(
    name="DynamicPyside6",
    author="TobiasRaanaes",
    description="Dynamic PySide6 Application with AI agent chat",
    long_description=read_file("README.md"),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.10",
    install_requires=all_requirements,
    entry_points={
        "console_scripts": [
            "dynamic-pyside6=your_package.main:main",
        ],
    },
    package_data={
        "your_package": [
            "Config/setup/*.txt",
            "System_Prompts/*.md",
            "chat_history/*.json",
            "Workspace/**/*",
        ],
    },
    include_package_data=True,
    cmdclass={
        'install': CustomInstallCommand,
    },
)