#!/usr/bin/env python

import json, sys, requests
import googleapiclient.discovery

from google.oauth2 import service_account
from relay_sdk import Interface, Dynamic as D


def get_or_default(path, default=None):
    try:
        return relay.get(path)
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 422:
            return default
        raise


def slice(orig, keys):
    return {key: orig[key] for key in keys if key in orig}


def get_credentials(connection):
    # For security purposes we whitelist the keys that can be fed in to the
    # google oauth library. This prevents workflow users from feeding arbitrary
    # data in to that library.
    service_account_info_keys = [
        "type",
        "project_id",
        "private_key_id",
        "private_key",
        "client_email",
        "client_id",
        "auth_uri",
        "token_uri",
        "auth_provider_x509_cert_url",
        "client_x509_cert_url",
    ]

    print("Getting service account info...")
    service_account_info = slice(json.loads(
        connection['serviceAccountKey']
    ), service_account_info_keys)

    return service_account.Credentials.from_service_account_info(service_account_info)


def do_insert_dataset(bigquery, project_id, body):
    print("Inserting dataset...")
    result = bigquery.datasets().insert(projectId=project_id, body=body).execute()
    print("Result:")
    print(result)
    return result


def insert_dataset():

    credentials = get_credentials(relay.get(D.google.connection))
    project = get_or_default(D.google.project, credentials.project_id)
    name = relay.get(D.name)
    location = get_or_default(D.location, None)
    description = get_or_default(D.description, None)

    if not project:
        print("Missing `google.project` parameter on step configuration and no project was found in the connection.")
        sys.exit(1)
    if not name:
        print("Missing `name` parameter on step configuration.")
        sys.exit(1)

    print("Initiating bigquery client...")
    bigquery = googleapiclient.discovery.build('bigquery', 'v2', credentials=credentials)

    body = {
        'datasetReference': {
            'projectId': project,
            'datasetId': name,
        }
    }

    if location is not None:
        body['location'] = location
    if description is not None:
        body['description'] = description

    dataset = do_insert_dataset(bigquery, project, body)

    # These are the keys that we're going to cherry-pick out of the result.
    # We're explicit about the keys that we want to publish for documentation
    # purposes.
    # https://cloud.google.com/bigquery/docs/reference/rest/v2/datasets#Dataset
    dataset_keys = [
        "id",
        "selfLink",
        "datasetReference",
        "description",
        "defaultTableExpirationMs",
        "defaultPartitionExpirationMs",
        #"labels", #TODO do we want this?
        #"access", #TODO Do we want this?
        # Response looks like:
        # access:
        # - role: WRITER
        #   specialGroup: projectWriters
        # - role: OWNER
        #   specialGroup: projectOwners
        # - role: OWNER
        #   userByEmail: workflow@hunner-293423.iam.gserviceaccount.com
        # - role: READER
        #   specialGroup: projectReaders
        "creationTime",
        "location",
    ]

    return slice(dataset, dataset_keys)


if __name__ == "__main__":
    relay = Interface()
    dataset = insert_dataset()
    if dataset is None:
        print('Dataset failed insert!')
        sys.exit(1)

    print("Success!\n")
    print('\nAdding dataset to the output `dataset`')
    print(dataset)
    relay.outputs.set("dataset", dataset)
