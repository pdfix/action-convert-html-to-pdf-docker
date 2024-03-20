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

unzip_file() {
    local folder_name="$1"
    unzip chrome.zip -d "$folder_name"
}

run_pyinstaller() {
    local spec_file="$1"
    pyinstaller "$spec_file"
}

check_directory_exists() {
    local directory="$1"
    if [ -d "$directory" ]; then
        echo "Directory '$directory' already exists. Skipping download."
        return 1
    else
        return 0
    fi
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

version=122.0.6261.111

if check_directory_exists "chrome_v${version}";then

	linux_url="https://storage.googleapis.com/chrome-for-testing-public/122.0.6261.128/linux64/chrome-headless-shell-linux64.zip"
	mac_url="https://storage.googleapis.com/chrome-for-testing-public/122.0.6261.128/mac-arm64/chrome-headless-shell-mac-arm64.zip"
	windows_url="https://storage.googleapis.com/chrome-for-testing-public/122.0.6261.128/win64/chrome-headless-shell-win64.zip"

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
	folder_name="chrome_v${version}"
	unzip_file "$folder_name"

	echo 'Deleting temporary download file...'
	rm chrome.zip
fi

echo 'Building executable...'
run_pyinstaller "html_to_pdf.spec"
