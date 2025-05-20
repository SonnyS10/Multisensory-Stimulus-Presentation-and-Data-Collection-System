import os

def replace_in_file(filepath, old, new):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        if old in content:
            content = content.replace(old, new)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Replaced in: {filepath}")
    except Exception as e:
        print(f"Could not process {filepath}: {e}")

def replace_in_folder(folder, old, new, skip_filename):
    for root, dirs, files in os.walk(folder):
        for file in files:
            # Only process text/code files and skip the name changer file
            if file == skip_filename:
                continue
            if file.endswith(('.py', '.txt', '.md', '.csv', '.json', '.yml', '.yaml', '.ini')):
                filepath = os.path.join(root, file)
                replace_in_file(filepath, old, new)

if __name__ == "__main__":
    # Set your folder path here
    folder_path = r"C:\Users\cpl4168\Documents\Paid Research\Software-for-Paid-Research-"
    # Choose which way you want to replace:
    old_string = "srs1520"
    new_string = "cpl4168"
    # To do the reverse, swap the above two lines

    skip_file = os.path.basename(__file__)
    replace_in_folder(folder_path, old_string, new_string, skip_file)