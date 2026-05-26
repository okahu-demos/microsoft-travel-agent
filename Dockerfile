FROM python:3.12-slim

WORKDIR /app

# Install dependencies first
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


COPY ms_travel_agent.py .
COPY travel_agent/ travel_agent/

EXPOSE 8088

CMD ["python", "ms_travel_agent.py"]