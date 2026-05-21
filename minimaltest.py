#minimaltest
import os
import logging
import sys

# Setup logging immediately
log_file = "C:\\Temp\\configure_java_ide.log"
try:
    os.makedirs("C:\\Temp", exist_ok=True)
    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )
    logging.info("Script started successfully.")
except Exception as e:
    print(f"Failed to setup logging: {e}")
    sys.exit(1)

def main():
    print("Testing script execution...")
    logging.info("Running main function.")
    print("Script is running.")
    print(f"Current directory: {os.getcwd()}")
    logging.info(f"Current directory: {os.getcwd()}")
    print(f"Log file should be at: {log_file}")
    input("Press Enter to exit...")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}")
        logging.error(f"Error in script: {e}")
        input("Press Enter to exit...")