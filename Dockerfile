FROM python:3.11-slim

# Set UTF-8 locale for Persian text support
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8
ENV PYTHONUTF8=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py config.py database.py main.py ./
COPY templates/ templates/

# Create data directory for law.db (mounted from host /data/law/)
RUN mkdir -p /data/law
VOLUME ["/data/law"]

# Expose port
EXPOSE 8080

# Default DB path can be overridden via docker-compose env
ENV DB_PATH=/data/law/law.db

CMD ["python", "main.py"]
