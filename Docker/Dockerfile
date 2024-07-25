# Docker/platform/Dockerfile
FROM python:3.10-slim

WORKDIR /app

# Copy application files
COPY ad_miner /app/ad_miner
COPY requirements.txt /app/requirements.txt
COPY Docker/ad_miner.sh /usr/local/bin/ad_miner.sh

# Install dependencies
RUN chmod +x /usr/local/bin/ad_miner.sh
RUN pip install --no-cache-dir -r /app/requirements.txt

# Keep the container running in an idle state
CMD ["tail", "-f", "/dev/null"]
