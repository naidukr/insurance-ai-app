# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose ports for FastAPI and Streamlit
EXPOSE 8000 8501

# Create start script
RUN echo '#!/bin/bash\n\
echo "Starting Insurance AI Application..."\n\
echo "Backend API: http://localhost:8000"\n\
echo "Frontend Dashboard: http://localhost:8501"\n\
echo ""\n\
echo "Starting FastAPI backend..."\n\
python main.py &\n\
sleep 3\n\
echo ""\n\
echo "Starting Streamlit frontend..."\n\
streamlit run app.py --server.port=8501 --server.address=0.0.0.0' > /app/start.sh && chmod +x /app/start.sh

# Default command
CMD ["/app/start.sh"]
