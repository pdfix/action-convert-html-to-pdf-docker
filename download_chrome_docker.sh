#!/bin/bash

ARCH=$1

if [[ -z "$ARCH" ]]; then
  echo "Usage: $0 <arch>"
  echo "Example: $0 amd64"
  exit 1
fi

version=122.0.6261.128

case "$ARCH" in
  amd64)
    url="https://storage.googleapis.com/chrome-for-testing-public/$version/linux64/chrome-headless-shell-linux64.zip"
    ;;
  arm64)
    url="https://storage.googleapis.com/chrome-for-testing-public/$version/mac-arm64/chrome-headless-shell-mac-arm64.zip"
    ;;
  *)
    echo "Unsupported architecture: $ARCH"
    exit 1
    ;;
esac

echo "Downloading Chrome version $version for $ARCH..."
wget -O chrome.zip "$url"

echo 'Unpacking...'
unzip chrome.zip -d chrome

echo 'Deleting temporary download file...'
rm chrome.zip
