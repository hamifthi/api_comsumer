import asyncio
import os

from logging_config import setup_logging
from service_client import ClusterApiClient


logger = setup_logging()


async def main():
    hosts = os.getenv("CLUSTER_NODES").split(',')
    client = ClusterApiClient(hosts, logger)

    group_id = "test-group"

    # Create group
    if await client.create_group(group_id):
        logger.info("Group created successfully")

    # Get group information
    group_info = await client.get_group(group_id)
    if group_info:
        logger.info(f"Group info: {group_info}")
    else:
        logger.warning("Group not found")

    # Delete group
    if await client.delete_group(group_id):
        logger.info("Group deleted successfully")

if __name__ == '__main__':
    asyncio.run(main())
