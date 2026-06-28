FROM python:3.12-slim

WORKDIR /app

# Copy the whole repository
COPY . .

# Install backend dependencies
RUN pip install --no-cache-dir -r backend/requirements.txt

# Make website-generator importable
ENV PYTHONPATH="/app/backend:/app/website-generator"

WORKDIR /app/backend

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]