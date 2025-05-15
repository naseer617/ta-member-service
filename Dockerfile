FROM python:3.11-slim

WORKDIR /app

# Copy service-specific code
COPY ./app ./app

#Copy the shared directory
COPY ../shared ./shared

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

#Set Python path to include both app/ and shared/
ENV PYTHONPATH="/app:/app/shared:$PYTHONPATH"

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]