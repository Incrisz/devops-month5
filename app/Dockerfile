FROM python:3.12-alpine
WORKDIR /app
COPY server.py .
USER 10001
EXPOSE 8080
CMD ["python", "-u", "server.py"]
