# API Recipes (2026-11-03 verified)

Base URL: `https://api.elevenlabs.io`; header: `xi-api-key: $ELEVENLABS_API_KEY`. Music API requires a paid account.

## 纯音乐快速生成
```json
POST /v1/music
{
  "model_id": "music_v2_5",
  "prompt": "Intimate cinematic ambient piano, 78 BPM in A minor, soft felt piano arpeggios, restrained bowed strings, subtle tape warmth, gentle forward motion, instrumental only, no vocals, leave room for spoken narration, quiet hopeful ending.",
  "music_length_ms": 30000,
  "force_instrumental": true
}
```

## 专业分段生成
先 `POST /v1/music/plan` 生成计划，再校验或调整 chunks。示例供结构参考，不能同传 prompt。
```json
POST /v1/music
{
  "model_id": "music_v2_5",
  "composition_plan": {
    "chunks": [
      {"text":"[Intro]", "duration_ms":5000,"positive_styles":["warm cinematic electronic","soft felt piano","80 BPM","A minor","intimate close-mic texture","subtle pulse","restrained dynamics"],"negative_styles":["vocals","heavy drums"],"context_adherence":"high"},
      {"text":"[Build]", "duration_ms":15000,"positive_styles":["subtle analog bass pulse","slow rising strings","increasing emotional tension"],"negative_styles":["vocals","abrupt jump"],"context_adherence":"high"},
      {"text":"[Resolution]", "duration_ms":10000,"positive_styles":["gentle piano resolution","warm expansive strings","clean quiet ending"],"negative_styles":["vocals","aggressive percussion"],"context_adherence":"high"}
    ]
  }
}
```

## 视频配乐
FormData: repeated video files (`videos[]`), `description`, up to 10 `tags[]`, `model_id=music_v2_5`, `use_audio_as_reference`, `add_sfx`, `separate_tracks`.

## 后续修订
`POST /v1/music/detailed` with `store_for_inpainting:true`, keep `song-id` and original plan; for inpainting pass mix of stored audio reference chunks and regeneration chunks. Guide: https://elevenlabs.io/docs/eleven-api/guides/how-to/music/inpainting

## 坑
- `force_instrumental` only prompt route.
- UI 文档描述的“音频参考”不代表可以任意把音频文件直接发到 `/v1/music` JSON；应按专门的 Upload/Inpainting/Finetune 文档路径使用。
- 生成时长并不保证每一个视频剪辑点精确对齐；需要后期处理。
- 上传视频接口返回音频/ZIP，不是 MP4。
- 输出原始生成和用户已授权文件；使用者负责核实商用权益与地区限制。
