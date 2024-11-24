"""
This script provides a quick way to activate the conda environment
created by the installation process.
"""

import platform
import subprocess
from utils.install_utils import InstallationManager

def main():
    # Initialize installation manager
    install_mgr = InstallationManager()

    # Check if conda installation exists
    if not install_mgr.conda_dir.exists():
        print("Conda installation not found. Please run start_cli.py or start_webui.py first.")
        return

    # Prepare activation command
    if platform.system().lower() == "windows":
        activate_cmd = f"call {install_mgr.activate_script} {install_mgr.env_name}"
        # On Windows, open a new command prompt with the environment activated
        cmd = f"start cmd /K {activate_cmd}"
        subprocess.run(cmd, shell=True, check=True)
    else:
        # For Unix-like systems, print the command for users to copy
        activate_cmd = f"source {install_mgr.activate_script} {install_mgr.env_name}"
        print("\nTo activate the environment, copy and run this command in your terminal:")
        print(f"\n    {activate_cmd}\n")

if __name__ == "__main__":
    main()
