# Use the specified base image
FROM ghcr.io/linuxserver/baseimage-alpine:3.20-d6fdb4e3-ls8

# Set the working directory
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install Python 3 and venv
RUN apk add --no-cache python3 py3-pip && \
    python3 -m venv /app/venv && \
    /app/venv/bin/pip install --no-cache-dir -r requirements.txt

# Ensure the virtual environment is used for all subsequent commands
ENV PATH="/app/venv/bin:$PATH"

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Run app.py when the container launches
CMD ["python", "script_name.py"]
