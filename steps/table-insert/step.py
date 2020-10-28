#!/usr/bin/env python

import json
import sys
import googleapiclient.discovery

from google.oauth2 import service_account
from relay_sdk import Interface, Dynamic as D


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


def get_client(product, version, credentials):
    print("Initiating %s client..." % product)
    return googleapiclient.discovery.build(product, version, credentials=credentials)


def insert_table(connection, dataset_id, name, schema, description):
    credentials = get_credentials(connection)
    client = get_client('bigquery', 'v2', credentials)

    project_id = credentials.project_id
    body = {
        'tableReference': {
            'projectId': project_id,
            'datasetId': dataset_id,
            'tableId': name,
        }
    }

    if location is not None:
        body['location'] = location
    if description is not None:
        body['description'] = description

    print("Inserting table...")
    result = client.tables().insert(projectId=project_id, datasetId=dataset_id, body=body).execute()
    print("Result:")
    print(result)

    # These are the keys that we're going to cherry-pick out of the result.
    # We're explicit about the keys that we want to publish for documentation
    # purposes.
    # https://cloud.google.com/bigquery/docs/reference/rest/v2/datasets#Dataset
    table_keys = [
        "id",
        "selfLink",
        "tableReference",
        "description",
        "schema",
        #"labels", #TODO do we want this?
        "creationTime",
        "location",
    ]

    return slice(result, table_keys)


if __name__ == "__main__":
    relay = Interface()

    connection = relay.get(D.google.service_account_info)
    dataset_id = relay.get(D.dataset_id)
    name = relay.get(D.name)
    location = relay.get(D.location)
    description = relay.get(D.description)
    schema = relay.get(D.schema)

    if not dataset_id:
        print("Missing `dataset_id` parameter on step configuration.")
        sys.exit(1)
    if not name:
        print("Missing `name` parameter on step configuration.")
        sys.exit(1)

    table = insert_table(connection, dataset_id, name, location, description)
    if table is None:
        print('table failed insert!')
        sys.exit(1)

    print("Success!\n")
    print("{:<80} {:<30} {:<30}".format('ID', 'SELFLINK', 'LOCATION'))
    print("{:<80} {:<30} {:<30}".format(
        table['id'],
        table['selfLink'],
        table['location'],
    ))
    print('\nAdding table to the output `table`')
    print(table)
    relay.outputs.set("table", table)
