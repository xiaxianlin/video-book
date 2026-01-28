# MiniMax TTS 生成脚本使用说明

## 概述

本脚本使用 MiniMax API 为有声书片段生成高质量的中文语音。

## 前置要求

### 1. 安装依赖

```bash
pip install requests
```

### 2. 获取 MiniMax API Key

1. 访问 [MiniMax 平台](https://platform.minimaxi.com/)
2. 注册/登录账号
3. 在账户管理界面获取 API Key

### 3. 设置环境变量

```bash
export MINIMAX_API_KEY='your_api_key_here'
```

或者在 `.bashrc` / `.zshrc` 中添加：

```bash
echo 'export MINIMAX_API_KEY="your_api_key_here"' >> ~/.bashrc
source ~/.bashrc
```

## 使用方法

### 基本使用

```bash
python3 generate_tts_minimax.py
```

### 工作流程

脚本会自动：

1. 读取 `source/03_segmentation/tts_segments.json` 中的 TTS 片段
2. 读取 `source/02_casting/voice_mapping.json` 中的音色映射
3. 为每个片段调用 MiniMax API 生成音频
4. 将音频保存到 `source/04_tts_raw/` 目录
5. 生成日志文件 `generation_log.json` 和失败记录 `failed_segments.json`

## 音色配置

### 默认音色映射

脚本内置了默认的音色映射：

- **narrator** (旁白): `moss_audio_ce44fc67-7ce3-11f0-8de5-96e35d26fb85`
- **char_001** (周启明): `Chinese (Mandarin)_Lyrical_Voice`
- **char_002** (沈知夏): `Chinese (Mandarin)_Graceful_Lady`
- **char_003**: `Chinese (Mandarin)_Persuasive_Man`
- **char_004** (李桂芳): `Chinese (Mandarin)_Mature_Woman`
- **char_005**: `Chinese (Mandarin)_Steady_Man`
- **char_006** (王海生): `Chinese (Mandarin)_Professional_Man`
- **char_007**: `Chinese (Mandarin)_Young_Woman`
- **char_008**: `Chinese (Mandarin)_Neutral_Voice`

### 自定义音色

如果 `source/02_casting/voice_mapping.json` 存在，脚本会使用该文件中的配置。

示例格式：

```json
{
  "voice_assignments": {
    "narrator": "your_narrator_voice_id",
    "char_001": "your_char_001_voice_id",
    "char_002": "your_char_002_voice_id"
  }
}
```

### 获取可用音色列表

访问 MiniMax 平台的音色管理页面查看所有可用音色。

## 情感支持

脚本自动将对话归属中的情感标签映射到 MiniMax 支持的情感：

| 我们的标签 | MiniMax 情感 |
|-----------|-------------|
| happy | happy |
| sad, desperate, bitter, resigned, pleading | sad |
| angry, defensive, frustrated, threatening | angry |
| nervous, tense, fearful, panicked | fearful |
| surprised, shocked | surprised |
| calm, cold, professional, determined, sarcastic | calm |
| whisper | whisper |

## 配置选项

### TTS 模型

默认使用 `speech-2.8-hd`（最新高清模型）。可选：

- `speech-2.8-hd` - 最新高清模型（推荐）
- `speech-2.8-turbo` - 最新快速模型
- `speech-2.6-hd` - 高清模型
- `speech-2.6-turbo` - 快速模型

### 音频设置

- **采样率**: 32000 Hz
- **比特率**: 128000 bps
- **格式**: WAV（无损）
- **声道**: 单声道

## 输出文件

### 音频文件

- **位置**: `source/04_tts_raw/`
- **命名**: `{segment_id}.wav`
- **格式**: WAV, 32kHz, 128kbps, Mono

### 日志文件

#### generation_log.json

```json
{
  "timestamp": "2026-01-28 12:00:00",
  "stats": {
    "total": 761,
    "successful": 750,
    "failed": 5,
    "skipped": 6
  },
  "failed_count": 5
}
```

#### failed_segments.json

记录失败的片段，便于重试：

```json
[
  {
    "segment_id": "ch_001_seg_025",
    "error": "Failed to generate audio"
  }
]
```

## 错误处理

### 常见错误

1. **API Key 未设置**
   ```
   Error: MINIMAX_API_KEY environment variable not set
   ```
   解决：设置环境变量 `export MINIMAX_API_KEY='your_key'`

2. **速率限制**
   ```
   Error: Rate limit triggered (1002)
   ```
   解决：脚本会自动等待 0.5 秒，如仍失败可增加等待时间

3. **文本过长**
   ```
   Error: Text exceeds 10,000 characters
   ```
   解决：确保 TTS 片段长度不超过 10,000 字符

4. **非法字符过多**
   ```
   Error: Illegal characters exceed 10% (1042)
   ```
   解决：检查文本内容，移除特殊符号

### 重试失败的片段

脚本会跳过已存在的音频文件，因此可以直接重新运行来重试失败的片段：

```bash
python3 generate_tts_minimax.py
```

## 性能优化

### 并行处理（可选）

如需加快生成速度，可以修改脚本使用多线程：

```python
from concurrent.futures import ThreadPoolExecutor

# 在 main() 函数中
with ThreadPoolExecutor(max_workers=5) as executor:
    futures = [executor.submit(process_segment, seg) for seg in segments]
```

### 速率限制

脚本默认每次请求后等待 0.5 秒。根据你的 API 配额调整：

```python
time.sleep(0.5)  # 调整此值
```

## 成本估算

MiniMax TTS 定价（2026）：约 ¥0.015 / 1000 字符

示例：
- 11,861 字 ≈ ¥0.18
- 100,000 字 ≈ ¥1.50

## 故障排查

### 检查 API 连接

```bash
curl -X POST https://api.minimaxi.com/v1/t2a_v2 \
  -H "Authorization: Bearer $MINIMAX_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"speech-2.8-hd","text":"测试","voice_setting":{"voice_id":"moss_audio_ce44fc67-7ce3-11f0-8de5-96e35d26fb85"},"audio_setting":{"format":"wav"}}'
```

### 查看日志

```bash
# 查看生成日志
cat source/04_tts_raw/generation_log.json | jq

# 查看失败的片段
cat source/04_tts_raw/failed_segments.json | jq
```

### 验证音频文件

```bash
# 统计生成的音频文件
ls source/04_tts_raw/*.wav | wc -l

# 播放测试
ffplay source/04_tts_raw/ch_001_seg_001.wav
```

## 下一步

生成完成后，运行后处理脚本：

```bash
claude-code /postprocess-audio
```

该步骤会：
- 添加静音填充
- 标准化响度到 -18 LUFS
- 转换为 MP3 格式
- 合并为章节音频文件
