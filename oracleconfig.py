import os
import subprocess
import platform
import configparser
import json
import sys
import logging
import traceback

# Setup logging immediately
log_file = "C:\\Temp\\configure_java_ide.log"
try:
    os.makedirs("C:\\Temp", exist_ok=True)
    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        force=True
    )
    logging.info("Script started successfully.")
except Exception as e:
    print(f"Failed to setup logging to {log_file}: {e}")
    sys.exit(1)

def find_java_home():
    """Attempt to find the Java installation path (JAVA_HOME)."""
    try:
        java_home = os.environ.get("JAVA_HOME")
        if java_home and os.path.exists(java_home):
            logging.info(f"Found JAVA_HOME in environment: {java_home}")
            return java_home

        possible_paths = [
            "C:\\Program Files\\Java\\jdk-24",  # Your JDK version
            "C:\\Program Files\\Java\\jdk-17",
            "C:\\Program Files\\Java\\jdk-21",
            "C:\\Program Files\\Java\\jdk-11",
        ]

        for path in possible_paths:
            if os.path.exists(path):
                logging.info(f"Found Java at: {path}")
                return path

        result = subprocess.check_output("where java", shell=True).decode().splitlines()
        if result:
            java_bin = result[0]
            java_home = os.path.dirname(os.path.dirname(java_bin))
            if os.path.exists(java_home):
                logging.info(f"Found Java via 'where java': {java_home}")
                return java_home
    except Exception as e:
        logging.error(f"Error finding Java: {e}")
        print(f"Error finding Java: {e}")

    print("Could not find Java installation automatically.")
    java_home = input("Enter the path to your Java JDK (e.g., C:\\Program Files\\Java\\jdk-24): ").strip()
    if os.path.exists(java_home):
        logging.info(f"User provided Java path: {java_home}")
        return java_home
    else:
        logging.error(f"Invalid Java path provided: {java_home}")
        print(f"Invalid path: {java_home}")
        return None

def set_environment_variable(java_home):
    """Set JAVA_HOME environment variable if not already set."""
    try:
        if os.environ.get("JAVA_HOME"):
            print("JAVA_HOME already set.")
            logging.info("JAVA_HOME already set in environment.")
            return

        subprocess.run(
            f'setx JAVA_HOME "{java_home}" /M',
            shell=True,
            check=True
        )
        print("JAVA_HOME set in system environment variables.")
        logging.info(f"Set JAVA_HOME to {java_home}")
    except subprocess.CalledProcessError as e:
        print("Error: Failed to set JAVA_HOME. Ensure you are running as Administrator.")
        print("To set JAVA_HOME manually:")
        print(f"1. Open System Properties > Advanced > Environment Variables.")
        print(f"2. Under System Variables, add JAVA_HOME = {java_home}.")
        logging.error(f"Failed to set JAVA_HOME: {e}")
    except Exception as e:
        logging.error(f"Unexpected error setting JAVA_HOME: {e}")
        print(f"Error setting JAVA_HOME: {e}")

def configure_netbeans(java_home):
    """Configure NetBeans to use the specified Java installation."""
    netbeans_configs = [
        "C:\\Program Files\\NetBeans-25\\netbeans\\etc\\netbeans.conf",
        "C:\\Users\\thoma\\AppData\\Roaming\\NetBeans\\25\\etc\\netbeans.conf"
    ]
    
    print("\nNetBeans configuration paths:")
    for path in netbeans_configs:
        print(f" - {path} {'(exists)' if os.path.exists(path) else '(missing)'}")
    netbeans_conf = input("Enter the correct path to netbeans.conf or press Enter to try listed paths: ").strip()
    
    if not netbeans_conf:
        for path in netbeans_configs:
            if os.path.exists(path):
                netbeans_conf = path
                break
    else:
        if not os.path.exists(netbeans_conf):
            print(f"Invalid path: {netbeans_conf}")
            logging.error(f"Invalid NetBeans path provided: {netbeans_conf}")
            return

    if not netbeans_conf:
        print("NetBeans configuration file not found. Please verify the path.")
        logging.error("NetBeans configuration file not found.")
        return

    try:
        with open(netbeans_conf, "r") as f:
            lines = f.readlines()

        with open(netbeans_conf, "w") as f:
            for line in lines:
                if line.startswith("netbeans_jdkhome"):
                    f.write(f'netbeans_jdkhome="{java_home}"\n')
                else:
                    f.write(line)
            if not any(line.startswith("netbeans_jdkhome") for line in lines):
                f.write(f'netbeans_jdkhome="{java_home}"\n')
        print(f"Updated NetBeans configuration at {netbeans_conf}.")
        logging.info(f"Updated NetBeans configuration at {netbeans_conf}")
    except Exception as e:
        print(f"Error configuring NetBeans: {e}")
        logging.error(f"Error configuring NetBeans: {e}")

def configure_eclipse(java_home):
    """Configure Eclipse to use the specified Java installation."""
    eclipse_configs = [
        "C:\\Users\\thoma\\eclipse\\cpp-2025-03\\eclipse\\eclipse.ini",
        "C:\\Users\\thoma\\eclipse\\java-2025-03\\eclipse\\eclipse.ini"
    ]

    jvm_path = os.path.join(java_home, "bin", "javaw.exe")
    if not os.path.exists(jvm_path):
        print(f"Java executable not found at {jvm_path}. Using 'java' instead.")
        jvm_path = os.path.join(java_home, "bin", "java.exe")
        logging.warning(f"Using java.exe instead of javaw.exe: {jvm_path}")

    print("\nEclipse configuration paths:")
    for path in eclipse_configs:
        print(f" - {path} {'(exists)' if os.path.exists(path) else '(missing)'}")
    print("Enter the path to eclipse.ini or press Enter to try listed paths.")
    print("To configure multiple, run the script separately for each.")
    eclipse_ini = input("Path: ").strip()

    if not eclipse_ini:
        eclipse_ini_list = [path for path in eclipse_configs if os.path.exists(path)]
    else:
        eclipse_ini_list = [eclipse_ini] if os.path.exists(eclipse_ini) else []

    if not eclipse_ini_list:
        print("No valid Eclipse configuration files found.")
        logging.error("No valid Eclipse configuration files found.")
        return

    for eclipse_ini in eclipse_ini_list:
        try:
            with open(eclipse_ini, "r") as f:
                lines = f.readlines()

            vm_set = False
            with open(eclipse_ini, "w") as f:
                for line in lines:
                    if line.startswith("-vm"):
                        f.write("-vm\n")
                        f.write(f"{jvm_path}\n")
                        vm_set = True
                    elif line.strip() == jvm_path:
                        continue
                    else:
                        f.write(line)
                if not vm_set:
                    f.write("-vm\n")
                    f.write(f"{jvm_path}\n")
            print(f"Updated Eclipse configuration at {eclipse_ini}.")
            logging.info(f"Updated Eclipse configuration at {eclipse_ini}")
        except Exception as e:
            print(f"Error configuring Eclipse at {eclipse_ini}: {e}")
            logging.error(f"Error configuring Eclipse at {eclipse_ini}: {e}")

def configure_vscode(java_home):
    """Configure Visual Studio Code to use the specified Java installation."""
    settings_path = "C:\\Users\\thoma\\AppData\\Roaming\\Code\\User\\settings.json"
    
    if not os.path.exists(settings_path):
        print(f"VS Code configuration file not found at {settings_path}.")
        logging.error(f"VS Code configuration file not found: {settings_path}")
        return

    try:
        settings = {}
        if os.path.exists(settings_path):
            with open(settings_path, "r") as f:
                settings = json.load(f)

        settings["java.home"] = java_home
        settings["java.jdt.ls.java.home"] = java_home

        with open(settings_path, "w") as f:
            json.dump(settings, f, indent=4)
        print(f"Updated VS Code configuration at {settings_path}.")
        logging.info(f"Updated VS Code configuration at {settings_path}")
    except Exception as e:
        print(f"Error configuring VS Code: {e}")
        logging.error(f"Error configuring VS Code: {e}")

def main():
    print("Configuring Oracle Java for NetBeans, Eclipse, and VS Code...")
    logging.info("Starting configuration process.")

    try:
        java_home = find_java_home()
        if not java_home:
            print("Error: Could not find or set Oracle Java installation.")
            logging.error("Failed to find or set Java installation.")
            sys.exit(1)
        print(f"Found Java installation at: {java_home}")

        set_environment_variable(java_home)
        configure_netbeans(java_home)
        configure_eclipse(java_home)
        configure_vscode(java_home)

        print("\nConfiguration complete. Please restart your IDEs to apply changes.")
        print(f"Logs saved to: {log_file}")
        logging.info("Configuration process completed.")
    except Exception as e:
        print(f"Unexpected error: {e}")
        logging.error(f"Unexpected error: {e}\n{traceback.format_exc()}")
    
    input("Press Enter to exit...")

if __name__ == "__main__":
    main()