FROM python:3.11

WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Expose the port HF Spaces expects
EXPOSE 7860

# Run the app
CMD ["uvicorn", "api.index:app", "--host", "0.0.0.0", "--port", "7860"]
