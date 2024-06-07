import logging
from typing import List, Optional, Dict

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type, before_sleep_log


class ClusterApiClient:
    def __init__(self, hosts: List[str], logger: logging.Logger):
        # Use dependency injection to inject required dependencies
        self.hosts = hosts
        self.logger = logger

    @retry(
        stop=stop_after_attempt(6),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(httpx.RequestError),
        before_sleep=before_sleep_log(logging.getLogger("tenacity.retry"), logging.WARNING),
        reraise=True
    )
    async def _post_with_retry(self, client: httpx.AsyncClient, url: str, json: Dict):
        return await client.post(url, json=json)

    @retry(
        stop=stop_after_attempt(6),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(httpx.RequestError),
        before_sleep=before_sleep_log(logging.getLogger("tenacity.retry"), logging.WARNING),
        reraise=True
    )
    async def _delete_with_retry(self, client: httpx.AsyncClient, url: str):
        return await client.delete(url)

    @retry(
        stop=stop_after_attempt(6),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(httpx.RequestError),
        before_sleep=before_sleep_log(logging.getLogger("tenacity.retry"), logging.WARNING),
        reraise=True
    )
    async def _get_with_retry(self, client: httpx.AsyncClient, url: str):
        return await client.get(url)

    async def create_group(self, group_id: str) -> bool:
        async with httpx.AsyncClient() as client:
            succeeded_hosts = []
            try:
                for host in self.hosts:
                    url = f"https://{host}/v1/group/"
                    response = await self._post_with_retry(client, url, json={"groupId": group_id})
                    if response.status_code == 201:
                        succeeded_hosts.append(host)
                    elif response.status_code == 400:
                        raise httpx.RequestError(f"Bad Request: Group {group_id} already exists on {host}")
                    elif response.status_code == 504:
                        raise httpx.TimeoutException(f"Connection time out on {host}")
                    else:
                        raise httpx.HTTPError(f"Create group: unexpected error happened on {host}"
                                              f" with status code {response.status_code}")
            except (httpx.RequestError, httpx.TimeoutException, httpx.HTTPError) as error:
                self.logger.warning(f"Error creating groups due to the {error} on host {host}")
                await self._rollback_create(client, succeeded_hosts, group_id)
                return False
            return True

    async def delete_group(self, group_id: str) -> bool:
        async with httpx.AsyncClient() as client:
            succeeded_hosts = []
            try:
                for host in self.hosts:
                    url = f"https://{host}/v1/group?groupId=group_id"
                    response = await self._delete_with_retry(client, url)
                    if response.status_code == 200:
                        succeeded_hosts.append(host)
                    elif response.status_code == 400:
                        raise httpx.RequestError(f"Bad Request: Group {group_id} not found on {host}")
                    elif response.status_code == 504:
                        raise httpx.TimeoutException(f"Connection time out on {host}")
                    else:
                        raise httpx.HTTPError(f"Delete group: unexpected error happened on {host}"
                                              f" with status code {response.status_code}")
            except (httpx.RequestError, httpx.TimeoutException, httpx.HTTPError) as error:
                self.logger.warning(f"Error deleting groups due to the {error} on host {host}")
                await self._rollback_delete(client, succeeded_hosts, group_id)
                return False
            return True

    async def get_group(self, group_id: str) -> Optional[Dict[str, str]]:
        async with httpx.AsyncClient() as client:
            try:
                for host in self.hosts:
                    url = f"https://{host}/v1/group?groupId=group_id"
                    response = await self._get_with_retry(client, url)
                    if response.status_code == 200:
                        return response.json()
                    elif response.status_code == 404:
                        self.logger.info(f"Group {group_id} not found on {host}")
                    else:
                        self.logger.warning(f"Failed to fetch group {group_id} from {host} because of"
                                            f" {response.status_code}")
            except (httpx.HTTPError, httpx.HTTPStatusError) as error:
                self.logger.warning(f"Request error when fetching group {group_id} from {host}: {error}")
        return None

    async def _rollback_create(self, client: httpx.AsyncClient, succeeded_hosts: List[str], group_id: str):
        for host in succeeded_hosts:
            await client.delete(f"http://{host}/v1/group/", params={"groupId": group_id})

    async def _rollback_delete(self, client: httpx.AsyncClient, succeeded_hosts: List[str], group_id: str):
        for host in succeeded_hosts:
            await client.post(f"http://{host}/v1/group/", json={"groupId": group_id})
