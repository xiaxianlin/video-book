---
name: generate-tts-audio
description: Generate audio files from text segments using MiniMax TTS API with retry logic and error handling. Use after TTS segments are built or when the user requests to generate audio from text segments.
---

# 生成 TTS 音频 Skill

## 目的
使用 MiniMax TTS API 从文本片段生成高质量中文音频文件，包含重试逻辑和错误处理。

## 输入
- `source/03_segmentation/tts_segments.json` - TTS 就绪片段
- `source/02_casting/voice_mapping.json` - 音色映射配置
- 环境变量：`MINIMAX_API_KEY`

## 输出
- `source/04_tts_raw/*.wav` - 原始 TTS 音频文件
- `source/04_tts_raw/generation_log.json` - 生成日志
- `source/04_tts_raw/failed_segments.json` - 失败片段列表

## 执行指令

当此 skill 被调用时：

### 1. 验证前置条件

检查必需的文件和环境变量：

```bash
# 检查 API Key
if [ -z "$MINIMAX_API_KEY" ]; then
  echo "Error: MINIMAX_API_KEY environment variable not set"
  echo "Please set it with: export MINIMAX_API_KEY='your_api_key'"
  exit 1
fi

# 检查 TTS 片段文件
if [ ! -f "source/03_segmentation/tts_segments.json" ]; then
  echo "Error: TTS segments file not found"
  echo "Please run /build-segments first"
  exit 1
fi

# 创建输出目录
mkdir -p source/04_tts_raw
```

### 2. 运行 TTS 生成脚本

执行 MiniMax TTS 生成脚本：

```bash
cd /Users/bytedance/projects/video-book
python3 .claude/skills/generate-tts-audio/generate_tts_minimax.py
```

### 3. 脚本功能说明

脚本会自动执行以下操作：

#### a. 加载配置
- 读取 `source/02_casting/voice_mapping.json` 中的音色映射
- 如果文件不存在，使用内置的默认音色映射
- 加载 `source/03_segmentation/tts_segments.json` 中的所有片段

#### b. API 配置
- **API 端点**: `https://api.minimaxi.com/v1/t2a_v2`
- **备用端点**: `https://api-bj.minimaxi.com/v1/t2a_v2`
- **模型**: `speech-2.8-hd`（最新高清模型）
- **音频格式**: WAV, 32kHz, 128kbps, Mono
- **认证**: Bearer Token

#### c. 处理每个片段
对于每个 TTS 片段：

1. **检查是否已存在**
   - 如果 `source/04_tts_raw/{segment_id}.wav` 已存在，跳过
   - 支持断点续传

2. **准备 API 请求**
   ```python
   payload = {
       'model': 'speech-2.8-hd',
       'text': segment_text,
       'voice_setting': {
           'voice_id': voice_id,
           'speed': 1.0,
           'vol': 1.0,
           'pitch': 0,
           'emotion': emotion  # 如果有情感标签
       },
       'audio_setting': {
           'sample_rate': 32000,
           'bitrate': 128000,
           'format': 'wav',
           'channel': 1
       }
   }
   ```

3. **发送请求并处理响应**
   - 主 API 失败时自动切换到备用 API
   - 超时时间：60 秒
   - 成功：将 hex 编码的音频转换为 bytes 并保存
   - 失败：记录到 failed_segments.json

4. **速率控制**
   - 每次请求后等待 0.5 秒
   - 避免触发 API 速率限制

#### d. 情感映射

脚本自动将对话归属中的情感标签映射到 MiniMax 支持的情感：

| 源情感 | MiniMax 情感 |
|--------|-------------|
| happy, mocking | happy |
| sad, desperate, bitter, resigned, pleading | sad |
| angry, defensive, frustrated, threatening | angry |
| nervous, tense, fearful, panicked | fearful |
| surprised, shocked | surprised |
| calm, cold, professional, determined, sarcastic | calm |
| whisper | whisper |

### 4. 生成日志

脚本会创建 `source/04_tts_raw/generation_log.json`：

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

### 5. 失败处理

如有失败的片段，会创建 `source/04_tts_raw/failed_segments.json`：

```json
[
  {
    "segment_id": "ch_001_seg_025",
    "error": "Failed to generate audio"
  }
]
```

### 6. 报告结果

脚本会输出详细的统计信息：

```
============================================================
TTS Generation Complete
Total segments: 761
Successful: 750
Failed: 5
Skipped: 6
============================================================
```

## 音色配置

### 默认音色映射

如果 `source/02_casting/voice_mapping.json` 不存在，使用以下默认映射：

- **narrator**: `moss_audio_ce44fc67-7ce3-11f0-8de5-96e35d26fb85`
- **char_001** (周启明): `Chinese (Mandarin)_Lyrical_Voice`
- **char_002** (沈知夏): `Chinese (Mandarin)_Graceful_Lady`
- **char_003** (赵建成): `Chinese (Mandarin)_Persuasive_Man`
- **char_004** (李桂芳): `Chinese (Mandarin)_Mature_Woman`
- **char_005** (陈涛/林哥): `Chinese (Mandarin)_Steady_Man`
- **char_006** (王海生): `Chinese (Mandarin)_Professional_Man`
- **char_007** (其他女性): `Chinese (Mandarin)_Young_Woman`
- **char_008** (其他中性): `Chinese (Mandarin)_Neutral_Voice`

### 自定义音色

可以编辑 `source/02_casting/voice_mapping.json` 来自定义音色：

```json
{
  "voice_assignments": {
    "narrator": "your_narrator_voice_id",
    "char_001": "your_char_001_voice_id"
  }
}
```

## 验证

生成完成后，验证输出：

```bash
# 统计生成的音频文件
ls source/04_tts_raw/*.wav | wc -l

# 查看生成日志
cat source/04_tts_raw/generation_log.json | jq

# 播放测试
ffplay source/04_tts_raw/ch_001_seg_001.wav

# 检查文件大小（确保不为 0）
find source/04_tts_raw -name "*.wav" -size 0
```

## 错误处理

### 常见错误及解决方案

1. **API Key 未设置**
   ```
   Error: MINIMAX_API_KEY environment variable not set
   ```
   解决：`export MINIMAX_API_KEY='your_api_key'`

2. **TTS 片段文件不存在**
   ```
   Error: TTS segments file not found
   ```
   解决：先运行 `/build-segments`

3. **API 速率限制 (1002)**
   - 脚本会自动等待并重试
   - 如持续失败，增加等待时间

4. **API 连接失败**
   - 脚本会自动切换到备用 API
   - 检查网络连接

5. **文本过长 (>10,000 字符)**
   - 确保 TTS 片段长度合理
   - 检查 `/build-segments` 的配置

### 重试失败的片段

脚本支持断点续传，直接重新运行即可：

```bash
python3 .claude/skills/generate-tts-audio/generate_tts_minimax.py
```

已存在的文件会被跳过，只处理失败或未生成的片段。

## 成本估算

**MiniMax TTS 定价**（2026）：约 ¥0.015 / 1000 字符

**本项目估算**：
- 总字数: 11,861 字
- 预计成本: ≈ ¥0.18

## 性能优化

### 并行处理（可选）

如需加快生成速度，可以修改脚本使用多线程：

```python
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=5) as executor:
    futures = [executor.submit(process_segment, seg) for seg in segments]
```

### 调整速率限制

根据 API 配额调整等待时间（脚本第 272 行）：

```python
time.sleep(0.5)  # 可以调整此值
```

## 下一步

TTS 生成完成后，运行后处理：

```bash
claude-code /postprocess-audio
```

该步骤会：
- 添加静音填充（开头 200ms，结尾 300ms）
- 标准化响度到 -18 LUFS
- 转换为 MP3 格式（192kbps）
- 合并为章节音频文件

## 技术特性

✅ **双 API 容错** - 主 API 失败自动切换备用
✅ **断点续传** - 跳过已存在的文件
✅ **完整日志** - 详细记录生成状态
✅ **错误处理** - 超时重试、失败记录
✅ **情感支持** - 自动映射 23 种情感到 8 种 MiniMax 情感
✅ **Hex 解码** - 正确处理 MiniMax 的 hex 编码音频响应
✅ **速率控制** - 避免触发 API 限制

## 注意事项

1. **API Key 安全**: 不要将 API Key 提交到代码仓库
2. **音色测试**: 建议先用少量片段测试音色效果
3. **成本控制**: 注意 API 使用量，避免超出预算
4. **质量检查**: 生成后抽查音频质量
5. **备份**: 定期备份生成的音频文件
