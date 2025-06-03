# Use the official Debian slim image as a base
FROM debian:stable-slim

# Update system and Install python3 and necessary dependencies
RUN apt-get update && \
    apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    wget \
    unzip \
    libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 libgbm1 libasound2 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /usr/html-to-pdf/


# Create a virtual environment and install dependencies
ENV VIRTUAL_ENV=venv
RUN python3 -m venv venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
COPY requirements.txt /usr/html-to-pdf/
RUN pip install --no-cache-dir -r requirements.txt


# Download chrome
COPY download_chrome.sh /usr/html-to-pdf/
RUN chmod +x download_chrome.sh
RUN /usr/html-to-pdf/download_chrome.sh


# Copy the source code
COPY config.json /usr/html-to-pdf/
COPY src/ /usr/html-to-pdf/src/


ENTRYPOINT ["/usr/html-to-pdf/venv/bin/python3", "/usr/html-to-pdf/src/main.py"]
