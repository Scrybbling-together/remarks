#!/bin/bash

# ReMarkable to Markdown Converter - Docker Runner
# Convenient wrapper script for running remarks in Docker

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
IMAGE_NAME="remarks:latest"
LOG_LEVEL="INFO"

# Print usage
usage() {
    echo "Usage: $0 INPUT_DIR OUTPUT_DIR [OPTIONS]"
    echo ""
    echo "Convert ReMarkable files to Markdown and PDF"
    echo ""
    echo "Arguments:"
    echo "  INPUT_DIR     Path to xochitl directory or .rmn/.rmdoc file"
    echo "  OUTPUT_DIR    Path where output files will be saved"
    echo ""
    echo "Options:"
    echo "  -l, --log-level LEVEL    Set log level (DEBUG, INFO, WARNING, ERROR)"
    echo "  -b, --build              Build Docker image before running"
    echo "  -h, --help               Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 ~/remarkable-backup/xochitl ~/output"
    echo "  $0 ~/remarkable-backup/xochitl ~/output --log-level DEBUG"
    echo "  $0 ~/notebook.rmn ~/output --build"
    exit 1
}

# Parse arguments
BUILD_IMAGE=false

if [ $# -lt 2 ]; then
    usage
fi

INPUT_DIR="$1"
OUTPUT_DIR="$2"
shift 2

# Parse optional arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -l|--log-level)
            LOG_LEVEL="$2"
            shift 2
            ;;
        -b|--build)
            BUILD_IMAGE=true
            shift
            ;;
        -h|--help)
            usage
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            usage
            ;;
    esac
done

# Validate input directory
if [ ! -e "$INPUT_DIR" ]; then
    echo -e "${RED}Error: Input directory/file does not exist: $INPUT_DIR${NC}"
    exit 1
fi

# Convert to absolute paths
INPUT_DIR=$(cd "$(dirname "$INPUT_DIR")" && pwd)/$(basename "$INPUT_DIR")
OUTPUT_DIR=$(mkdir -p "$OUTPUT_DIR" && cd "$OUTPUT_DIR" && pwd)

echo -e "${BLUE}===================="
echo "Remarks Docker Runner"
echo "====================${NC}"
echo ""
echo "Input:  $INPUT_DIR"
echo "Output: $OUTPUT_DIR"
echo "Log level: $LOG_LEVEL"
echo ""

# Build image if requested
if [ "$BUILD_IMAGE" = true ]; then
    echo -e "${YELLOW}Building Docker image...${NC}"
    docker build -t "$IMAGE_NAME" .
    echo -e "${GREEN}Image built successfully${NC}"
    echo ""
fi

# Check if image exists
if ! docker image inspect "$IMAGE_NAME" &> /dev/null; then
    echo -e "${YELLOW}Image '$IMAGE_NAME' not found. Building...${NC}"
    docker build -t "$IMAGE_NAME" .
    echo ""
fi

# Run the converter
echo -e "${YELLOW}Starting conversion...${NC}"
echo ""

docker run --rm \
    -v "$INPUT_DIR:/input:ro" \
    -v "$OUTPUT_DIR:/output" \
    "$IMAGE_NAME" \
    /input /output --log_level "$LOG_LEVEL"

echo ""
echo -e "${GREEN}===================="
echo "Conversion Complete!"
echo "====================${NC}"
echo ""
echo "Output files saved to: $OUTPUT_DIR"
echo ""
