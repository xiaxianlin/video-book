---
name: generate-tts-audio
description: Generate audio files from text segments using OpenAI TTS API with retry logic and error handling. Use after TTS segments are built or when the user requests to generate audio from text segments.
---

# 生成 TTS 音频 Skill

## 目的
使用 OpenAI TTS API 从文本片段生成音频文件，包含重试逻辑和错误处理。

## 输入
- `build/03_segmentation/tts_segments.json` - TTS 就绪片段
- `config/default_config.json` - TTS 配置
- 环境变量：`OPENAI_API_KEY`

## 输出
- `build/04_tts_raw/*.wav` - 原始 TTS 音频文件
- `build/04_tts_raw/generation_log.json` - 生成日志
- `build/04_tts_raw/failed_segments.json` - 失败片段列表

## 执行指令

当此 skill 被调用时：

1. **验证前置条件**
   - 检查 `OPENAI_API_KEY` 环境变量
   - 验证 `build/03_segmentation/tts_segments.json` 存在
   - 如需要则创建输出目录

2. **加载配置**
   - API 端点：`/v1/audio/speech`
   - 模型：`gpt-4o-mini-tts`
   - 输出格式：`wav`
   - 重试次数：3
   - 重试延迟：2 秒

3. **处理片段**
   对于 tts_segments.json 中的每个片段：

   a. **准备 API 请求**
   ```bash
   curl https://api.openai.com/v1/audio/speech \
     -H "Authorization: Bearer $OPENAI_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{
       "model": "gpt-4o-mini-tts",
       "input": "<segment_text>",
       "voice": "<voice_name>",
       "response_format": "wav"
     }' \
     --output "build/04_tts_raw/seg_<segment_id>.wav"
   ```

   b. **处理响应**
   - 成功：保存 WAV 文件，记录成功
   - 失败：使用指数退避重试
   - 3 次失败后：添加到 failed_segments.json

4. **实现幂等性**
   - 检查输出文件是否已存在
   - 如果文件存在且有效则跳过生成
   - 允许使用 `--force` 标志强制重新生成

5. **跟踪进度**
   - 记录每个片段的生成
   - 更新进度计数器
   - 估算剩余时间
   - 持续保存生成日志

6. **生成日志**
   创建 generation_log.json：
   ```json
   {
     "generation_date": "2026-01-26T14:00:00Z",
     "total_segments": 150,
     "successful": 148,
     "failed": 2,
     "total_duration_seconds": 11250,
     "segments": [
       {
         "segment_id": "seg_00001",
         "status": "success",
         "file_path": "build/04_tts_raw/seg_00001.wav",
         "duration_seconds": 10.5,
         "generation_time_ms": 1250
       }
     ]
   }
   ```

7. **处理失败**
   创建 failed_segments.json：
   ```json
   {
     "failed_segments": [
       {
         "segment_id": "seg_00042",
         "error": "API rate limit exceeded",
         "retry_count": 3,
         "last_attempt": "2026-01-26T14:15:00Z"
       }
     ]
   }
   ```

8. **报告结果**
   - 处理的片段总数
   - 成功率
   - 生成的音频总时长
   - 失败的片段（如有）
   - 估算的 API 成本

## 验证
- 所有成功的片段都有有效的 WAV 文件
- 文件大小合理（不为 0 字节）
- 音频时长与预期时长匹配
- 失败的片段已记录以供重试

## 错误处理
- 速率限制：等待后重试
- 网络错误：使用退避重试
- 无效的 API 密钥：停止并报告
- 格式错误的响应：记录并跳过
