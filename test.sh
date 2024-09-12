#!/bin/bash

# local docker test 
info() { echo -e "\033[1;35m$1\033[0m"; }

# init
pushd "$(dirname $0)" > /dev/null

img="html-to-pdf"
pltfm="--platform linux/amd64"

docker build $pltfm --rm -t $img .

tmp_dir=".test"
if [ -d "$(pwd)/$tmp_dir" ]; then
  rm -rf $(pwd)/$tmp_dir
fi
mkdir -p $(pwd)/$tmp_dir

info "list files in cwd"
docker run $pltfm -it -v $(pwd):/data -w /data --entrypoint ls $img

info "show help"
docker run $pltfm -it -v $(pwd):/data -w /data $img --help

info "extract config"
docker run $pltfm -it -v $(pwd):/data -w /data $img config -o $tmp_dir/config.json
if [ ! -f "$(pwd)/$tmp_dir/config.json" ]; then
  echo "config.json not saved"
  exit 1
fi

info "run html-to-pdf"
docker run $pltfm -it -v $(pwd):/data -w /data $img html-to-pdf --url https://pdfix.net -o $tmp_dir/pdfix.net.pdf --verbose
if [ ! -f "$(pwd)/$tmp_dir/pdfix.net.pdf" ]; then
  echo "html-to-pdf to pdf failed on https://pdfix.net"
  exit 1
fi


popd

echo "SUCCESS"
