import os
from pathlib import Path
import httpx
import pytest
from server import app

@pytest.mark.asyncio
async def test_status():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://local') as cli:
        r=await cli.get('/api/status')
        assert r.status_code==200
        assert r.json()['model_default']=='music_v2_5'

@pytest.mark.asyncio
async def test_index():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://local') as cli:
        r=await cli.get('/')
        assert r.status_code==200 and 'AI 音乐导演' in r.text

@pytest.mark.asyncio
async def test_invalid_request_skips_remote():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://local') as cli:
        r=await cli.post('/api/compose',json={'prompt':'hello','composition_plan':{'chunks':[]}})
        assert r.status_code==400
        r=await cli.post('/api/plan',json={'prompt':'example','length_seconds':1})
        assert r.status_code==400
