# Easier to start with Node and add python than to start with Python and
# add node
FROM python:2.7

ENV PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=UTF-8 \
    LC_ALL=C.UTF-8 \
    LANG=C.UTF-8

WORKDIR /app
# launch gunicorn
# Do this as threads rather than processes because we need to share state
# between requests (i.e. for dynamically registered event listeners).
CMD gunicorn \
        -w 1 --threads 4 \
        -b 0.0.0.0:80 \
        server:app

# Install Python and Gulp into the container
#
# Install Python deps that require compilation from the system to save on
# dev packages.
RUN echo "Installing required packages" && \
    pip install -U pip pyinotify && \
    echo "Cleaning up" && \
    rm -rf ~/.cache/pip && \
    true

# Install Python
#
COPY requirements.txt /app/
RUN pip install -r requirements.txt && \
    rm -rf ~/.cache/pip && \
    true

# Install and build the app
ADD . /app
RUN python -m compileall \
        server \
    && \
    true
