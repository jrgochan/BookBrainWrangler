# Ollama Integration Test Scripts

This directory contains test scripts for validating the Ollama integration in BookBrainWrangler. These tests verify that the Ollama client can properly connect to an Ollama server and perform various operations such as model listing, text generation, chat interactions, and embedding creation.

## Requirements

- Python 3.8+
- Ollama server installed and running
- At least one model pulled in Ollama (e.g., `llama2`)

## Installation

Ollama needs to be installed and running on your system. If you haven't installed Ollama yet, follow these instructions:

### Windows

1. Download the installer from [Ollama's official website](https://ollama.ai/download)
2. Run the installer and follow the prompts
3. Launch Ollama from the Start menu

### macOS

1. Download the macOS app from [Ollama's official website](https://ollama.ai/download)
2. Install the app and launch it
3. Ollama will run in the menu bar

### Linux

```bash
curl -fsSL https://ollama.ai/install.sh | sh
ollama serve
```

## Pulling a Model

Before running tests, you need to pull at least one model:

```bash
ollama pull llama2
```

Other popular models include:
- `llama2:7b`
- `llama2:13b`
- `mistral`
- `gemma:2b`

## Running the Tests

### On Windows (PowerShell)

```powershell
cd scripts/ollama
.\run_tests.ps1 -model llama2 -wait -verbose
```

### On macOS/Linux (Bash)

```bash
cd scripts/ollama
chmod +x run_tests.sh
./run_tests.sh --model llama2 --wait --verbose
```

### Using Python Directly

```bash
cd scripts/ollama
python test_ollama.py --model llama2 --wait-for-server --verbose
```

## Command-line Options

Both the shell scripts and the Python script accept the following options:

| Option | Description |
|--------|-------------|
| `--host` | Ollama server host (default: from env OLLAMA_HOST or localhost) |
| `--port` | Ollama server port (default: from env OLLAMA_PORT or 11434) |
| `--model` | Model to test (default: llama2) |
| `--test` | Which tests to run: all, connectivity, models, generation, embeddings (default: all) |
| `--wait-for-server` | Wait for Ollama server to be available before starting tests |
| `--wait-timeout` | Maximum time to wait for server in seconds (default: 60) |
| `--verbose` | Enable verbose output |

## Test Categories

The test suite includes the following categories:

### Connectivity Tests
- Verifies basic socket connection to the Ollama server
- Checks if the API is available and responding

### Model Tests
- Lists available models on the Ollama server
- Retrieves detailed information about specific models

### Generation Tests
- Tests text generation with a sample prompt
- Tests chat generation with a conversation history
- Verifies handling of system prompts and context

### Embedding Tests
- Creates embeddings for sample texts
- Validates embedding vectors (dimensions, values, etc.)
- Calculates similarity between embeddings

## Examples

### Test only connectivity

```bash
./run_tests.sh --test connectivity
```

### Test with a specific model

```bash
./run_tests.sh --model mistral
```

### Test with a custom server

```bash
./run_tests.sh --host 192.168.1.100 --port 8080
```

## Troubleshooting

### Server Not Running

If the tests fail with "Server not running" errors, make sure:
1. Ollama is installed and running
2. The server is accessible at the specified host and port
3. Try using the `--wait-for-server` option to wait for the server to start

### No Models Available

If tests fail because no models are available:
1. Pull a model with `ollama pull llama2`
2. Verify it was pulled with `ollama list`
3. Use the exact model name from the list in your test command

### Generation/Embedding Failures

If text generation or embedding tests fail:
1. Ensure the model supports the operation (not all models support embeddings)
2. Try with a different model
3. Check if the model is fully downloaded and not corrupted

## Integration with BookBrainWrangler

These tests help ensure that the Ollama integration in BookBrainWrangler is working correctly. They can be run:
- During development to verify changes
- After updating Ollama to a new version
- When troubleshooting issues with AI functionality

The Ollama integration allows BookBrainWrangler to use local AI models for various tasks like text generation, chat, and embeddings, which are essential for the knowledge base functionality.
