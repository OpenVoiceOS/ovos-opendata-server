# Use official Python image
FROM python:3.11

# Set the working directory
WORKDIR /app

# Copy files
COPY ./app /app

# Install dependencies
RUN pip install --no-cache-dir fastapi[all] sqlalchemy psycopg2 pydantic-settings

# Expose the FastAPI port
EXPOSE 8000

# Run the app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
