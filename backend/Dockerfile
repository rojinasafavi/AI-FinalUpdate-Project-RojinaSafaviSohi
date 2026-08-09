# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables for better Python behavior in Docker
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory in the container
WORKDIR /app

# Install system dependencies (needed for pandas and excel processing)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container
COPY backend/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the backend code
COPY backend/ ./backend/

# Copy the services needed for analysis (since backend imports from root/services)
COPY services/ ./services/

# Expose the port the app runs on
EXPOSE 8000

# Set PYTHONPATH so that we can find the modules correctly
ENV PYTHONPATH=/app

# Command to run the application
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
