FROM ghcr.io/odense-rpa/ats-worker:v0.3.0

WORKDIR /app

COPY . .

RUN pip install flask requests

CMD ["python", "q_datafordeleren_api/docker_service_api/internal_api.py"]