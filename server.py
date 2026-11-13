"""Local MVP. No API keys in the browser; do not expose to the public internet without authentication."""
from __future__ import annotations
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

import httpx
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel

from director import build_brief
from music_core import MAX_VIDEO_BYTES, safe_tags, validate_length, validate_model, validate_plan, validate_prompt

ROOT = Path(__file__).resolve().parent
# Read a local .env only if the environment variable has not already been set.
if (ROOT / '.env').is_file():
    for line in (ROOT / '.env').read_text('utf-8').splitlines():
        if '=' in line and not line.lstrip().startswith('#'):
            k, v = line.split('=', 1)
            if k.strip() and k.strip() not in os.environ:
                os.environ[k.strip()] = v.strip().strip('"').strip("'")

API_URL = 'https://api.elevenlabs.io/v1/music'
app = FastAPI(title='Eleven Music Director MVP', docs_url=None, redoc_url=None)

class BriefRequest(BaseModel):
    idea: str
    context: str = ''
    mode: str = 'auto'
    length_seconds: int = 30
    instrumental: bool = True

class PlanRequest(BaseModel):
    prompt: str
    length_seconds: int = 30
    model_id: str = 'music_v2_5'

class ComposeRequest(BaseModel):
    prompt: Optional[str] = None
    composition_plan: Optional[dict] = None
    length_seconds: int = 30
    model_id: str = 'music_v2_5'
    instrumental: bool = True


def api_key() -> str:
    key = os.getenv('ELEVENLABS_API_KEY', '').strip()
    if not key:
        raise HTTPException(503, '未配置 ELEVENLABS_API_KEY，音乐生成暂不可用')
    return key


def upstream_error(e: httpx.HTTPStatusError):
    # Avoid exposing secrets, request headers, and unnecessarily verbose upstream responses.
    try:
        body = e.response.json()
        detail = body.get('detail', body)
        if isinstance(detail, dict):
            status = detail.get('status', '')
            message = detail.get('message', '')
            return HTTPException(e.response.status_code, f'ElevenLabs：{status} {message}'[:500])
    except Exception:
        pass
    return HTTPException(e.response.status_code, f'上游接口返回 HTTP {e.response.status_code}')


@app.get('/')
async def home():
    return FileResponse(ROOT / 'index.html', media_type='text/html')


@app.get('/api/status')
async def status():
    return {'elevenlabs_ready':bool(os.getenv('ELEVENLABS_API_KEY')), 'ai_director_ready':bool(os.getenv('OPENAI_API_KEY')),
            'model_default':'music_v2_5','video_max_files':10,'video_max_total_mb':200,'video_max_seconds':600}


@app.post('/api/brief')
async def brief(req: BriefRequest):
    if len(req.idea.strip()) < 2:
        raise HTTPException(400, '请先描述想做的音乐')
    if req.mode not in ('auto', 'simple', 'advanced', 'video'):
        raise HTTPException(400, '创作模式不正确')
    if not 3 <= req.length_seconds <= 600:
        raise HTTPException(400, '创作时长应在 3–600 秒')
    key = os.getenv('OPENAI_API_KEY', '').strip()
    if not key:
        raise HTTPException(503, 'AI 音乐导演需要配置 OPENAI_API_KEY；不配置仍可使用普通音乐生成、官方计划生成和视频配乐')
    try:
        return await build_brief(key=key, model=os.getenv('OPENAI_MODEL', 'gpt-5.4-mini'),
                                 idea=req.idea.strip(), context=req.context,
                                 mode=req.mode, length_seconds=req.length_seconds, instrumental=req.instrumental)
    except httpx.HTTPStatusError as e:
        raise HTTPException(e.response.status_code, 'OpenAI 创作方案生成失败，请确认 Key / 模型权限 / 配额') from e
    except (httpx.HTTPError, ValueError, json.JSONDecodeError) as e:
        raise HTTPException(502, f'创作方案生成失败：{str(e)[:200]}') from e


@app.post('/api/plan')
async def plan(req: PlanRequest):
    try:
        prompt = validate_prompt(req.prompt)
        length_ms = validate_length(req.length_seconds * 1000)
        model = validate_model(req.model_id)
        if model == 'music_v1':
            raise ValueError('本工作台的结构化 plans 使用 music_v2_5 或 music_v2')
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    async with httpx.AsyncClient(timeout=180) as client:
        try:
            result = await client.post(API_URL + '/plan', headers={'xi-api-key': api_key()},
                json={'prompt':prompt,'music_length_ms':length_ms,'model_id':model})
            result.raise_for_status()
            return result.json()
        except httpx.HTTPStatusError as e:
            raise upstream_error(e) from e
        except httpx.HTTPError as e:
            raise HTTPException(502, '网络错误：无法连接 ElevenLabs') from e


@app.post('/api/compose')
async def compose(req: ComposeRequest):
    try:
        model = validate_model(req.model_id)
        if (req.prompt is None) == (req.composition_plan is None):
            raise ValueError('prompt 和 composition_plan 必须二选一')
        if req.prompt is not None:
            payload = {'prompt': validate_prompt(req.prompt), 'music_length_ms': validate_length(req.length_seconds*1000),
                       'model_id':model, 'force_instrumental':req.instrumental}
        else:
            payload = {'composition_plan':validate_plan(req.composition_plan, model), 'model_id':model}
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    async with httpx.AsyncClient(timeout=600) as client:
        try:
            result = await client.post(API_URL, headers={'xi-api-key':api_key()}, params={'output_format':'auto'},json=payload)
            result.raise_for_status()
            return Response(result.content, media_type=result.headers.get('content-type','audio/mpeg'),
                            headers={'Content-Disposition':'attachment; filename="eleven-music.mp3"',
                                     'X-Song-Id':result.headers.get('song-id', '')})
        except httpx.HTTPStatusError as e:
            raise upstream_error(e) from e
        except httpx.HTTPError as e:
            raise HTTPException(502, '音乐生成请求超时或网络异常') from e


@app.post('/api/video')
async def video(
    videos: list[UploadFile] = File(...), description: str = Form(''), tags: str = Form(''),
    model_id: str = Form('music_v2_5'), add_sfx: bool = Form(False),
    separate_tracks: bool = Form(False), use_audio_as_reference: bool = Form(False)
):
    if not 1 <= len(videos) <= 10:
        raise HTTPException(400, '一次仅支持 1–10 个视频')
    try:
        validate_model(model_id)
        if len(description) > 4100:
            raise ValueError('视频配乐描述不得超过 4100 字符')
        parsed_tags = safe_tags([t.strip() for t in tags.split(',') if t.strip()])
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    file_paths = []
    total_size = 0
    total_seconds = 0.0
    has_duration_probe = bool(shutil.which('ffprobe'))
    try:
        for video in videos:
            suffix = Path(video.filename or '').suffix.lower()
            if suffix not in ('.mp4', '.mov', '.webm', '.m4v', '.mkv'):
                raise HTTPException(400, '支持上传 mp4 / mov / webm / m4v / mkv 视频文件')
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as out:
                name = out.name
                file_paths.append(name)
                while block := await video.read(1024*1024):
                    total_size += len(block)
                    if total_size > MAX_VIDEO_BYTES:
                        raise HTTPException(413, '上传文件合计超过 200 MB')
                    out.write(block)
            if has_duration_probe:
                probe = subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','default=noprint_wrappers=1:nokey=1',name],
                                       capture_output=True, text=True, timeout=15)
                if probe.returncode != 0:
                    raise HTTPException(400, '无法读取视频时长或格式无效')
                try:
                    total_seconds += float(probe.stdout.strip())
                except ValueError:
                    raise HTTPException(400, '无法确定视频时长')
                if total_seconds > 600:
                    raise HTTPException(400, '视频总时长不得超过 600 秒')
        if not has_duration_probe:
            # Rely on the upstream duration validation, but preserve its error response.
            pass
        opened = [open(path, 'rb') for path in file_paths]
        try:
            multipart_files = [('videos[]',(Path(path).name, f, 'application/octet-stream')) for path,f in zip(file_paths,opened)]
            fields = {'description': description, 'model_id': model_id,
                      'add_sfx': str(add_sfx).lower(), 'separate_tracks': str(separate_tracks).lower(),
                      'use_audio_as_reference': str(use_audio_as_reference).lower()}
            # httpx expects a mapping for data; repeated list tags are additional multipart fields.
            multipart_files.extend(('tags[]', (None, t)) for t in parsed_tags)
            async with httpx.AsyncClient(timeout=900) as client:
                try:
                    result = await client.post(API_URL+'/video-to-music',
                                               headers={'xi-api-key':api_key()},
                                               files=multipart_files,data=fields)
                    result.raise_for_status()
                    is_zip = separate_tracks or 'zip' in result.headers.get('content-type','')
                    filename = 'eleven-video-music.zip' if is_zip else 'eleven-video-music.mp3'
                    return Response(result.content, media_type=result.headers.get('content-type', 'application/zip' if is_zip else 'audio/mpeg'),
                                    headers={'Content-Disposition':f'attachment; filename="{filename}"'})
                except httpx.HTTPStatusError as e:
                    raise upstream_error(e) from e
                except httpx.HTTPError as e:
                    raise HTTPException(502, '视频配乐请求超时或网络异常') from e
        finally:
            for f in opened:
                f.close()
    finally:
        for path in file_paths:
            Path(path).unlink(missing_ok=True)
