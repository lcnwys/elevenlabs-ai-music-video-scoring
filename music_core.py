"""Music director request validators and pure helpers (no network calls)."""
from __future__ import annotations
import json
from typing import Any

ALLOWED_MODELS = {'music_v1', 'music_v2', 'music_v2_5'}
MAX_PLAN_LENGTH_MS = 600_000
MAX_VIDEO_BYTES = 200_000_000


def validate_model(model: str) -> str:
    if model not in ALLOWED_MODELS:
        raise ValueError('不支持的 Music 模型')
    return model


def validate_prompt(prompt: str) -> str:
    prompt = (prompt or '').strip()
    if not prompt:
        raise ValueError('请输入音乐创作描述')
    if len(prompt) > 4100:
        raise ValueError('提示词不得超过 4100 字符')
    return prompt


def validate_length(ms: int | None) -> int | None:
    if ms is not None and not (3000 <= int(ms) <= MAX_PLAN_LENGTH_MS):
        raise ValueError('音乐时长应在 3 至 600 秒')
    return int(ms) if ms is not None else None


def validate_plan(plan: dict[str, Any], model: str = 'music_v2_5') -> dict[str, Any]:
    validate_model(model)
    if model not in ('music_v2', 'music_v2_5'):
        raise ValueError('当前界面仅支持 music_v2/v2_5 的 chunks 编曲计划')
    if not isinstance(plan, dict) or not isinstance(plan.get('chunks'), list):
        raise ValueError('Composition Plan 必须包含 chunks 数组')
    chunks = plan['chunks']
    if not 1 <= len(chunks) <= 30:
        raise ValueError('Composition Plan 应有 1–30 个 chunks')
    total = 0
    for idx, chunk in enumerate(chunks):
        if not isinstance(chunk, dict):
            raise ValueError(f'chunk {idx+1} 必须是对象')
        if 'song_id' in chunk:  # inpainting reference chunk: handled on server by ElevenLabs
            if not isinstance(chunk['song_id'], str) or not chunk['song_id']:
                raise ValueError(f'chunk {idx+1} 缺少有效 song_id')
            r = chunk.get('range')
            if r is not None and (not isinstance(r, dict) or not isinstance(r.get('start_ms'), int) or not isinstance(r.get('end_ms'), int) or r['end_ms'] <= r['start_ms']):
                raise ValueError(f'chunk {idx+1} 的 range 无效')
            if isinstance(r, dict):
                total += r['end_ms'] - r['start_ms']
            continue
        duration = chunk.get('duration_ms')
        if not isinstance(duration, int) or not 3000 <= duration <= 120000:
            raise ValueError(f'chunk {idx+1} 时长应为 3000–120000 ms')
        if not isinstance(chunk.get('text'), str) or not chunk['text'].strip().startswith('['):
            raise ValueError(f'chunk {idx+1} 的 text 应以 [段落名称] 开头')
        for name in ('positive_styles', 'negative_styles'):
            arr = chunk.get(name, [])
            if not isinstance(arr, list) or len(arr) > 50 or any(not isinstance(s, str) for s in arr):
                raise ValueError(f'chunk {idx+1} 的 {name} 必须是最多 50 项的字符串数组')
        if chunk.get('context_adherence', 'high') not in ('low', 'medium', 'high'):
            raise ValueError(f'chunk {idx+1} context_adherence 不正确')
        total += duration
    # For inpainting references without range, total time cannot be locally calculated.
    if all(('song_id' not in c or 'range' in c) for c in chunks):
        if not 3000 <= total <= MAX_PLAN_LENGTH_MS:
            raise ValueError('Composition Plan 总时长应在 3–600 秒')
    return plan


def safe_tags(tags: list[str]) -> list[str]:
    if len(tags) > 10:
        raise ValueError('视频风格 tags 最多 10 项')
    if any(not isinstance(t, str) or len(t) > 100 for t in tags):
        raise ValueError('风格标签格式不正确')
    return [t.strip() for t in tags if t.strip()]


def extract_response_text(data: dict[str, Any]) -> str:
    for output in data.get('output', []):
        for content in output.get('content', []):
            if content.get('type') == 'output_text' and isinstance(content.get('text'), str):
                return content['text']
    raise ValueError('AI 未返回可读取的创作方案')


def parse_brief_json(response: dict[str, Any]) -> dict[str, Any]:
    parsed = json.loads(extract_response_text(response))
    if not isinstance(parsed, dict) or not isinstance(parsed.get('prompt_en'), str):
        raise ValueError('AI 创作方案缺少 prompt_en')
    return parsed
