FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Create non-root user for security best practices
RUN useradd -m -u 1000 user

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Set environment variables
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    # Set model cache to a writable location
    TRANSFORMERS_CACHE=/tmp/transformers_cache \
    HF_HOME=/tmp/hf_home

# Create cache directories with proper permissions
RUN mkdir -p /tmp/transformers_cache /tmp/hf_home && \
    chmod 777 /tmp/transformers_cache /tmp/hf_home

# Copy application code
COPY --chown=user:user . /app/

# Create static directory with proper permissions
RUN mkdir -p /app/static && chown -R user:user /app/static

# Switch to non-root user
USER user

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]