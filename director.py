"""Optional conversational music-director reasoning through OpenAI Responses API."""
from __future__ import annotations
from pathlib import Path
from typing import Any
import httpx
from music_core import parse_brief_json

SYSTEM = (Path(__file__).parent / 'skill' / 'SYSTEM_PROMPT.txt').read_text('utf-8')

# Strict output: The UI's user-facing brief is a suggestion, not an API guarantee.
MUSIC_SCHEMA = {
    'type':'object','additionalProperties':False,
    'properties': {
        'title':{'type':'string'},
        'summary_cn':{'type':'string'},
        'reason_cn':{'type':'string'},
        'recommended_route':{'type':'string','enum':['simple','advanced','video']},
        'prompt_en':{'type':'string'},
        'tempo_bpm':{'type':'integer'},
        'key':{'type':'string'},
        'meter':{'type':'string'},
        'harmonic_idea':{'type':'string'},
        'instrumental':{'type':'boolean'},
        'length_seconds':{'type':'integer'},
        'tags_en':{'type':'array','items':{'type':'string'}},
        'sections':{'type':'array','items':{'type':'object','additionalProperties':False,
            'properties':{'name':{'type':'string'}, 'duration_seconds':{'type':'integer'}, 'direction_en':{'type':'string'}, 'lyrics':{'type':'string'}},
            'required':['name','duration_seconds','direction_en','lyrics']
        }},
        'cautions_cn':{'type':'array','items':{'type':'string'}}
    },
    'required':['title','summary_cn','reason_cn','recommended_route','prompt_en','tempo_bpm','key','meter','harmonic_idea','instrumental','length_seconds','tags_en','sections','cautions_cn']
}

async def build_brief(*, key: str, model: str, idea: str, context: str, mode: str, length_seconds: int, instrumental: bool) -> dict[str, Any]:
    payload = {'idea': idea, 'chat_or_event_context':context[:12000], 'requested_mode':mode,
               'length_seconds': length_seconds, 'instrumental': instrumental}
    req = {
        'model':model,
        'instructions':SYSTEM,
        'input':[{'role':'user','content':__import__('json').dumps(payload, ensure_ascii=False)}],
        'text':{'format':{'type':'json_schema','name':'music_director_brief','strict':True,'schema':MUSIC_SCHEMA}},
        'max_output_tokens':3500,
    }
    async with httpx.AsyncClient(timeout=120) as client:
        response = await client.post('https://api.openai.com/v1/responses',
            headers={'Authorization':f'Bearer {key}','Content-Type':'application/json'},json=req)
        response.raise_for_status()
        brief = parse_brief_json(response.json())
    # User-specified duration is authoritative; the draft sections are suggestions.
    brief['length_seconds'] = length_seconds
    brief['tags_en'] = [str(x)[:100] for x in brief.get('tags_en', [])[:10]]
    brief['prompt_en'] = str(brief['prompt_en'])[:4100]
    return brief
