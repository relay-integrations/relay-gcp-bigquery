FROM relaysh/core:latest-python
RUN pip install google-api-python-client oauth2client
COPY "./step.py" "/entrypoint.py"
ENTRYPOINT []
CMD ["python3", "/entrypoint.py"]

LABEL "org.opencontainers.image.title"="Insert GCP BiqQuery tables"
LABEL "org.opencontainers.image.description"="This step inserts new tables in GCP BigQuery"
LABEL "com.puppet.nebula.sdk.version"="v1"
