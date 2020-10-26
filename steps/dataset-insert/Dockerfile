FROM python:3-alpine
RUN apk --no-cache add bash ca-certificates curl git jq openssh && update-ca-certificates
RUN pip --no-cache-dir install "https://packages.nebula.puppet.net/sdk/support/python/v1/nebula_sdk-1-py3-none-any.whl"
RUN pip --no-cache-dir install google-api-python-client
COPY "./step.py" "/nebula/gcp-bigquery-step-dataset-insert.py"
ENTRYPOINT []
CMD ["python3", "/nebula/gcp-bigquery-step-dataset-insert.py"]

LABEL "org.opencontainers.image.title"="Insert GCP BiqQuery datasets"
LABEL "org.opencontainers.image.description"="This task inserts new datasets in GCP BigQuery"
LABEL "com.puppet.nebula.sdk.version"="v1"

