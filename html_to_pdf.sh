#!/bin/bash

activate_venv_unix() {
    if [ -d "venv" ]; then
        source venv/bin/activate
    elif [ -d "env" ]; then
        source env/bin/activate
    else
        read -p "Python virtual environment 'venv' or 'env' not found. Do you want to create it automatically? (y/n): " create_venv
        if [ "$create_venv" == "y" ] || [ "$create_venv" == "Y" ]; then
            echo "Creating Python virtual environment..."
            python3 -m venv venv
            source venv/bin/activate
        else
            echo "Exiting program. Please create the virtual environment 'venv' manually."
            exit 1
        fi
    fi
}

activate_venv_win() {
    if [ -d "venv" ]; then
        source venv/Scripts/activate
    elif [ -d "env" ]; then
        source env/Scrits/activate
    else
        read -p "Python virtual environment 'venv' or 'env' not found. Do you want to create it automatically? (y/n): " create_venv
        if [ "$create_venv" == "y" ] || [ "$create_venv" == "Y" ]; then
            echo "Creating Python virtual environment..."
            python -m venv venv
            source venv/Scripts/activate
        else
            echo "Exiting program. Please create the virtual environment 'venv' manually."
            exit 1
        fi
    fi
}

cd "$(dirname "$0")"
if [ "$(uname -s)" = "Linux" ] || [ "$(uname -s)" = "Darwin" ]; then
    activate_venv_unix
elif [ "$(uname -o)" = "Msys" ]; then
    activate_venv_win
else
    echo "Unsupported OS type: $(uname -s)"
    exit 1
fi

usage() {
    echo "Usage: $0 --url <URL> --output <output_file.pdf>"
    echo "Usage: $0 --input <index.html> --output <output_file.pdf>"
    exit 1
}


URL=""
OUTPUT=""

while [ "$1" != "" ]; do
    case $1 in
        --url )           shift
                          URL=$1
                          ;;
        --input )         shift
                          URL=$1
                          ;;
        --output )        shift
                          OUTPUT=$1
                          ;;
        * )               usage
    esac
    shift
done

if [ -z "$URL" ] || [ -z "$OUTPUT" ]; then
    usage
fi

# Get the full path of this script
SCRIPT_PATH=$(realpath "$0")

# Get the directory where this script is located
SCRIPT_DIR=$(dirname "$SCRIPT_PATH")

${SCRIPT_DIR}/dist/html_to_pdf/html_to_pdf --url "$URL" --output "$OUTPUT"
#python3 ${SCRIPT_DIR}/src/html_to_pdf.py --url "$URL" --output "$OUTPUT"

# Check if the command was successful
if [ $? -eq 0 ]; then
    echo "PDF has been saved to $OUTPUT"
else
    echo "Failed to create PDF"
    exit 1
fi
