"""
Script to install the FAISS GPU version.
This script will:
1. Uninstall any existing FAISS installations
2. Install the faiss-gpu package compatible with the system's CUDA version
"""

import os
import sys
import subprocess
import platform
from typing import Tuple, Optional

def run_command(command: str) -> Tuple[int, str, str]:
    """Run a shell command and return the exit code, stdout and stderr."""
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True,
        universal_newlines=True
    )
    stdout, stderr = process.communicate()
    return process.returncode, stdout, stderr

def get_cuda_version() -> Optional[str]:
    """Get the CUDA version if installed."""
    try:
        # Try running nvcc (CUDA compiler)
        exitcode, stdout, stderr = run_command("nvcc --version")
        if exitcode == 0:
            # Extract version from output
            for line in stdout.split('\n'):
                if 'release' in line.lower() and 'V' in line:
                    version = line.split('V')[1].split(' ')[0]
                    # Return just the major.minor version (e.g., 11.2)
                    version_parts = version.split('.')
                    if len(version_parts) >= 2:
                        return f"{version_parts[0]}{version_parts[1]}"
                    return version.replace('.', '')
        return None
    except Exception:
        return None

def uninstall_existing_faiss():
    """Uninstall any existing FAISS installations."""
    print("Uninstalling any existing FAISS packages...")
    
    # Uninstall different FAISS variants
    packages = ["faiss", "faiss-cpu", "faiss-gpu"]
    
    for package in packages:
        print(f"Checking for {package}...")
        exitcode, stdout, stderr = run_command(f"pip show {package}")
        
        if exitcode == 0:
            print(f"  Found {package}. Uninstalling...")
            exitcode, stdout, stderr = run_command(f"pip uninstall -y {package}")
            if exitcode == 0:
                print(f"  Successfully uninstalled {package}")
            else:
                print(f"  Failed to uninstall {package}")
                print(f"  Error: {stderr}")
        else:
            print(f"  {package} not installed. Skipping.")

def install_faiss_gpu(cuda_version: Optional[str] = None):
    """Install the appropriate faiss-gpu package based on CUDA version."""
    if cuda_version:
        # For specific CUDA versions, install the matching faiss-gpu version
        if cuda_version.startswith("11"):
            # For CUDA 11.x
            print(f"Installing faiss-gpu for CUDA {cuda_version}...")
            command = "pip install faiss-gpu==1.7.2+cu113"  # Use 11.3 compatibility
        elif cuda_version.startswith("10"):
            # For CUDA 10.x
            print(f"Installing faiss-gpu for CUDA {cuda_version}...")
            command = "pip install faiss-gpu==1.7.2+cu102"  # Use 10.2 compatibility
        else:
            # For other CUDA versions, try the latest
            print(f"CUDA version {cuda_version} detected. Installing latest faiss-gpu...")
            command = "pip install faiss-gpu"
    else:
        # If no CUDA version detected, warn but install the latest anyway
        print("WARNING: CUDA not detected but installing faiss-gpu anyway.")
        print("This will NOT work without a compatible NVIDIA GPU and CUDA installation.")
        command = "pip install faiss-gpu"
    
    # Install faiss-gpu
    exitcode, stdout, stderr = run_command(command)
    
    if exitcode == 0:
        print("\n✓ Successfully installed faiss-gpu!")
        print(stdout)
    else:
        print("\n✗ Failed to install faiss-gpu!")
        print(f"Error: {stderr}")

def main():
    """Main function."""
    print("\n===== FAISS GPU Installation Script =====\n")
    
    # Check CUDA version
    cuda_version = get_cuda_version()
    if cuda_version:
        print(f"CUDA version {cuda_version} detected.")
    else:
        print("WARNING: CUDA not detected on this system.")
        print("FAISS GPU requires an NVIDIA GPU with CUDA installed.")
        user_input = input("Do you want to continue anyway? (y/n): ")
        if user_input.lower() != 'y':
            print("Installation aborted.")
            return
    
    # Uninstall existing FAISS packages
    uninstall_existing_faiss()
    
    # Install faiss-gpu
    install_faiss_gpu(cuda_version)
    
    # Print next steps
    print("\n===== Next Steps =====\n")
    print("To verify the installation, run:")
    print("python scripts/check_faiss_gpu.py")
    print("\nRestart the application for changes to take effect.")

if __name__ == "__main__":
    main()
