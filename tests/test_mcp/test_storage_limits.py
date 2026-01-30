"""Tests for budget limits storage."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.fixture
def mock_worksheet():
    """Create mock worksheet."""
    ws = MagicMock()
    ws.get_all_values = MagicMock(return_value=[
        ["Категория", "Лимит"],
        ["Еда", "10000"],
        ["Транспорт", "5000"],
    ])
    ws.update = MagicMock()
    ws.delete_rows = MagicMock()
    return ws


@pytest.fixture
def mock_spreadsheet(mock_worksheet):
    """Create mock spreadsheet."""
    ss = MagicMock()
    ss.worksheet = MagicMock(return_value=mock_worksheet)
    ss.add_worksheet = MagicMock(return_value=mock_worksheet)
    return ss


@pytest.mark.asyncio
async def test_get_limits_returns_dict(mock_spreadsheet, mock_worksheet):
    """Test that get_limits returns category: amount dict."""
    from src.mcp.storage.sheets import GoogleSheetsStorage

    storage = GoogleSheetsStorage()
    storage._spreadsheet = mock_spreadsheet
    storage._client = MagicMock()

    with patch.object(storage, '_run_sync', new_callable=AsyncMock) as mock_run:
        mock_run.side_effect = [mock_worksheet, mock_worksheet.get_all_values()]

        result = await storage.get_limits("user123")

        assert result["status"] == "success"
        assert result["limits"]["Еда"] == 10000.0
        assert result["limits"]["Транспорт"] == 5000.0


@pytest.mark.asyncio
async def test_get_limits_empty_sheet(mock_spreadsheet):
    """Test get_limits with empty limits sheet."""
    from src.mcp.storage.sheets import GoogleSheetsStorage

    mock_ws = MagicMock()
    mock_ws.get_all_values = MagicMock(return_value=[["Категория", "Лимит"]])
    mock_spreadsheet.worksheet = MagicMock(return_value=mock_ws)

    storage = GoogleSheetsStorage()
    storage._spreadsheet = mock_spreadsheet
    storage._client = MagicMock()

    with patch.object(storage, '_run_sync', new_callable=AsyncMock) as mock_run:
        mock_run.side_effect = [mock_ws, mock_ws.get_all_values()]

        result = await storage.get_limits("user123")

        assert result["status"] == "success"
        assert result["limits"] == {}


@pytest.mark.asyncio
async def test_set_limit_new_category(mock_spreadsheet, mock_worksheet):
    """Test setting limit for new category."""
    from src.mcp.storage.sheets import GoogleSheetsStorage

    storage = GoogleSheetsStorage()
    storage._spreadsheet = mock_spreadsheet
    storage._client = MagicMock()

    with patch.object(storage, '_run_sync', new_callable=AsyncMock) as mock_run:
        # First call: get worksheet, second: get values, third: update
        mock_run.side_effect = [mock_worksheet, mock_worksheet.get_all_values(), None]

        result = await storage.set_limit("user123", "Продукты", 15000)

        assert result["status"] == "success"
        assert result["category"] == "Продукты"
        assert result["limit"] == 15000


@pytest.mark.asyncio
async def test_set_limit_zero_deletes(mock_spreadsheet, mock_worksheet):
    """Test that setting limit to 0 deletes the limit."""
    from src.mcp.storage.sheets import GoogleSheetsStorage

    storage = GoogleSheetsStorage()
    storage._spreadsheet = mock_spreadsheet
    storage._client = MagicMock()

    with patch.object(storage, '_run_sync', new_callable=AsyncMock) as mock_run:
        mock_run.side_effect = [mock_worksheet, mock_worksheet.get_all_values(), None]

        result = await storage.set_limit("user123", "Еда", 0)

        assert result["status"] == "success"
        assert result["deleted"] is True


@pytest.mark.asyncio
async def test_delete_limit(mock_spreadsheet, mock_worksheet):
    """Test deleting a limit."""
    from src.mcp.storage.sheets import GoogleSheetsStorage

    storage = GoogleSheetsStorage()
    storage._spreadsheet = mock_spreadsheet
    storage._client = MagicMock()

    with patch.object(storage, '_run_sync', new_callable=AsyncMock) as mock_run:
        mock_run.side_effect = [mock_worksheet, mock_worksheet.get_all_values(), None]

        result = await storage.delete_limit("user123", "Еда")

        assert result["status"] == "success"
