---
name: package-release
description: Assemble all processed audio files and metadata into final release structure ready for distribution. Use after audio post-processing is complete or when the user requests to package the final audiobook release.
---

# 打包发布 Skill

## 目的
将所有处理后的音频文件和元数据打包为最终发布结构，准备分发。

## 输入
- `build/05_post/chapters/*.mp3` - 章节音频文件
- `build/01_extracted/chapters.json` - 章节元数据
- `build/02_casting/voice_mapping.json` - 音色分配
- `build/03_segmentation/segment_manifest.json` - 片段统计
- `build/05_post/processing_log.json` - 处理统计

## 输出
- `release/audio/chapters/*.mp3` - 最终章节音频文件
- `release/audio/full_book.mp3` - 可选的全书音频（如果请求）
- `release/meta.json` - 完整项目元数据
- `release/chapters.json` - 章节信息
- `release/README.md` - 发布文档

## 执行指令

当此 skill 被调用时：

1. **复制章节音频文件**
   ```bash
   cp build/05_post/chapters/*.mp3 release/audio/chapters/
   ```

2. **生成全书音频（可选）**
   如果请求，连接所有章节：
   ```bash
   # 创建文件列表
   ls release/audio/chapters/*.mp3 | sort > filelist.txt

   # 连接
   ffmpeg -f concat -safe 0 -i filelist.txt \
     -c copy \
     release/audio/full_book.mp3
   ```

3. **创建 meta.json**
   编译综合元数据：
   ```json
   {
     "project": {
       "name": "audiobook_project",
       "version": "1.0.0",
       "generation_date": "2026-01-26T14:00:00Z",
       "pipeline_version": "v1.0"
     },
     "source": {
       "input_file": "input/source.md",
       "total_chapters": 10,
       "total_word_count": 25000
     },
     "audio": {
       "total_duration_seconds": 11325,
       "total_duration_formatted": "3h 8m 45s",
       "format": "MP3",
       "bitrate": "192kbps",
       "channels": "mono",
       "sample_rate": "44100Hz"
     },
     "production": {
       "tts_provider": "openai",
       "tts_model": "gpt-4o-mini-tts",
       "total_segments": 150,
       "target_loudness_lufs": -18,
       "characters_count": 5
     },
     "characters": [
       {
         "character_id": "char_001",
         "name": "张三",
         "voice": "onyx",
         "total_lines": 150
       }
     ]
   }
   ```

4. **创建 chapters.json**
   播放器的章节级信息：
   ```json
   {
     "chapters": [
       {
         "chapter_number": 1,
         "title": "第一章标题",
         "audio_file": "audio/chapters/ch_001.mp3",
         "duration_seconds": 1125,
         "duration_formatted": "18m 45s",
         "word_count": 2500,
         "file_size_mb": 2.8
       }
     ]
   }
   ```

5. **生成 README.md**
   创建发布文档：
   ```markdown
   # 有声书发布

   ## 项目信息
   - **标题**：[小说标题]
   - **生成日期**：2026-01-26
   - **总时长**：3h 8m 45s
   - **格式**：MP3, 192kbps, Mono

   ## 内容
   - 10 个章节
   - 多角色旁白
   - 专业音频处理

   ## 音频文件
   - `audio/chapters/` - 单独的章节文件
   - `audio/full_book.mp3` - 完整有声书（可选）

   ## 技术规格
   - TTS 提供商：OpenAI gpt-4o-mini-tts
   - 响度：-18 LUFS
   - 真峰值：-1.0 dBTP
   - 片段时长：~75 秒

   ## 角色与音色
   [角色和分配音色列表]

   ## 使用方法
   按顺序播放章节文件，或使用 full_book.mp3 连续播放。
   ```

6. **验证发布包**
   - 所有章节 MP3 存在
   - 元数据文件为有效 JSON
   - 文件大小合理
   - 音频文件可播放
   - README 完整

7. **生成发布清单**
   ```json
   {
     "release_date": "2026-01-26T14:00:00Z",
     "files": [
       {
         "path": "audio/chapters/ch_001.mp3",
         "size_bytes": 2936832,
         "md5": "abc123...",
         "duration_seconds": 1125
       }
     ],
     "total_size_mb": 28.5,
     "checksum": "sha256:def456..."
   }
   ```

8. **报告结果**
   - 发布中的文件总数
   - 总包大小
   - 发布目录结构
   - 验证状态
   - 分发就绪状态

## 验证
- 所有预期文件存在
- JSON 文件有效且完整
- 音频文件可播放
- 元数据准确
- README 信息丰富

## 可选增强
- 生成封面艺术占位符
- 创建 M4B 有声书格式
- 添加章节标记
- 生成播客分发的 RSS feed
- 创建分发存档（ZIP/TAR）
