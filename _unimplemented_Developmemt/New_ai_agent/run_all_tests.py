# run_all_tests.py

import sys
import os
from pathlib import Path
import asyncio
from ai_agent.testing.runner import TestRunner

# Add the project root to sys.path
project_root = Path(__file__).resolve().parents[2]  # Adjust based on your directory structure
sys.path.append(str(project_root))

async def main():
    # Define the working directory where temporary test files will be written
    work_dir = Path('temp_test_env')
    work_dir.mkdir(exist_ok=True)

    # Read all test files
    test_files = [
        'ai_agent/testing/integration/test_agent_workflow.py',
        'ai_agent/testing/integration/test_workflow.py',
        'ai_agent/testing/validators/test_validator.py'
    ]

    all_results = []

    runner = TestRunner(work_dir=str(work_dir))

    for test_file in test_files:
        with open(test_file, 'r') as f:
            tests = f.read()

        # Assuming you have corresponding code files, replace 'code_content' with actual code
        code_content = "your_code_here"  # Replace with actual code if needed

        result = await runner.run_tests(code=code_content, tests=tests)
        all_results.append(result)

    # Process and display results
    for res in all_results:
        print(res)

    # Cleanup
    try:
        work_dir.rmdir()
    except OSError:
        # Directory not empty or other error
        pass

if __name__ == '__main__':
    asyncio.run(main())
