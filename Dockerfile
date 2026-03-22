# Use the official Python lightweight image
FROM python:3.10-slim

# Prevent python from writing pyc files to disc
ENV PYTHONDONTWRITEBYTECODE 1
# Prevent python from buffering stdout and stderr
ENV PYTHONUNBUFFERED 1
# Default port for Google Cloud Run
ENV PORT 8080

# Working directory inside the container
WORKDIR /app

# Install dependencies first for efficient caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Run the web service on container startup using gunicorn
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 app:app
