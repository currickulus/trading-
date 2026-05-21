import os
import platform
import glob

def find_folders(base_paths, search_term):
    """Search for folders matching the search_term in the given base_paths."""
    found_folders = []
    for base in base_paths:
        try:
            # Expand user home directory if needed
            base = os.path.expanduser(base)
            # Use glob to find matching folders recursively
            pattern = os.path.join(base, f"**/{search_term}")
            matches = glob.glob(pattern, recursive=True)
            for match in matches:
                if os.path.isdir(match):
                    found_folders.append(os.path.abspath(match))
        except Exception as e:
            print(f"Error searching in {base}: {e}")
    return found_folders

def list_eclipse_folders():
    """Find Eclipse installation and configuration folders."""
    print("\nSearching for Eclipse folders...")
    base_paths = [
        "C:\\Program Files",  # Windows
        "C:\\Program Files (x86)",
        "~/eclipse",  # macOS/Linux user directory
        "/Applications",  # macOS
        "/usr/local",  # Linux
        "/opt"  # Linux
    ]
    search_terms = ["eclipse", "Eclipse", "*.ini"]  # Look for eclipse folders and eclipse.ini
    eclipse_folders = set()
    
    for term in search_terms:
        folders = find_folders(base_paths, term)
        for folder in folders:
            # Filter for folders containing eclipse.ini or Eclipse.app (macOS)
            if "eclipse.ini" in folder or os.path.basename(folder) == "eclipse" or "Eclipse.app" in folder:
                eclipse_folders.add(folder)
    
    if eclipse_folders:
        print("Found Eclipse folders:")
        for folder in sorted(eclipse_folders):
            print(f" - {folder}")
    else:
        print("No Eclipse folders found.")

def list_netbeans_folders():
    """Find NetBeans installation and configuration folders."""
    print("\nSearching for NetBeans folders...")
    base_paths = [
        "C:\\Program Files",  # Windows
        "C:\\Program Files (x86)",
        "~/netbeans",  # macOS/Linux user directory
        "/Applications",  # macOS
        "/usr/local",  # Linux
        "/opt",  # Linux
        "~/.netbeans"  # NetBeans user configuration
    ]
    search_terms = ["NetBeans", "netbeans", "netbeans.conf"]  # Look for NetBeans folders and config
    netbeans_folders = set()
    
    for term in search_terms:
        folders = find_folders(base_paths, term)
        for folder in folders:
            # Filter for folders containing netbeans.conf or NetBeans.app (macOS)
            if "netbeans.conf" in folder or os.path.basename(folder).startswith("NetBeans"):
                netbeans_folders.add(folder)
    
    if netbeans_folders:
        print("Found NetBeans folders:")
        for folder in sorted(netbeans_folders):
            print(f" - {folder}")
    else:
        print("No NetBeans folders found.")

def list_vscode_folders():
    """Find Visual Studio Code installation and configuration folders."""
    print("\nSearching for VS Code folders...")
    base_paths = [
        "C:\\Program Files",  # Windows
        "C:\\Program Files (x86)",
        "~/AppData/Roaming/Code",  # Windows user config
        "/Applications",  # macOS
        "~/.config/Code",  # Linux/macOS user config
        "/usr/share",  # Linux
        "/opt"  # Linux
    ]
    search_terms = ["Code", "code", "settings.json"]  # Look for VS Code folders and settings
    vscode_folders = set()
    
    for term in search_terms:
        folders = find_folders(base_paths, term)
        for folder in folders:
            # Filter for folders containing settings.json or Code.app (macOS)
            if "settings.json" in folder or os.path.basename(folder).startswith("Visual Studio Code"):
                vscode_folders.add(folder)
    
    if vscode_folders:
        print("Found VS Code folders:")
        for folder in sorted(vscode_folders):
            print(f" - {folder}")
    else:
        print("No VS Code folders found.")

def main():
    print("Listing Eclipse, NetBeans, and VS Code folders...")
    print(f"Operating System: {platform.system()} ({platform.release()})")
    
    list_eclipse_folders()
    list_netbeans_folders()
    list_vscode_folders()
    
    print("\nInstructions:")
    print("1. Review the listed folders above.")
    print("2. Identify the correct paths for Eclipse (eclipse.ini), NetBeans (netbeans.conf), and VS Code (settings.json).")
    print("3. Provide these paths to update the configuration script.")
    print("Note: If no folders are found, check your IDE installation or manually locate the folders.")

if __name__ == "__main__":
    main()