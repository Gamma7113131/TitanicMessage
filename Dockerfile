# Use the official Python 3.12 slim image as the base image
FROM python:3.12-slim

# Set the working directory
WORKDIR /usr/src/app

# Copy the requirements file into the container
COPY requirements.txt ./

# Install any necessary dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container at /usr/src/app
COPY . .

# Expose port 80
EXPOSE 80

# Run the application
CMD ["python", "app.py"]
