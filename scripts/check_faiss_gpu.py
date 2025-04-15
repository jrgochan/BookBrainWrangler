"""
Script to check FAISS GPU support and provide installation guidance.
"""

import os
import sys
import importlib.util
import subprocess
from typing import List, Tuple

def check_package_installed(package_name: str) -> bool:
    """Check if a package is installed."""
    return importlib.util.find_spec(package_name) is not None

def check_cuda_version() -> Tuple[bool, str]:
    """Check if CUDA is installed and return version."""
    try:
        # Try running nvcc (CUDA compiler driver)
        result = subprocess.run(['nvcc', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            # Extract version from output
            output = result.stdout
            for line in output.split('\n'):
                if 'release' in line.lower() and 'V' in line:
                    version = line.split('V')[1].split(' ')[0]
                    return True, version
            return True, "Unknown version"
        return False, ""
    except FileNotFoundError:
        return False, ""

def check_pytorch_cuda() -> Tuple[bool, str]:
    """Check if PyTorch is using CUDA."""
    if not check_package_installed('torch'):
        return False, "PyTorch not installed"
    
    import torch
    if torch.cuda.is_available():
        return True, f"CUDA available (Device count: {torch.cuda.device_count()}, Device: {torch.cuda.get_device_name(0) if torch.cuda.device_count() > 0 else 'None'})"
    else:
        return False, "CUDA not available for PyTorch"

def check_faiss_gpu() -> Tuple[bool, str]:
    """Check if FAISS GPU support is available."""
    if not check_package_installed('faiss'):
        return False, "FAISS not installed"
    
    try:
        import faiss
        faiss_str = str(dir(faiss))
        
        # Check for GPU support in FAISS
        if 'GpuIndexFlatConfig' in faiss_str:
            # Check CUDA resources
            try:
                res = faiss.StandardGpuResources()
                return True, "FAISS GPU support available (StandardGpuResources initialized successfully)"
            except Exception as e:
                return False, f"FAISS has GPU types but CUDA error occurred: {str(e)}"
        else:
            # Check if using CPU-only FAISS
            has_avx = hasattr(faiss, 'IndexFlatL2_avx2')
            return False, f"CPU-only FAISS detected (AVX extensions: {'Yes' if has_avx else 'No'})"
    except ImportError as e:
        return False, f"Error importing FAISS: {str(e)}"
    except Exception as e:
        return False, f"Error checking FAISS GPU support: {str(e)}"

def get_installation_instructions(has_cuda: bool) -> str:
    """Get installation instructions based on environment."""
    if has_cuda:
        return """
To install FAISS with GPU support:

1. Ensure you have CUDA toolkit 10.0+ installed
2. Uninstall existing FAISS:
   pip uninstall -y faiss-cpu faiss faiss-gpu

3. Install FAISS with GPU support:
   pip install faiss-gpu

   # For specific CUDA versions:
   # pip install faiss-gpu==1.7.2+cu113  # For CUDA 11.3 (adjust version as needed)
   # pip install faiss-gpu==1.7.2+cu102  # For CUDA 10.2 (adjust version as needed)

4. Restart your application and check again
"""
    else:
        return """
GPU is not available on this system.

You are currently using the CPU version of FAISS, which is correct for a system without a CUDA-compatible GPU.

If you believe your system should have GPU support:
1. Install NVIDIA CUDA toolkit 10.0+
2. Install PyTorch with CUDA support
3. Then install FAISS with GPU support:
   pip install faiss-gpu
"""

def main():
    """Main function to check FAISS GPU support."""
    print("\n===== FAISS GPU Support Diagnostic =====\n")
    
    # Check CUDA
    has_cuda, cuda_version = check_cuda_version()
    print(f"CUDA Installation: {'Yes - ' + cuda_version if has_cuda else 'No'}")
    
    # Check PyTorch CUDA
    pytorch_cuda, pytorch_msg = check_pytorch_cuda()
    print(f"PyTorch CUDA: {'Yes' if pytorch_cuda else 'No'} - {pytorch_msg}")
    
    # Check FAISS GPU
    faiss_gpu, faiss_msg = check_faiss_gpu()
    print(f"FAISS GPU Support: {'Yes' if faiss_gpu else 'No'} - {faiss_msg}")
    
    # Overall status
    print("\n===== Diagnostic Summary =====\n")
    if faiss_gpu:
        print("✓ FAISS GPU support is properly configured!")
    else:
        print("✗ FAISS GPU support is not available.")
        
    # Print relevant installation instructions
    print("\n===== Installation Instructions =====\n")
    print(get_installation_instructions(has_cuda or pytorch_cuda))

if __name__ == "__main__":
    main()
