import os

def create_init_files(start_path):
    """
    Create __init__.py files in all directories under the given path.
    
    Args:
        start_path (str): The root directory to start from
    """
    # Counter for created files
    created_count = 0
    skipped_count = 0
    
    # Walk through all directories
    for root, dirs, files in os.walk(start_path):
        init_file_path = os.path.join(root, '__init__.py')
        
        # Check if __init__.py already exists
        if '__init__.py' not in files:
            try:
                # Create empty __init__.py file
                with open(init_file_path, 'w') as f:
                    f.write('# Auto-generated __init__.py file\n')
                created_count += 1
                print(f"Created: {init_file_path}")
            except Exception as e:
                print(f"Error creating {init_file_path}: {str(e)}")
        else:
            skipped_count += 1
            print(f"Skipped existing: {init_file_path}")
    
    # Print summary
    print(f"\nSummary:")
    print(f"Created {created_count} __init__.py files")
    print(f"Skipped {skipped_count} existing __init__.py files")

if __name__ == '__main__':
    # Get the current directory (where the script is run from)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    print(f"Starting to create __init__.py files in: {current_dir}")
    print("=" * 50)
    
    # Create the files
    create_init_files(current_dir)