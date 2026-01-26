# CLAUDE.md

本文件为 Claude Code (claude.ai/code) 在此代码仓库中工作时提供指导。

## 项目概述

这是一个自动化有声书制作流水线，使用 Claude Code Skills 将 Markdown 小说转换为专业的多角色有声书。系统使用 OpenAI TTS 进行语音生成，使用 ffmpeg 进行音频处理。

## 核心命令

### 运行完整流水线

```bash
# 顺序执行（首次运行推荐）
claude-code /extract-chapters
claude-code /prepare-casting
claude-code /attribute-dialogue
claude-code /split-scenes
claude-code /build-segments
claude-code /generate-tts-audio
claude-code /postprocess-audio
claude-code /package-release

# 单行执行
claude-code /extract-chapters && claude-code /prepare-casting && claude-code /attribute-dialogue && claude-code /split-scenes && claude-code /build-segments && claude-code /generate-tts-audio && claude-code /postprocess-audio && claude-code /package-release
```

### 部分重跑

```bash
# 从 TTS 步骤重新生成（例如，更改音色分配后）
claude-code /generate-tts-audio && claude-code /postprocess-audio && claude-code /package-release

# 仅重新处理音频（例如，调整响度设置后）
claude-code /postprocess-audio && claude-code /package-release
```

### 验证命令

```bash
# 检查章节提取
cat source/01_extracted/chapters.json | jq '.total_chapters'

# 查看音色分配
cat source/02_casting/voice_mapping.json | jq '.voice_assignments'

# 检查 TTS 生成状态
cat source/04_tts_raw/generation_log.json | jq '.successful, .failed'

# 验证音频质量
cat source/05_post/processing_log.json | jq '.processing_stats.average_loudness_lufs'

# 测试播放章节
ffplay source/05_post/chapters/ch_001.mp3
```

## 架构

### 流水线流程

系统遵循 8 阶段流水线，每个阶段产生的产物供下一阶段使用：

1. **extract-chapters**：解析 `input/source.md` → `source/01_extracted/chapters.json`
2. **prepare-casting**：识别角色并分配音色 → `source/02_casting/voice_mapping.json`
3. **attribute-dialogue**：将每行归属到说话者 → `source/03_segmentation/attributed_chapters.json`
4. **split-scenes**：将章节划分为逻辑场景 → `source/03_segmentation/scenes.json`
5. **build-segments**：创建 75 秒的 TTS 片段，严格分离说话人 → `source/03_segmentation/tts_segments.json`
6. **generate-tts-audio**：调用 OpenAI TTS API → `source/04_tts_raw/*.wav`
7. **postprocess-audio**：应用响度标准化并创建章节 MP3 → `source/05_post/chapters/*.mp3`
8. **package-release**：组装最终交付物 → `release/`

### 目录结构

```
audiobook_project/
├── input/              # 源小说 (source.md)
├── configs/            # 配置文件
│   ├── default_config.json
│   └── voices.json
├── source/             # 中间产物（按流水线步骤分阶段）
│   ├── 01_extracted/
│   ├── 02_casting/
│   ├── 03_segmentation/
│   ├── 04_tts_raw/
│   └── 05_post/
├── release/            # 最终交付物
│   ├── audio/chapters/
│   ├── meta.json
│   └── chapters.json
└── .claude/skills/     # 流水线 skill 定义
```

### 关键设计原则

**幂等性**：每个 skill 检查现有输出，除非强制，否则跳过重新生成。这使得安全重跑和部分流水线执行成为可能。

**严格说话人分离**：每个 TTS 片段只包含一个说话人。此约束简化了音色一致性，并支持按角色进行音频处理。

**75 秒片段目标**：TTS 片段目标为 75 秒，以平衡 API 效率和精细控制。片段在自然边界（句子/段落）处拆分。

**可审计的产物**：每个阶段都生成带有元数据的 JSON 清单，支持在任何时点进行调试和手动修正。

## 音频规格

- **格式**：MP3, 192kbps, Mono
- **响度**：-18 LUFS（播客标准）
- **真峰值**：-1.0 dBTP
- **静音**：每片段开头 200ms，结尾 300ms
- **TTS 提供商**：OpenAI gpt-4o-mini-tts
- **可用音色**：alloy, echo, fable, onyx, nova, shimmer

## 配置

### 主配置：`configs/default_config.json`

关键设置：
- `segment.target_duration_seconds`: 75（TTS 片段长度）
- `segment.strict_speaker_separation`: true
- `segment.emotion_intensity`: "low"（克制风格）
- `audio_processing.target_lufs`: -18
- `tts.model`: "gpt-4o-mini-tts"

### 音色映射：`source/02_casting/voice_mapping.json`

由 `/prepare-casting` 生成，将角色映射到 OpenAI 音色。可在运行 `/generate-tts-audio` 之前手动编辑。

## 前置条件

```bash
# 必需的环境变量
export OPENAI_API_KEY=your_api_key_here

# 必需的工具
# - Claude Code CLI
# - ffmpeg（用于音频处理）
# - jq（用于 JSON 验证，可选）
```

## 故障排查

### API 速率限制
```bash
# 检查失败的片段
cat source/04_tts_raw/failed_segments.json

# 等待后重试
sleep 60
claude-code /generate-tts-audio --retry-failed
```

### 角色归属错误
```bash
# 查看归属的章节
cat source/03_segmentation/attributed_chapters.json | jq '.chapters[0].segments[0:5]'

# 手动修复 JSON，然后从 build-segments 继续
vim source/03_segmentation/attributed_chapters.json
claude-code /build-segments && claude-code /generate-tts-audio && claude-code /postprocess-audio && claude-code /package-release
```

### 音频质量问题
```bash
# 检查处理统计
cat source/05_post/processing_log.json | jq '.processing_stats'

# 调整配置并重新处理
vim configs/default_config.json
claude-code /postprocess-audio --force
```

## 成本估算

OpenAI TTS 定价（2026）：约 $0.015 / 1000 字符

示例：25,000 字小说 ≈ 150,000 字符 ≈ $2.25

## 可扩展性

流水线设计便于扩展：
- 通过修改 `/generate-tts-audio` skill 替换 TTS 提供商
- 在 `/build-segments` 中添加 SSML 支持以控制韵律
- 在 `/attribute-dialogue` 中实现句子级情绪检测
- 在 `/package-release` 中生成带章节标记的 M4B 格式
