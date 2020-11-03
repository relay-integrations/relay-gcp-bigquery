#!/usr/bin/env python

import json
import sys
import requests
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


def get_client(product, version, credentials):
    print("Initiating %s client..." % product)
    return googleapiclient.discovery.build(product, version, credentials=credentials)


def create_transfer_config(connection, dataset_id, destination_table, display_name, schedule, replace, query):
    credentials = get_credentials(connection)
    client = get_client('bigquerydatatransfer', 'v1', credentials).projects().transferConfigs()

    if replace is True:
        write_disposition = 'WRITE_TRUNCATE'
    else:
        write_disposition = 'WRITE_APPEND'

    project_id = credentials.project_id
    body = {
        'destinationDatasetId': dataset_id,
        'displayName': display_name,
        'dataSourceId': 'scheduled_query',
        'params': {
            'query': query,
            'destination_table_name_template': destination_table,
            'write_disposition': write_disposition,
            'partitioning_field': '',
        },
        'schedule': schedule,
    }

    print("Creating transferConfig with %s..." % body)
    result = client.create(parent='projects/%s' % project_id, body=body).execute()
    print("Result:")
    print(result)

    # These are the keys that we're going to cherry-pick out of the result.
    # We're explicit about the keys that we want to publish for documentation
    # purposes.
    # https://cloud.google.com/bigquery/docs/reference/rest/v2/datasets#Dataset
    transfer_config_keys = [
        "name",
        "destinationDatasetId",
        "displayName",
        "schedule",
        "nextRunTime",
        "params",
        "datasetRegion",
    ]

    return slice(result, transfer_config_keys)


if __name__ == "__main__":
    relay = Interface()

    connection = relay.get(D.google.service_account_info)
    dataset_id = relay.get(D.dataset_id)
    destination_table = relay.get(D.destination_table)
    display_name = get_or_default(D.display_name, None)
    schedule = relay.get(D.schedule)
    replace = get_or_default(D.replace, False)
    query = relay.get(D.query)

    if not dataset_id:
        print("Missing `dataset_id` parameter on step configuration.")
        sys.exit(1)
    if not destination_table:
        print("Missing `destination_table` parameter on step configuration.")
        sys.exit(1)
    if not display_name:
        print("Missing `display_name` parameter on step configuration.")
        sys.exit(1)
    if not schedule:
        print("Missing `schedule` parameter on step configuration.")
        sys.exit(1)
    if not query:
        print("Missing `query` parameter on step configuration.")
        sys.exit(1)
    if not replace:
        replace = False

    transfer_config = create_transfer_config(connection, dataset_id, destination_table, display_name, schedule, replace, query)
    if transfer_config is None:
        print('transferConfig failed insert!')
        sys.exit(1)

    print("Success!\n")
    print('\nAdding transferConfig to the output `transferConfig`')
    print(transfer_config)
    relay.outputs.set("transferConfig", transfer_config)

