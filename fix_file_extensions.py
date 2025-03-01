#!/usr/bin/env python3
import os
import re

def fix_file_extensions(root_dir):
    """
    Recursively fix file extensions in the given directory.
    Specifically, it looks for files with 'pdf' in the name but without a .pdf extension.
    """
    # Pattern to match files that have 'pdf' in the name but don't end with '.pdf'
    pdf_pattern = re.compile(r'pdf.*$')
    
    count = 0
    dirs_visited = 0
    files_checked = 0
    
    print(f"Starting to scan directories from: {root_dir}")
    
    for root, dirs, files in os.walk(root_dir):
        dirs_visited += 1
        if dirs_visited % 100 == 0:
            print(f"Visited {dirs_visited} directories...")
        
        # Print current directory being processed
        print(f"Checking directory: {root}")
        
        for filename in files:
            files_checked += 1
            if files_checked % 1000 == 0:
                print(f"Checked {files_checked} files so far...")
                
            # Skip files that already have a .pdf extension
            if filename.endswith('.pdf'):
                continue
            
            # Look for 'pdf' in the filename
            if 'pdf' in filename:
                # Check if it matches our pattern (contains pdf but doesn't end with .pdf)
                old_path = os.path.join(root, filename)
                
                # Extract the part before 'pdf' and the uniqueness suffix after 'pdf'
                match = pdf_pattern.search(filename)
                if match:
                    start_pos = match.start()
                    # Get the part before 'pdf'
                    name_part = filename[:start_pos]
                    # Get the suffix (usually an ID) that follows 'pdf' 
                    id_part = filename[start_pos + 3:]  # skip 'pdf'
                    
                    # Create new filename with proper .pdf extension
                    new_filename = f"{name_part}{id_part}.pdf"
                    new_path = os.path.join(root, new_filename)
                    
                    # Rename the file
                    os.rename(old_path, new_path)
                    count += 1
                    print(f"Renamed: {filename} -> {new_filename}")
    
    print(f"Scan complete!")
    print(f"Directories visited: {dirs_visited}")
    print(f"Files checked: {files_checked}")
    print(f"Total files renamed: {count}")

if __name__ == "__main__":
    # Path to the directory to process
    root_dir = "/Users/ofekedut/development/otech/projects/lior_arbivv/server/features/docs_processing/monday_assets_bar"
    fix_file_extensions(root_dir)
