import pytest
import httpx
import os
import logging
from httpx import Response
from dotenv import load_dotenv
from unittest.mock import patch, AsyncMock
from service_client import ClusterApiClient


pytest_plugins = ('pytest_asyncio',)


@pytest.fixture
def hosts():
    load_dotenv()
    return os.getenv("CLUSTER_NODES").split(",")


@pytest.fixture
def logger():
    logging.basicConfig(level=logging.DEBUG)
    return logging.getLogger("ClusterApiClient")


@pytest.fixture
def api_client(logger, hosts):
    return ClusterApiClient(hosts, logger)


@pytest.mark.asyncio
async def test_create_group_success(api_client):
    with patch('httpx.AsyncClient.post', new=AsyncMock(return_value=Response(201))):
        result = await api_client.create_group("test-group")
        assert result is True


@pytest.mark.asyncio
async def test_create_group_bad_request(api_client):
    with patch('httpx.AsyncClient.post', new=AsyncMock(return_value=Response(400))):
        result = await api_client.create_group("test-group")
        assert result is False


@pytest.mark.asyncio
async def test_create_group_connection_timeout(api_client):
    with patch('httpx.AsyncClient.post', new=AsyncMock(return_value=Response(504))):
        result = await api_client.create_group("test-group")
        assert result is False


@pytest.mark.asyncio
async def test_create_group_timeout(api_client):
    with patch('httpx.AsyncClient.post', new=AsyncMock(side_effect=httpx.TimeoutException("Connection time out"))):
        api_client._post_with_retry.retry.sleep = AsyncMock()
        result = await api_client.create_group("test-group")
        assert result is False


@pytest.mark.asyncio
async def test_create_group_unexpected_error(api_client):
    with patch('httpx.AsyncClient.post', new=AsyncMock(return_value=Response(401))):
        result = await api_client.create_group("test-group")
        assert result is False


@pytest.mark.asyncio
async def test_delete_group_success(api_client):
    with patch('httpx.AsyncClient.delete', new=AsyncMock(return_value=Response(200))):
        result = await api_client.delete_group("test-group")
        assert result is True


@pytest.mark.asyncio
async def test_delete_group_not_found(api_client):
    with patch('httpx.AsyncClient.delete', new=AsyncMock(return_value=Response(400))):
        result = await api_client.delete_group("test-group")
        assert result is False


@pytest.mark.asyncio
async def test_delete_group_connection_timeout(api_client):
    with patch('httpx.AsyncClient.delete', new=AsyncMock(return_value=Response(504))):
        result = await api_client.delete_group("test-group")
        assert result is False


@pytest.mark.asyncio
async def test_delete_group_timeout(api_client):
    with patch('httpx.AsyncClient.delete', new=AsyncMock(side_effect=httpx.RequestError("Bad Request"))):
        api_client._delete_with_retry.retry.sleep = AsyncMock()
        result = await api_client.delete_group("test-group")
        assert result is False


@pytest.mark.asyncio
async def test_delete_group_timeout(api_client):
    with patch('httpx.AsyncClient.delete', new=AsyncMock(return_value=Response(403))):
        result = await api_client.delete_group("test-group")
        assert result is False


@pytest.mark.asyncio
async def test_get_group_success(api_client):
    with patch('httpx.AsyncClient.get', new=AsyncMock(return_value=Response(200, json={"groupId": "test-group"}))):
        result = await api_client.get_group("test-group")
        assert result == {"groupId": "test-group"}


@pytest.mark.asyncio
async def test_get_group_not_found(api_client):
    with patch('httpx.AsyncClient.get', new=AsyncMock(return_value=Response(404))):
        result = await api_client.get_group("test-group")
        assert result is None


@pytest.mark.asyncio
async def test_get_group_connection_timeout(api_client):
    with patch('httpx.AsyncClient.get', new=AsyncMock(return_value=Response(504))):
        result = await api_client.get_group("test-group")
        assert result is None
