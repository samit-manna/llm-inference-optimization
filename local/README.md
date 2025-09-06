# Local LLM Inference Setup

This directory contains the local inference implementation using llama.cpp on macOS with Apple Silicon.

## 🏗️ Architecture

- **llama.cpp**: High-performance C++ inference engine
- **Apple Silicon**: M4 Mac with Metal GPU acceleration
- **Quantized Models**: Optimized for local hardware constraints
- **Native Performance**: Direct hardware access for maximum efficiency

## 📁 Directory Structure

```
local/
├── Makefile              # Build and benchmark automation
├── llama.cpp/            # Submodule: llama.cpp inference engine
└── bench_old/            # Legacy benchmarking results
```

## 🚀 Quick Start

### Prerequisites
- macOS with Apple Silicon (M1/M2/M3/M4)
- Xcode Command Line Tools
- CMake and build essentials

### Setup
```bash
make setup
```

### Run Benchmarks
```bash
make bench
```

### Model Management
```bash
make download-model    # Download quantized model
make clean            # Clean build artifacts
```

## 💰 Cost Considerations

- **Estimated Cost**: ~$0.0045/hour (power consumption only)
- **Hardware**: Uses existing Mac hardware
- **Recommendation**: Ideal for development, testing, and prototyping

## 📊 Performance Characteristics

- **Power Efficient**: Excellent performance per watt
- **Development Friendly**: Fast iteration cycles
- **Hardware Limited**: Constrained by local GPU memory
- **Quantization Optimized**: Uses INT4/INT8 for efficiency

## ⚙️ Model Configuration

Supported quantization formats:
- **Q4_0**: 4-bit quantization, good balance
- **Q8_0**: 8-bit quantization, higher quality
- **F16**: Half precision, maximum quality

## 🔧 Troubleshooting

Common issues:
- **Memory Limits**: Reduce context length or use smaller quantization
- **Build Errors**: Ensure Xcode tools are up to date
- **Performance**: Enable Metal GPU acceleration

For detailed setup instructions, see the project root README.md.
