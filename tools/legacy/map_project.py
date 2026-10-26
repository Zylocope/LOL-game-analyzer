import os

# Folders to ignore (to keep the list readable)
IGNORE_DIRS = {
    'node_modules', 
    '.git', 
    '__pycache__', 
    '.venv', 
    'venv', 
    'build', 
    'dist',
    '.idea',
    '.vscode'
}

def map_project(start_path='.'):
    print(f"📂 Scanning Project Structure in: {os.path.abspath(start_path)}\n")
    
    for root, dirs, files in os.walk(start_path):
        # Filter out ignored directories
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        
        level = root.replace(start_path, '').count(os.sep)
        indent = ' ' * 4 * (level)
        folder_name = os.path.basename(root)
        
        # Don't print the root dot '.'
        if folder_name != '.':
            print(f"{indent}📁 {folder_name}/")
            
        subindent = ' ' * 4 * (level + 1)
        for f in files:
            print(f"{subindent}📄 {f}")

if __name__ == "__main__":
    map_project()