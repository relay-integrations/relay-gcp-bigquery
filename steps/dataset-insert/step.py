import json, sys
import googleapiclient.discovery

from google.oauth2 import service_account
from relay_sdk import Interface, Dynamic as D


def slice(orig, keys):
    return {key: orig[key] for key in keys if key in orig}


def slice_arr(orig, keys):
    return [slice(obj, keys) for obj in orig]


def do_insert_dataset(bigquery, project_id, body):
    print("Inserting dataset...")
    result = bigquery.datasets().insert(projectId=project_id, body=body).execute()
    print("Result:")
    print(result)
    return result


def insert_dataset():
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

    name = relay.get(D.name)
    location = relay.get(D.location)

    if not id:
        print("Missing `id` parameter on step configuration.")
        sys.exit(1)

    print("Getting service account info...")
    service_account_info = slice(json.loads(
        relay.get(D.google.service_account_info)['serviceAccountKey']
        ), service_account_info_keys)

    credentials = service_account.Credentials.from_service_account_info(service_account_info)
    print("Initiating bigquery client...")
    bigquery = googleapiclient.discovery.build('bigquery', 'v2', credentials=credentials)

    project_id = credentials.project_id
    body = {
        'datasetReference': {
            'projectId': project_id,
            'datasetId': name,
        }
    }
    if location is not None:
        body['location'] = location

    dataset = do_insert_dataset(bigquery, project_id, body)

    # These are the keys that we're going to cherry-pick out of the result.
    # We're explicit about the keys that we want to publish for documentation
    # purposes.
    # https://cloud.google.com/bigquery/docs/reference/rest/v2/datasets#Dataset
    dataset_keys = [
        "id",
        "selfLink",
        "datasetReference",
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

    return slice_arr(dataset, dataset_keys)


if __name__ == "__main__":
    relay = Interface()
    dataset = insert_dataset()
    if dataset is None:
        print('Dataset failed insert!')
        sys.exit(1)

    print("Success!\n")
    print("{:<80} {:<30} {:<30}".format('ID', 'TABLE EXPIRATION', 'LOCATION'))
    print("{:<80} {:<30} {:<30}".format(
        dataset['id'],
        dataset['defaultTableExpirationMs'],
        dataset['location'],
    ))
    print('\nAdding dataset to the output `dataset`')
    print(dataset)
    relay.outputs.set("dataset", dataset)
