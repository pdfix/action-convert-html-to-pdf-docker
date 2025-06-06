#!/bin/bash
download_file() {
    local os_type=$(uname -s)

    case "$os_type" in
        Linux*)     wget -O chrome.zip "$1" ;;
        Darwin*)    curl -o chrome.zip "$1" ;;
        MINGW*)     powershell -command "(New-Object Net.WebClient).DownloadFile('$1', 'chrome.zip')" ;;
        *)          echo "Unsupported OS type: $os_type" ;;
    esac
}

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
