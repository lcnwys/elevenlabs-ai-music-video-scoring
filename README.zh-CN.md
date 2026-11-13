# MusePilot · ElevenLabs Music Director

**从“想要一种感觉”，到可以试听、修改和交付的音乐草案。**

[English](README.md) · 简体中文 · 原项目名称 Eleven Music Director v0.1

MusePilot 是面向视频创作者的本地 AI 音乐工作台。用自然语言描述情绪和节奏，先拿到创作方案，再用 ElevenLabs 生成音乐。你可以快速试一段，也可以编辑结构化编曲计划，或者直接为视频生成配乐。

## 谁可以用它

| 创作需求 | 使用路线 |
|---|---|
| 漫剧角色登场 / 情绪场面 | 从人物状态和剧情节奏出发，整理配器、速度和音乐方向 |
| 短剧预告 / 设计作品集 | 先做多个音乐方向，试听后再收敛 |
| 产品展示 / 广告口播 | 生成留出人声空间的器乐配乐 |
| 已剪辑的视频 | 上传视频并设置描述、标签、音效和分轨选项 |
| 更精细的创作控制 | 检查并修改 Composition Plan JSON 后生成 |

## 三条创作路线

| 路线 | 输入 → 输出 | 依赖 |
|---|---|---|
| 快速音乐 | 提示词 → 生成音频 | ElevenLabs Music |
| 专业计划 | 提示词 → Composition Plan → 手动编辑 → 生成音频 | ElevenLabs Music Plan + Music |
| 视频配乐 | 1–10 个视频 + 配乐参数 → 音频或分轨 ZIP | ElevenLabs Video-to-Music |

可选的 **AI 音乐导演**使用 OpenAI 将想法和你主动填写的上下文整理成结构化建议。它不会自动读取 ChatGPT 会话；没有 OpenAI Key 时，普通音乐、官方计划生成和视频配乐仍可使用。离线模板是预设草案，不等于 LLM 推理。

界面目前以中文为主；本仓库提供中英文文档，尚未提供完整英文界面。

## 技术栈与环境

| 层 | 实现 |
|---|---|
| 前端 | 单文件原生 HTML / CSS / JavaScript，浏览器 localStorage 草案库 |
| 后端 | Python、FastAPI、Uvicorn、Pydantic |
| API 通信 | HTTPX；ElevenLabs Music；可选 OpenAI Responses API |
| 视频检查 | ffprobe 检查时长；建议安装 FFmpeg 工具集 |
| 存储 | 上传视频暂存在系统临时目录；草案和反馈保存在当前浏览器 |
| 推荐环境 | Python 3.11 / 3.12、桌面浏览器；无外部数据库 |

## 快速开始

下载或克隆仓库，进入包含 `server.py` 和 `requirements.txt` 的根目录。现有文件夹名称为 `eleven-music-director-v1`。

### 安装依赖

建议 Python **3.11 或 3.12**，并为每个项目单独建立虚拟环境。本项目是 Python 应用，**不需要 Node.js、npm 或独立数据库**。建议使用较新的 Chrome、Edge、Firefox 或 Safari；实际媒体解码能力取决于浏览器。

macOS / Linux：

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Windows PowerShell：

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

如果 PowerShell 的执行策略不允许激活，可直接使用 `.\.venv\Scripts\python.exe -m pip install -r requirements.txt`，后续启动命令也使用该 Python 路径。

FFmpeg 安装示例：

```bash
# macOS（已安装 Homebrew）
brew install ffmpeg
# Ubuntu / Debian
sudo apt-get update
sudo apt-get install ffmpeg
```

Windows 请安装 FFmpeg 并将其 `bin` 目录加入 PATH。新开终端后确认：

```bash
ffmpeg -version
ffprobe -version
```

### 配置 `.env`

macOS / Linux：`cp .env.example .env`；PowerShell：`Copy-Item .env.example .env`。用本机编辑器填写：

```dotenv
ELEVENLABS_API_KEY=<your-elevenlabs-api-key>
# 可选：仅 AI 导演需要
OPENAI_API_KEY=<your-openai-api-key>
OPENAI_MODEL=gpt-5.4-mini
```

仅使用 ElevenLabs 时，把 `OPENAI_API_KEY` 留空即可。`OPENAI_MODEL` 取值需是账号可访问且支持当前结构化输出请求的模型；可按实际账号修改。程序只在相应环境变量尚未设置时读取 `.env`，终端环境变量优先。

```bash
python -m uvicorn server:app --host 127.0.0.1 --port 8765
```

打开 **http://127.0.0.1:8765**。直接双击 `index.html` 可编辑离线模板、计划示例与草案记录，但不能发起真实 AI 生成。

## 第一次创作可以这样做

1. 输入“为 30 秒悬疑漫剧做器乐配乐，开场克制，结尾揭示反转”。
2. 可选使用 AI 导演整理方案；检查情绪、乐器、节奏和时长。
3. 编辑最终提示词或 Composition Plan，点击生成并试听。
4. 把评价与创作版本保存在草案库；音频需要单独下载。
5. 导出草案 JSON，保留你的创作过程。视频路线输出的是音乐或音轨 ZIP，**不是已合成配乐的 MP4**。

示例提示词：

> Cinematic instrumental for a 30-second motion-comic teaser. Sparse piano and restrained low strings under dialogue. A short pause before the reveal, then a tense final rise. No vocals; keep the midrange open for speech.

## 配置、限制与数据流

| 项目 | 当前行为 |
|---|---|
| 普通音乐时长 | 应用校验为 3–600 秒，实际可用范围仍受接口和账号限制 |
| 视频上传 | 1–10 个视频，合计至多 200 MB；有 ffprobe 时校验合计不超过 600 秒 |
| 无 ffprobe | 依赖上游时长校验；建议安装后再处理真实素材 |
| 视频格式 | MP4 / MOV / WebM / M4V / MKV |
| 草案持久化 | 当前浏览器 localStorage，保留最近 100 条；清理浏览器数据会丢失，建议导出 |
| 临时视频 | 请求结束后执行删除；进程异常终止仍可能留下临时文件 |

音乐提示词、编曲计划和视频配乐输入发送给 ElevenLabs。只有主动使用 AI 导演时，你填写的想法与上下文才会发送给 OpenAI。API Key 从后端环境 / 本机 `.env` 读取，通过 HTTPS 认证头发给对应服务商；不返回给浏览器，也不写入草案。真实生成可能分别产生 ElevenLabs 和 OpenAI 费用，不承诺上游零留存。

这是音乐构思与生成工具，不是完整 DAW；不包含自动人声避让、镜头级音乐对齐、视频成片合成、声音克隆或团队账号。歌词、素材、生成内容的使用权需按相关服务条款与实际授权核实。

## 开发与接口

| 路径 | 用途 |
|---|---|
| `server.py` | 本地 Web 服务、上传校验和 Music API 代理 |
| `director.py` | 可选 OpenAI 导演方案生成 |
| `music_core.py` | 模型、时长、提示词和计划校验 |
| `index.html` | 工作台界面和本地草案库 |
| `skill/` | 音乐导演提示词、技能定义与参考配方 |

| 本地接口 | 用途 |
|---|---|
| `GET /api/status` | 连接配置状态，不返回密钥 |
| `POST /api/brief` | 可选 AI 导演方案 |
| `POST /api/plan` | 官方结构化音乐计划 |
| `POST /api/compose` | 由提示词或计划生成音频 |
| `POST /api/video` | multipart 视频配乐请求 |

开发检查：`python -m pytest -q`。测试不代表真实账号对所有模型有权限。

## 参考

- [ElevenLabs Composition Plans](https://elevenlabs.io/docs/eleven-api/guides/how-to/music/composition-plans)
- [ElevenLabs Video-to-Music](https://elevenlabs.io/docs/api-reference/music/video-to-music)
- 本地 [安装与能力说明](START_HERE.html)

## 本地部署与二次开发

以上命令启动的是**本机单用户服务**。终端保持运行即可使用，按 `Ctrl+C` 停止；重启时进入同一目录，激活同一虚拟环境，再执行启动命令。不同项目使用相同端口时，请停止前一个服务，或把 `--port` 改为未占用端口。

如需让服务长期运行，可由进程管理器管理同一条 Uvicorn 命令。正式向团队或公网提供服务之前，需要增加身份认证、用户数据隔离、任务队列、用量限制、日志脱敏和文件清理。当前仓库没有实现这些生产部署能力。

## 常见问题

| 问题 | 排查方向 |
|---|---|
| 找不到 `uvicorn` 或模块 | 确认已激活虚拟环境，并在项目根目录执行 `python -m pip install -r requirements.txt` |
| 找不到 FFmpeg / 无法读取媒体 | 检查 `ffmpeg -version`、`ffprobe -version`，安装后重启终端 |
| API 提示 401 / 403 | 检查本机 Key、对应产品权限和账号状态；不要把完整 Key 发到 Issue |
| API 提示 429 / 生成超时 | 检查额度、并发与网络；先用短素材验证，确认上游任务状态后再决定是否重新提交 |
| 浏览器无法播放 | 检查浏览器支持的封装与编码；可以下载到本地播放器检查 |
| 修改环境变量后仍未生效 | 在配置所在终端重启 Uvicorn |

## 参与改进

欢迎提交复现步骤、已脱敏报错和功能建议。漫剧对白被音乐遮住、译配字幕偏移、音乐情绪不匹配等具体场景，比单纯写“效果不好”更有帮助。请写明系统、Python / FFmpeg 版本、输入格式和最短复现流程；真实素材请先确认分享权限。

当前仓库尚未附带 `LICENSE`。公开源码本身不等于授予复用或再分发许可；许可范围需待维护者确定许可证后明确。API 使用、生成内容和依赖软件的授权另行适用。

## ElevenLabs 接入与价格咨询

这个项目由独立开发者维护，希望用一个能实际操作的小工具，帮助漫剧团队、视频创作者和产品开发者理解 ElevenLabs 的能力。

如果你正在做**漫剧配音、短剧出海、视频配乐、音效制作、语音产品或批量 API 集成**，欢迎联系我，一起评估适合的产品、工作流和接入方式。我也可以提供**有价格优势的 ElevenLabs 方案报价**，具体方案、适用条件和价格以实际需求及单独报价为准。

**咨询邮箱：[lcnwys@gmail.com](mailto:lcnwys@gmail.com)**

为了更快给出建议，邮件中可以写明：

- 你在做什么内容或产品，以及一段已脱敏的需求说明。
- 每月预计视频/音频分钟数、目标语言、团队规模和是否需要 API。
- 希望先做样片验证，还是正在准备上线。

请不要在邮件或公开 Issue 中发送 API Key、账号密码或未获授权的客户素材。功能问题适合提 Issue；商务和价格咨询请发邮件。

> 这是独立社区项目，并非 ElevenLabs 官方产品。咨询和报价也不代表官方背书；ElevenLabs 的名称和商标归其权利人所有。
