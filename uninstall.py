import shutil
import os

def delete_directory(directory_path, description):
    """Helper function to delete a directory with confirmation."""
    if not os.path.exists(directory_path):
        print(f"Directory '{directory_path}' ({description}) does not exist. Skipping.")
        return

    print(f"WARNING: You are about to delete '{directory_path}' ({description}).")
    response = input("Are you sure you want to proceed? (yes/no): ").strip().lower()
    if response != "yes":
        print(f"Skipping deletion of '{directory_path}'.")
        return

    try:
        shutil.rmtree(directory_path)
        print(f"Successfully deleted '{directory_path}'.")
    except PermissionError as e:
        print(f"Error: Permission denied while deleting '{directory_path}'. {e}")
        print("Ensure VS Code is not running and you have permission. Try running as administrator.")
    except Exception as e:
        print(f"Error: Failed to delete '{directory_path}'. {e}")

def uninstall_vscode():
    print("This script will uninstall Visual Studio Code by deleting its directories.")
    print("Ensure you have backed up any important data (e.g., settings, extensions) before proceeding.\n")

    # Define VS Code directories
    vscode_dirs = [
        (r"C:\Users\thoma\vscode", "VS Code installation"),
        (r"C:\Users\thoma\AppData\Roaming\Code", "VS Code settings"),
        (r"C:\Users\thoma\.vscode", "VS Code extensions"),
    ]

    # Delete directories
    for dir_path, desc in vscode_dirs:
        delete_directory(dir_path, desc)

    print("\nVS Code uninstallation complete. Please check the directories to ensure all files are removed.")

if __name__ == "__main__":
    uninstall_vscode()