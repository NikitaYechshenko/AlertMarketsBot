FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Copy requirements from app/ and project code
COPY app/requirements.txt .
# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

COPY app . .


CMD ["python", "-m", "app.bot.main"]
