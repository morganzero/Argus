# Use the specified base image
FROM ghcr.io/linuxserver/baseimage-alpine:3.20-d6fdb4e3-ls8

# Set the working directory
WORKDIR /config

# Copy the current directory contents into the container at /config
COPY . /config

# Install Python 3, venv, and OpenSSH client
RUN apk add --no-cache python3 py3-pip openssh && \
    python3 -m venv /config/venv && \
    /config/venv/bin/pip install --no-cache-dir -r /config/requirements.txt

# Ensure the virtual environment is used for all subsequent commands
ENV PATH="/config/venv/bin:$PATH"

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Run Argus.py when the container launches
CMD ["python", "/config/Argus.py"]
