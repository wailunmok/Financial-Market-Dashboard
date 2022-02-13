# syntax=docker/dockerfile:1
FROM python:3.9-slim-buster


# Set working directory for relative paths
RUN mkdir wd
WORKDIR wd

# Add and install requirements
COPY app/requirements.txt .
RUN pip3 install -r requirements.txt

# add remote file at root directory in container
COPY app/ ./

CMD [ "gunicorn", "--workers=5", "--threads=1", "-b 0.0.0.0:80", "index:server"]
# CMD ["python", "app.py"] To be tested
