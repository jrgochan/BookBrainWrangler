# FAISS GPU Support

This document explains the requirements and configuration options for using GPU acceleration with FAISS in Book Brain Wrangler.

## System Requirements

To use FAISS with GPU acceleration, you need:

1. **NVIDIA GPU**: A CUDA-compatible NVIDIA GPU
2. **CUDA Toolkit**: NVIDIA CUDA Toolkit installed (version 10.0 or newer)
3. **faiss-gpu**: The GPU version of FAISS installed

## Current System Status

The diagnostic script (`scripts/check_faiss_gpu.py`) shows that your system:
- Does not have CUDA installed
- Is using the CPU-only version of FAISS
- Cannot use GPU acceleration without installing CUDA

This is normal for systems without an NVIDIA GPU. The application will continue to work correctly using CPU-based vector search.

## CPU vs. GPU Performance

- **CPU Version (faiss-cpu)**: Works on all systems, good performance for smaller knowledge bases
- **GPU Version (faiss-gpu)**: Much faster for large knowledge bases, but requires NVIDIA GPU with CUDA

## Installing CUDA (For NVIDIA GPU Systems Only)

If you have a compatible NVIDIA GPU and want to enable GPU acceleration:

1. Install the [NVIDIA CUDA Toolkit](https://developer.nvidia.com/cuda-downloads)
2. Install the PyTorch CUDA version
3. Run the installation script:

```
python scripts/install_faiss_gpu.py
```

## Checking GPU Support

To check if GPU support is available and properly configured:

```
python scripts/check_faiss_gpu.py
```

## Settings in Book Brain Wrangler

The application will automatically detect whether GPU support is available:

- If FAISS GPU support is available, a toggle will be shown in Settings → Knowledge Base to enable/disable it
- If GPU support is not available, the toggle will be disabled with an explanation

## References

- [FAISS GitHub Repository](https://github.com/facebookresearch/faiss)
- [FAISS GPU Documentation](https://github.com/facebookresearch/faiss/wiki/Faiss-on-the-GPU)
- [NVIDIA CUDA Toolkit](https://developer.nvidia.com/cuda-toolkit)
