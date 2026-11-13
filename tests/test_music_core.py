import json
import pytest
from music_core import validate_model, validate_length, validate_prompt, validate_plan, safe_tags, parse_brief_json


def sample():
    return {'chunks':[{'text':'[Intro]','duration_ms':3000,'positive_styles':['cinematic','instrumental','80 BPM'],'negative_styles':['vocals'],'context_adherence':'high'}]}

def test_valid_plan():
    assert validate_plan(sample())['chunks'][0]['duration_ms']==3000

def test_model_v1_not_supported_for_chunks():
    with pytest.raises(ValueError): validate_plan(sample(), 'music_v1')

def test_invalid_chunk():
    plan=sample();plan['chunks'][0]['duration_ms']=2000
    with pytest.raises(ValueError):validate_plan(plan)

def test_max_total():
    plan={'chunks':[dict(sample()['chunks'][0],duration_ms=120000) for _ in range(6)]}
    with pytest.raises(ValueError):validate_plan(plan)

def test_prompt_cap():
    with pytest.raises(ValueError):validate_prompt('a'*4101)
    with pytest.raises(ValueError):validate_prompt('   ')

def test_timing_and_tags():
    assert validate_length(3000)==3000
    with pytest.raises(ValueError):validate_length(601000)
    assert safe_tags(['cinematic','ambient']) == ['cinematic','ambient']
    with pytest.raises(ValueError):safe_tags(['a']*11)

def test_structured_response_parsing():
    example={'output':[{'content':[{'type':'output_text','text':json.dumps({'prompt_en':'Original cinematic piano'})}]}]}
    assert parse_brief_json(example)['prompt_en']=='Original cinematic piano'

def test_inpainting_reference():
    p={'chunks':[{'song_id':'song123','range':{'start_ms':0,'end_ms':10000}},sample()['chunks'][0]]}
    assert validate_plan(p)==p
