# TokenTon26 AI Wallet - Docker Configuration
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY . .

# Expose Gradio port
EXPOSE 7860

# Run the app
CMD ["python", "-m", "app"]
