# Use an official Python runtime as a parent image
FROM ghcr.io/linuxserver/baseimage-alpine:3.20-d6fdb4e3-ls8

# Set the working directory
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN apk add --no-cache \
    python3 \
    py3-pip \
    && pip3 install --no-cache-dir -r requirements.txt

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Run app.py when the container launches
CMD ["python", "Argus.py"]
