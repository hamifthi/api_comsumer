import logging
from typing import List

import httpx


class ClusterApi:
    def __init__(self, hosts: List[str], logger: logging.Logger):
        # Use dependency injection to inject required dependencies
        self.hosts = hosts
        self.logger = logger

    async def create_group(self, group_id: str) -> bool:
        async with httpx.AsyncClient() as client:
            succeeded_hosts = []
            try:
                for host in self.hosts:
                    response = await client.post(f"https://{host}/v1/group/", json={"groupId": group_id})
                    if response.status_code == 201:
                        succeeded_hosts.append(host)
                    elif response.status_code == 400:
                        raise httpx.HTTPError(f"Bad Request: Group {group_id} already exists on {host}")
                    elif response.status_code == 504:
                        raise httpx.RequestError(f"Connection time out on {host}")
                    else:
                        raise httpx.HTTPError(f"Failed to create group: {response.status_code}")
            except (httpx.RequestError, httpx.HTTPError) as error:
                self.logger.warning(f"Error creating groups due to the {error} on host {host}")
                await self._rollback_create(client, succeeded_hosts, group_id)
                return False
            return True

    async def delete_group(self, group_id: str) -> bool:
        async with httpx.AsyncClient() as client:
            succeeded_hosts = []
            try:
                for host in self.hosts:
                    response = await client.delete(f"https://{host}/v1/group/", params={"groupId": group_id})
                    if response.status_code == 200:
                        succeeded_hosts.append(host)
                    elif response.status_code == 400:
                        raise httpx.HTTPError(f"Bad Request: Group {group_id} not found on {host}")
                    elif response.status_code == 504:
                        raise httpx.RequestError(f"Connection time out on {host}")
                    else:
                        raise httpx.HTTPError(f"Failed to create group: {response.status_code}")
            except (httpx.RequestError, httpx.HTTPError) as error:
                self.logger.warning(f"Error deleting groups due to the {error} on host {host}")
                await self._rollback_delete(client, succeeded_hosts, group_id)
                return False
            return True

    async def _rollback_create(self, client: httpx.AsyncClient, succeeded_hosts: List[str], group_id: str):
        for host in succeeded_hosts:
            await client.delete(f"http://{host}/v1/group/", params={"groupId": group_id})

    async def _rollback_delete(self, client: httpx.AsyncClient, succeeded_hosts: List[str], group_id: str):
        for host in succeeded_hosts:
            await client.post(f"http://{host}/v1/group/", json={"groupId": group_id})
