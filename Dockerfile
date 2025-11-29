FROM apache/airflow:2.7.0

USER root

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
    && apt-get autoremove -yqq --purge \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

USER airflow

# Install Python dependencies
RUN pip install --no-cache-dir \
    requests \
    pandas \
    numpy

# Set working directory
WORKDIR /opt/airflow

