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
            if file == skip_filename:
                continue
            if file.endswith(('.py', '.txt', '.md', '.csv', '.json', '.yml', '.yaml', '.ini')):
                filepath = os.path.join(root, file)
                replace_in_file(filepath, old, new)

if __name__ == "__main__":
    # Try both folder paths
    base_path = r"C:\Users"
    folder1 = os.path.join(base_path, "srs1520", "Documents", "Paid Research", "Software-for-Paid-Research-")
    folder2 = os.path.join(base_path, "cpl4168", "Documents", "Paid Research", "Software-for-Paid-Research-")

    if os.path.exists(folder1):
        folder_path = folder1
        old_string = "cpl4168"
        new_string = "srs1520"
    elif os.path.exists(folder2):
        folder_path = folder2
        new_string = "srs1520"
        old_string = "cpl4168"
    else:
        print("Neither folder path exists.")
        exit(1)

    print(f"Swapping '{old_string}' with '{new_string}' in {folder_path}")

    skip_file = os.path.basename(__file__)
    replace_in_folder(folder_path, old_string, new_string, skip_file)