---
name: build-segments
description: Create TTS-ready audio segments with strict 75-second duration and single-speaker constraints. Use after scene splitting is complete or when the user requests to build TTS segments.
---

# 构建片段 Skill

## 目的
创建符合 TTS 要求的音频片段，严格遵守 75 秒时长和单一说话人约束。

## 输入
- `build/03_segmentation/scenes.json` - 场景结构
- `build/02_casting/voice_mapping.json` - 音色分配
- `config/default_config.json` - 片段配置

## 输出
- `build/03_segmentation/tts_segments.json` - TTS 就绪片段
- `build/03_segmentation/segment_manifest.json` - 片段元数据

## 执行指令

当此 skill 被调用时：

1. **读取配置**
   - 目标时长：75 秒（从配置读取）
   - 严格说话人分离：true
   - 情绪强度：low

2. **将场景处理为片段**
   对于每个场景：
   - 按相同说话人分组连续文本
   - 计算时长（字数 / 每秒 2.5 字）
   - 接近 75 秒限制时拆分
   - 绝不在一个片段中混合说话人

3. **创建 TTS 片段**
   为 OpenAI TTS API 构建结构：
   ```json
   {
     "segments": [
       {
         "segment_id": "seg_00001",
         "chapter_id": "ch_001",
         "scene_id": "ch_001_sc_001",
         "speaker_id": "narrator",
         "speaker_name": "旁白",
         "voice": "alloy",
         "text": "那是一个寒冷的冬天早晨。张三走在街上，心里想着今天的计划。",
         "word_count": 25,
         "estimated_duration_seconds": 10,
         "emotion": "neutral",
         "emotion_intensity": "low",
         "sequence_number": 1
       }
     ]
   }
   ```

4. **应用分段规则**
   - 每个片段最多 75 秒
   - 每个片段一个说话人（严格）
   - 尽可能在句子边界处断开
   - 保持叙事流畅性
   - 在片段之间添加自然停顿

5. **生成片段清单**
   创建制作清单：
   ```json
   {
     "total_segments": 150,
     "total_duration_seconds": 11250,
     "segments_by_chapter": {
       "ch_001": 15,
       "ch_002": 18
     },
     "segments_by_speaker": {
       "narrator": 80,
       "char_001": 40,
       "char_002": 30
     }
   }
   ```

6. **保存输出**
   - 将片段写入 `build/03_segmentation/tts_segments.json`
   - 将清单写入 `build/03_segmentation/segment_manifest.json`
   - 确保使用正确的 UTF-8 编码

7. **报告结果**
   - 创建的片段总数
   - 平均片段时长
   - 说话人分布
   - 需要审查的片段

## 验证
- 所有片段 ≤ 75 秒
- 每个片段恰好有一个说话人
- 所有片段都有音色分配
- 片段顺序正确
- 原始内容没有遗漏文本
