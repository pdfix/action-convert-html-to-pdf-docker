# HTML to PDF/UA conversion

HTML to PDF/UA conversion with Google Chrome Headless and PDFix SDK

## OS/ARCH

linux/amd64

## Usage
Build image
```
docker build --platform linux/amd64 --rm -t html-to-pdfua . 
```

Run image
```
docker run --rm -v $(pwd):/data -w /data -it html-to-pdf --url {url} -o index.html
```

Parameter --url can be real url address or path to a local HTML file mapped from the host.

By default the container saves the PDF in /out folder in container, which should be mapped from the host. 

