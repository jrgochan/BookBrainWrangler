#!/bin/bash
# Script to run Ollama integration tests

# Find the project root directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/../.." &> /dev/null && pwd )"

# Add the project root to PYTHONPATH
export PYTHONPATH=$PROJECT_ROOT:$PYTHONPATH

# Parse arguments
POSITIONAL=()
HOST=""
PORT=""
MODEL="llama2"
TEST="all"
WAIT=false
VERBOSE=false

while [[ $# -gt 0 ]]; do
  key="$1"
  case $key in
    --host)
      HOST="$2"
      shift
      shift
      ;;
    --port)
      PORT="$2"
      shift
      shift
      ;;
    --model)
      MODEL="$2"
      shift
      shift
      ;;
    --test)
      TEST="$2"
      shift
      shift
      ;;
    --wait)
      WAIT=true
      shift
      ;;
    --verbose|-v)
      VERBOSE=true
      shift
      ;;
    --help|-h)
      echo "Usage: run_tests.sh [options]"
      echo ""
      echo "Options:"
      echo "  --host HOST      Ollama server host (default: localhost or OLLAMA_HOST env var)"
      echo "  --port PORT      Ollama server port (default: 11434 or OLLAMA_PORT env var)"
      echo "  --model MODEL    Model to test (default: llama2)"
      echo "  --test TEST      Which tests to run (all, connectivity, models, generation, embeddings)"
      echo "  --wait           Wait for Ollama server to become available"
      echo "  --verbose, -v    Enable verbose output"
      echo "  --help, -h       Show this help message"
      exit 0
      ;;
    *)
      POSITIONAL+=("$1")
      shift
      ;;
  esac
done

# Build the command
CMD="python $SCRIPT_DIR/test_ollama.py"

if [ ! -z "$HOST" ]; then
  CMD="$CMD --host $HOST"
fi

if [ ! -z "$PORT" ]; then
  CMD="$CMD --port $PORT"
fi

if [ ! -z "$MODEL" ]; then
  CMD="$CMD --model $MODEL"
fi

if [ ! -z "$TEST" ]; then
  CMD="$CMD --test $TEST"
fi

if [ "$WAIT" = true ]; then
  CMD="$CMD --wait-for-server"
fi

if [ "$VERBOSE" = true ]; then
  CMD="$CMD --verbose"
fi

# Run the tests
echo "Running Ollama tests..."
echo "Command: $CMD"
echo ""

$CMD

# Get the exit code
EXIT_CODE=$?

# Exit with the same code
exit $EXIT_CODE
