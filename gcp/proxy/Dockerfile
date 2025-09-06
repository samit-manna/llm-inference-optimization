FROM python:3.11-slim
RUN pip install fastapi uvicorn httpx prometheus-client pydantic
WORKDIR /app
COPY app.py /app/
ENV TARGET_URL=http://localhost:8000/v1/chat/completions \
    INSTANCE_HOURLY_USD=0.0
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "9000"]
