# Api Consumer

This is a Python client library for interacting with a cluster API. It provides methods to create, delete, and fetch groups within the cluster. The client is designed to handle retries on request failures and includes robust logging for debugging and monitoring purposes.

## Features

- **Create Group**: Create a new group in the cluster.
- **Delete Group**: Delete an existing group from the cluster.
- **Fetch Group**: Retrieve details of a specific group from the cluster.
- **Retry Mechanism**: Automatically retries failed requests with exponential backoff.
- **Logging**: Detailed logging for monitoring and debugging.

## Requirements

- Python 3.12+
- `httpx`
- `tenacity`
- `pytest` (for running tests)

## Running

You can run the project by pulling the docker image from docker hub `docker image pull hamedfathi75/api_consumer` <br>
and run it using this command `docker run --rm -e CLUSTER_NODES="node1.example.com,node2.example.com,node3.example.com" hamedfathi75/api_consumer:v1.0.0`

## Kubernetes

It is also already available for kubernetes where you could also run it with <br>
`kubectl apply -f manifests/deployment.yml` <br>
`kubectl apply -f manifests/configmap.yml`

## Design decisions

- Using Asyncio to use multithread and make the calls with async and await. 
- The retry functionality is because making the api calls more reliable.
- Using pytest to write the unit tests.
- I use dependency injection to inject the dependencies to the api client class and define logging config in a separate
 file.
- I use mock for tests also mock the sleep inside the retry to make tests fast.
- I try to make the docker image as lightweight as possible.
- Also, the class is open to future development based on open close principle.
- The rollback functionality is provided to make sure the endpoints won't create or remove groups in some nodes and not the others.

