"""
This module contains the main function to start the web UI.
"""

import os
import platform
import subprocess
from pathlib import Path
from utils.install_utils import InstallationManager

# Set HF_HOME to models folder in project directory
os.environ["HF_HOME"] = str(Path(__file__).parent / "models")
os.environ["MODELSCOPE_CACHE"] = str(Path(__file__).parent / "models")


def main():
    # Initialize installation manager
    install_mgr = InstallationManager()

    # Ensure environment is set up
    if not install_mgr.conda_dir.exists():
        print("Conda installation not found. Running setup...")
        install_mgr.setup()

    # Activate environment and run server
    if platform.system().lower() == "windows":
        activate_cmd = f"call {install_mgr.activate_script} {install_mgr.env_name}"
    else:
        activate_cmd = f"source {install_mgr.activate_script} {install_mgr.env_name}"

    run_cmd = f"{activate_cmd} && python server.py"

    if platform.system().lower() == "windows":
        subprocess.run(run_cmd, shell=True, check=True)
    else:
        subprocess.run(["bash", "-c", run_cmd], check=True)


if __name__ == "__main__":
    main()
