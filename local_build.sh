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

install_dependencies() {
    if [ -f "requirements.txt" ]; then
        echo "Installing dependencies from requirements.txt..."
        pip install -r requirements.txt
    else
        echo "requirements.txt not found. No dependencies installed."
    fi
}

download_file() {
    local os_type=$(uname -s)

    case "$os_type" in
        Linux*)     wget -O chrome.zip "$1" ;;
        Darwin*)    curl -o chrome.zip "$1" ;;
        MINGW*)     powershell -command "(New-Object Net.WebClient).DownloadFile('$1', 'chrome.zip')" ;;
        *)          echo "Unsupported OS type: $os_type" ;;
    esac
}


if [[ "$(uname -s)" = "Linux" ]] || [[ "$(uname -s)" = "Darwin" ]]; then
    activate_venv_unix
elif [[ "$(uname -o)" = "Msys" ]]; then
    activate_venv_win
else
    echo "Unsupported OS type: $(uname -s)"
    exit 1
fi

install_dependencies

version=122.0.6261.128

linux_url="https://storage.googleapis.com/chrome-for-testing-public/$version/linux64/chrome-headless-shell-linux64.zip"
mac_url="https://storage.googleapis.com/chrome-for-testing-public/$version/mac-arm64/chrome-headless-shell-mac-arm64.zip"
windows_url="https://storage.googleapis.com/chrome-for-testing-public/$version/win64/chrome-headless-shell-win64.zip"

echo 'Downloading chrome version '${version}'...'
if [[ $(uname -s) == "Linux" ]]; then
 	  download_file "$linux_url"
		pltfm=linux64
elif [[ $(uname -s) == "Darwin" ]]; then
 	  download_file "$mac_url"
		pltfm=mac-arm64
elif [[ $(uname -o) == "Msys" ]]; then
 	  download_file "$windows_url"
		pltfm=win64
else
 	  echo "Unsupported OS type: $(uname -s)"
   	exit 1
fi

echo 'Unpacking...'
unzip chrome.zip -d chrome

echo 'Deleting temporary download file...'
rm chrome.zip

echo 'Building executable...'
pyinstaller "html_to_pdf.spec"

cp config.json dist/html_to_pdf/