FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Make sure entrypoint.sh is executable
RUN chmod +x /app/entrypoint.sh

EXPOSE 5001

# Use the custom entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]


