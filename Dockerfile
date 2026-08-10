# Use the official Debian slim image as a base
FROM debian:stable-slim

# Update system and install Python, Chromium, and fonts
RUN apt-get update && \
    apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    chromium \
    fontconfig \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /usr/html-to-pdf/

# Create a virtual environment and install dependencies
ENV VIRTUAL_ENV=venv
RUN python3 -m venv venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
COPY requirements.txt /usr/html-to-pdf/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the source code
COPY config.json /usr/html-to-pdf/
COPY src/ /usr/html-to-pdf/src/

# License
LABEL license="Chromium (BSD-style license)"

ENTRYPOINT ["/usr/html-to-pdf/venv/bin/python3", "/usr/html-to-pdf/src/main.py"]
