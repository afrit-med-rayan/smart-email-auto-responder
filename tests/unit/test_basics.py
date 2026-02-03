import pytest

def test_basic_assertion():
    assert 1 + 1 == 2

@pytest.mark.asyncio
async def test_async_basic():
    await asyncio.sleep(0.01)
    assert True
