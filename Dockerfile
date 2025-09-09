FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y build-essential

# Install Poetry
RUN pip install --no-cache-dir poetry

# Set work directory
WORKDIR /app

# Copy only poetry files first for better caching
COPY pyproject.toml poetry.lock* /app/

# Install dependencies
RUN poetry config virtualenvs.create false \
  && poetry install --no-interaction --no-ansi --only main

# Copy the rest of the application code
COPY . /app

# Expose the port your app runs on
EXPOSE 8000

# Run the app with Uvicorn
CMD ["uvicorn", "src.test_backend.api:app", "--host", "0.0.0.0", "--port", "8000"]
