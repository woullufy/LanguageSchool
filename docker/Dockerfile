FROM python:3.11-slim

WORKDIR /app

COPY docker/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . . 

# Expose Flask default port
# EXPOSE 5050

# Run the Flask app
CMD ["python", "app.py"]