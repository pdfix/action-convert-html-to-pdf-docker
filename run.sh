#!/bin/bash

# init
pushd "$(dirname $0)" > /dev/null

IMAGE_NAME="html-to-pdf"
IMAGE_TAG="latest"
IMAGE="$IMAGE_NAME:$IMAGE_TAG"

# Initialize variables for arguments
FORCE_REBUILD=false
URL=""
INPUT_PDF=""
OUTPUT_PDF=""

# Function to print help message
print_help() {
    echo "Usage: $0 [OPTIONS]"
    echo
    echo "Options:"
    echo "  --input <input.html>     Path to the input HTML file"
    echo "  --output <output.pdf>    Path the output PDF file"
    echo "  --url <url>              URL adress"
    echo "  --build                  Force rebuild of the Docker image"
    echo "  --help                   Display this help message"
}

# Parse script arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --build) FORCE_REBUILD=true ;;
        --url) URL="$2"; shift ;;
        --input) INPUT_PDF="$2"; shift ;;
        --output) OUTPUT_PDF="$2"; shift ;;
        --help) print_help; exit 0 ;;
        *) echo "Unknown parameter passed: $1"; print_help; exit 1 ;;
    esac
    shift
done

# Check required arguments
if [ -z "$INPUT_PDF" ] || [ -z "$URL" ] && [ -z "$OUTPUT_PDF" ]; then
    echo "Error: --input or url and --output arguments are required."
    print_help
    exit 1
fi

# Extract directory paths and file names
INPUT_DIR=$(dirname "$INPUT_PDF")
INPUT_FILE=$(basename "$INPUT_PDF")
OUTPUT_DIR=$(dirname "$OUTPUT_PDF")
OUTPUT_FILE=$(basename "$OUTPUT_PDF")

# Check if Docker is installed
if ! command -v docker &> /dev/null
then
    echo "Error: Docker is not installed on this system."
    exit 1
else
    echo "Docker is installed."
fi

# Function to build Dockerfile
build_dockerfile() {
    echo "Building Dockerfile..."
    if docker build -t $IMAGE .
    then
        echo "Dockerfile built successfully and image $IMAGE created."
    else
        echo "Error: Failed to build Dockerfile."
        exit 1
    fi
}

# Check if the Docker image is already present
if docker image inspect $IMAGE > /dev/null 2>&1
then
    if [ "$FORCE_REBUILD" = true ]; then
        echo "Force rebuild flag is set. Rebuilding Docker image $IMAGE..."
        build_dockerfile
    else
        echo "Docker image $IMAGE already exists."
    fi
else
    echo "Docker image $IMAGE does not exist. Building Dockerfile..."
    build_dockerfile
fi

DATA_IN="/data_in"
DATA_OUT="/data_out"

# Run the Docker container with the specified arguments
docker_cmd="docker run --rm -v \"$INPUT_DIR\":\"$DATA_IN\" -v \"$OUTPUT_DIR\":\"$DATA_OUT\""

docker_cmd+=" -it $IMAGE"

if [ -n "$URL" ]; then
    docker_cmd+=" --url \"$URL\""
fi
if [ -n "$INPUT_FILE" ]; then
    docker_cmd+=" --input \"$INPUT_FILE\""
fi

docker_cmd+=" -o \"$DATA_OUT/$OUTPUT_FILE\""

eval $docker_cmd

popd > /dev/null
