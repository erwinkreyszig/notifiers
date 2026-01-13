# stage 1: base build stage
FROM python:3.14-slim AS builder

# create app directory
RUN mkdir /app

# set working directory inside container
WORKDIR /app

# set environment variables
# prevents python from writing pyc files to disk
ENV PYTHONDONTWRITEBYTECODE=1
# prevents python from buffering stdout and stder
ENV PYTHONUNBUFFERED=1

# upgrade pip
RUN pip install --upgrade pip

# copy django project and install dependencies
COPY requirements.txt /app/

# run to install all dependencies
RUN pip install --no-cache-dir -r requirements.txt

# stage 2: production stage
FROM python:3.14-slim

# TODO: will deal with this later
# RUN useradd -m -r appuser && mkdir /app && chown -R appuser /app
RUN mkdir /app

# copy python dependencies from builder stage
COPY --from=builder /usr/local/lib/python3.14/site-packages/ /usr/local/lib/python3.14/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/

# set working directory
WORKDIR /app

# copy application code
# will deal with this later
# COPY --chown=appuser:appuser . .
COPY . .

# set environment variables to optimize python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# switch to non-root user
# will deal with this later
# USER appuser

# expose application port
EXPOSE 8100

# start application using gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8100", "--workers", "1", "app.wsgi:application"]