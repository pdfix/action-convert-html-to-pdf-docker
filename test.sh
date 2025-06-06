#!/bin/bash

# local docker test 
info() { echo -e "\033[1;35m$1\033[0m"; }

# init
pushd "$(dirname $0)" > /dev/null

img="html-to-pdf:test"
pltfm="--platform linux/amd64"
tmp_dir=".test"

docker build $pltfm --rm -t $img .

if [ -d "$(pwd)/$tmp_dir" ]; then
    rm -rf $(pwd)/$tmp_dir
fi
mkdir -p $(pwd)/$tmp_dir

info "List files in cwd"
docker run --rm $pltfm -v $(pwd):/data -w /data --entrypoint ls $img

info "Test #01: Show help"
docker run --rm $pltfm -v $(pwd):/data -w /data $img --help

info "Test #02: Extract config"
docker run --rm $pltfm -v $(pwd):/data -w /data $img config -o $tmp_dir/config.json
if [ ! -f "$(pwd)/$tmp_dir/config.json" ]; then
    echo "config.json not saved"
    exit 1
fi

info "Test #03: Run html-to-pdf"
docker run --rm $pltfm -v $(pwd):/data -w /data $img html-to-pdf --url https://pdfix.net -o $tmp_dir/pdfix.net.pdf --verbose
if [ ! -f "$(pwd)/$tmp_dir/pdfix.net.pdf" ]; then
    echo "html-to-pdf to pdf failed on https://pdfix.net"
    exit 1
fi

info "Removing testing docker image"
docker rmi $img

popd

echo "SUCCESS"
