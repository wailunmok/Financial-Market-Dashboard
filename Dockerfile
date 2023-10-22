# syntax=docker/dockerfile:1
FROM python:3.7


# Set working directory for relative paths
RUN mkdir wd
WORKDIR wd

# Add and install requirements
COPY app/requirements.txt .
RUN pip3 install --upgrade pip setuptools wheel
RUN pip3 install -r requirements.txt
RUN pip3 install prophet==1.1.4


# add remote file at root directory in container
COPY app/ ./

CMD [ "gunicorn", "--workers=5", "--threads=1", "--timeout=600", "-b 0.0.0.0:80", "index:server"]
# CMD ["python", "app.py"] To be tested
