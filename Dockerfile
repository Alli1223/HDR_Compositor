# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /usr/src/app

# Install exiftool and any other dependencies
RUN apt-get update && \
    apt-get install -y exiftool && \
    rm -rf /var/lib/apt/lists/*

# Copy the Python scripts into the container
COPY ./find_and_merge_aeb.py ./find_and_merge_aeb.py
COPY ./hdr_utils.py ./hdr_utils.py

# Install Python dependencies
RUN pip install --no-cache-dir opencv-python-headless numpy

# Define environment variables for input and output directories
ENV INPUT_DIR=/usr/src/app/images
ENV OUTPUT_DIR=/usr/src/app/output

# Make directory for output to ensure it exists
RUN mkdir -p ${OUTPUT_DIR}

# Command to run the script, using environment variables
CMD python ./find_and_merge_aeb.py $INPUT_DIR $OUTPUT_DIR
