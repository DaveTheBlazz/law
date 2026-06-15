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
COPY app.py config.py database.py run.py ./
COPY templates/ templates/
COPY static/ static/
COPY opinions.csv ./

# Expose port
EXPOSE 8080

CMD ["python", "run.py"]
