# Markdown 小说 → 多角色有声书生产流水线

基于 Claude Code Skills 的专业有声书自动化生产系统。

## 项目概述

将 Markdown 格式小说转换为专业级多角色有声书，支持：
- ✅ 多角色配音（OpenAI TTS）
- ✅ 智能对白归属
- ✅ 专业音频处理（-18 LUFS 标准）
- ✅ 可重跑、可审计的工作流
- ✅ 章节级与全书级输出

## 快速开始

### 1. 准备环境

```bash
# 安装依赖
# - Claude Code CLI
# - ffmpeg (音频处理)

# 设置 OpenAI API Key
export OPENAI_API_KEY=your_api_key_here
```

### 2. 准备输入

将小说 Markdown 文件放置到：
```
input/source.md
```

### 3. 运行完整流水线

```bash
# 方式一：逐步执行（推荐首次使用）
claude-code /extract-chapters
claude-code /prepare-casting
claude-code /attribute-dialogue
claude-code /split-scenes
claude-code /build-segments
claude-code /generate-tts-audio
claude-code /postprocess-audio
claude-code /package-release

# 方式二：一键执行
claude-code /extract-chapters && \
claude-code /prepare-casting && \
claude-code /attribute-dialogue && \
claude-code /split-scenes && \
claude-code /build-segments && \
claude-code /generate-tts-audio && \
claude-code /postprocess-audio && \
claude-code /package-release
```

### 4. 获取成品

最终输出位于：
```
release/
├── audio/
│   ├── chapters/      # 章节 MP3
│   └── full_book.mp3  # 全书合集（可选）
├── meta.json          # 项目元数据
├── chapters.json      # 章节信息
└── README.md          # 发布说明
```

## 工作流步骤

| 步骤 | Skill | 输入 | 输出 | 说明 |
|------|-------|------|------|------|
| 1 | `/extract-chapters` | `input/source.md` | `build/01_extracted/chapters.json` | 提取章节结构 |
| 2 | `/prepare-casting` | 章节内容 | `build/02_casting/voice_mapping.json` | 角色与音色映射 |
| 3 | `/attribute-dialogue` | 章节+角色 | `build/03_segmentation/attributed_chapters.json` | 对白归属 |
| 4 | `/split-scenes` | 归属内容 | `build/03_segmentation/scenes.json` | 场景拆分 |
| 5 | `/build-segments` | 场景 | `build/03_segmentation/tts_segments.json` | 构建 75 秒 TTS 片段 |
| 6 | `/generate-tts-audio` | TTS 片段 | `build/04_tts_raw/*.wav` | 生成原始音频 |
| 7 | `/postprocess-audio` | 原始音频 | `build/05_post/chapters/*.mp3` | 音频后处理 |
| 8 | `/package-release` | 处理后音频 | `release/` | 打包发布 |

## 技术规格

### 音频标准
- **格式**: MP3, 192kbps, Mono
- **响度**: -18 LUFS
- **真峰值**: -1.0 dBTP
- **静音**: 段首 200ms, 段尾 300ms

### TTS 配置
- **提供商**: OpenAI
- **模型**: gpt-4o-mini-tts
- **可用音色**: alloy, echo, fable, onyx, nova, shimmer
- **片段时长**: 目标 75 秒
- **说话人分离**: 严格（一个片段一个说话人）

### 情绪控制
- **强度**: Low（克制风格）
- **标签**: neutral, happy, sad, angry, surprised, fearful

## 项目结构

```
audiobook_project/
├── input/              # 输入文件
├── config/             # 配置文件
├── build/              # 构建中间产物
│   ├── 01_extracted/
│   ├── 02_casting/
│   ├── 03_segmentation/
│   ├── 04_tts_raw/
│   └── 05_post/
├── release/            # 最终发布
├── skills/             # Claude Code Skills 定义
└── WORKFLOW.md         # 详细工作流文档
```

## Skills 说明

所有 skills 位于 `skills/` 目录：

1. **extract-chapters.md** - 章节提取
2. **prepare-casting.md** - 角色配音准备
3. **attribute-dialogue.md** - 对白归属
4. **split-scenes.md** - 场景拆分
5. **build-segments.md** - 片段构建
6. **generate-tts-audio.md** - TTS 音频生成
7. **postprocess-audio.md** - 音频后处理
8. **package-release.md** - 发布打包

每个 skill 都是独立可执行的，支持单独重跑。

## 部分重跑

支持从任意步骤重新开始：

```bash
# 仅重新生成 TTS 音频（例如更换音色后）
claude-code /generate-tts-audio && \
claude-code /postprocess-audio && \
claude-code /package-release

# 仅重新处理音频（例如调整响度标准后）
claude-code /postprocess-audio && \
claude-code /package-release
```

## 成本估算

基于 OpenAI TTS 定价（2026）：
- **费率**: ~$0.015 / 1000 字符
- **示例**: 25,000 字小说 ≈ 150,000 字符 ≈ $2.25

## 故障排查

详见 `WORKFLOW.md` 中的 Troubleshooting 章节。

常见问题：
- API 限流 → 等待后重试
- 音频质量问题 → 调整 config 后重新处理
- 角色归属错误 → 手动修正 JSON 后继续

## 扩展性

本系统支持：
- ✅ 替换 TTS Provider（ElevenLabs, Azure, etc.）
- ✅ 升级到 SSML 标记
- ✅ 句级情绪检测
- ✅ 接入平台上传 API
- ✅ 生成 M4B 格式
- ✅ 添加章节标记

## 文档

- **WORKFLOW.md** - 完整工作流文档
- **tech_plan.md** - 技术方案
- **config/default_config.json** - 配置模板

## 许可

本项目为个人作者与内容创作者提供的自动化工具。

---

**版本**: v1.0
**更新日期**: 2026-01-26
