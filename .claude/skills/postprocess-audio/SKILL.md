---
name: postprocess-audio
description: Apply professional audio processing to raw TTS files including silence padding, loudness normalization, and MP3 encoding. Use after TTS audio generation is complete or when the user requests audio post-processing.
---

# 音频后处理 Skill

## 目的
对原始 TTS 文件应用专业音频处理：添加静音、标准化响度、编码为 MP3。

## 输入
- `build/04_tts_raw/*.wav` - 原始 TTS 音频文件
- `build/03_segmentation/tts_segments.json` - 片段元数据
- `config/default_config.json` - 音频处理标准

## 输出
- `build/05_post/segments/*.mp3` - 处理后的片段 MP3
- `build/05_post/chapters/*.mp3` - 章节级 MP3
- `build/05_post/processing_log.json` - 处理日志

## 前置条件
- 已安装 ffmpeg 并在 PATH 中可用
- ffmpeg 支持 loudnorm 滤镜

## 执行指令

当此 skill 被调用时：

1. **验证前置条件**
   ```bash
   ffmpeg -version
   ```
   确保 ffmpeg 已安装并支持 loudnorm 滤镜

2. **加载处理标准**
   从配置读取：
   - 段首静音：200ms
   - 段尾静音：300ms
   - 目标 LUFS：-18
   - 真峰值：-1.0 dBTP
   - MP3 比特率：192kbps
   - MP3 声道：mono

3. **处理每个片段**
   对于 `build/04_tts_raw/` 中的每个 WAV 文件：

   a. **添加静音填充**
   ```bash
   ffmpeg -i input.wav \
     -af "adelay=200|200,apad=pad_dur=300ms" \
     temp_padded.wav
   ```

   b. **标准化响度**
   ```bash
   ffmpeg -i temp_padded.wav \
     -af "loudnorm=I=-18:TP=-1.0:LRA=11" \
     temp_normalized.wav
   ```

   c. **编码为 MP3**
   ```bash
   ffmpeg -i temp_normalized.wav \
     -codec:a libmp3lame \
     -b:a 192k \
     -ac 1 \
     build/05_post/segments/seg_<id>.mp3
   ```

4. **合并片段为章节**
   对于每个章节：

   a. **创建文件列表**
   ```
   file 'seg_00001.mp3'
   file 'seg_00002.mp3'
   file 'seg_00003.mp3'
   ```

   b. **连接片段**
   ```bash
   ffmpeg -f concat -safe 0 -i filelist.txt \
     -c copy \
     build/05_post/chapters/ch_001.mp3
   ```

5. **验证音频质量**
   对于每个输出文件：
   - 检查文件大小 > 0
   - 验证音频时长
   - 检查响度级别
   - 验证 MP3 编码

6. **生成处理日志**
   ```json
   {
     "processing_date": "2026-01-26T14:00:00Z",
     "segments_processed": 150,
     "chapters_created": 10,
     "processing_stats": {
       "total_input_duration_seconds": 11250,
       "total_output_duration_seconds": 11325,
       "average_loudness_lufs": -18.2,
       "peak_true_peak_dbtp": -1.1
     },
     "files": [
       {
         "segment_id": "seg_00001",
         "input_file": "build/04_tts_raw/seg_00001.wav",
         "output_file": "build/05_post/segments/seg_00001.mp3",
         "duration_seconds": 10.5,
         "loudness_lufs": -18.1,
         "file_size_mb": 0.25
       }
     ]
   }
   ```

7. **报告结果**
   - 处理的片段总数
   - 创建的章节总数
   - 达到的平均响度
   - 总输出大小
   - 任何处理错误

## 验证
- 所有 MP3 文件有效
- 响度在目标 ±1 LUFS 范围内
- 真峰值低于阈值
- 章节文件包含所有片段
- 没有音频削波或失真

## 错误处理
- 缺少输入文件：记录并跳过
- ffmpeg 错误：重试一次，然后记录
- 无效音频：标记以供人工审查
- 磁盘空间问题：停止并报告
