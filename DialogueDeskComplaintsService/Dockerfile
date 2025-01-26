# Use an official Python runtime as a base image
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Copy requirements file and the app itself into the container
COPY requirements.txt requirements.txt
COPY . .

# Install dependencies
RUN pip install -r requirements.txt

# Expose the default port (8000)
EXPOSE 8000

# Run the bot
CMD ["python", "app.py"]
