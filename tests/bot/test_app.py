import pytest
from httpx import AsyncClient
from src.bot.app import create_app

# Создаем экземпляр приложения для тестов
app = create_app()

@pytest.mark.asyncio
async def test_health_check():
    """
    Tests that the /health endpoint returns a 200 status code
    and the correct JSON response.
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health")
    
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}
