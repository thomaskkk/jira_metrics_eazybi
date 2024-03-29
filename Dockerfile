
# Use the official lightweight Python image.
# https://hub.docker.com/_/python
FROM python:3.11-slim

# Allow statements and log messages to immediately appear in the Knative logs
ENV PYTHONUNBUFFERED True

ENV APP_HOME /app
WORKDIR $APP_HOME

# Copy the rest of the working directory contents into the container at /app
COPY src/ ./

# copy the requirements file used for dependencies
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --trusted-host pypi.python.org -r requirements.txt

# Install google cloud sdk (Debugging)
RUN apt-get -y update; apt-get -y install curl
RUN curl -sSL https://sdk.cloud.google.com | bash
ENV PATH $PATH:/usr/local/gcloud/google-cloud-sdk/bin

# Run the web service on container startup. Here we use the gunicorn
# webserver, with one worker process and 8 threads.
# For environments with multiple CPU cores, increase the number of workers
# to be equal to the cores available.
# Timeout is set to 0 to disable the timeouts of the workers to allow Cloud Run to handle instance scaling.

# Enable this for cloud run production - PROD ENVIROMENT
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 'main:create_app()'

# OR Enable this for cloud run debbuging on vscode - DEV ENVIROMENT
# ENTRYPOINT ["python", "main.py"]
