---
name: attribute-dialogue
description: Analyze chapter content and attribute each line of dialogue to the correct character or narrator. Use after voice casting is complete, when the user requests dialogue attribution, or as part of the audiobook production pipeline.
---

# 对白归属 Skill

## 目的
分析章节内容，将每一行对话归属到正确的角色或旁白。

## 输入
- `source/01_extracted/chapters.json` - 章节内容
- `source/02_casting/character_list.json` - 角色定义
- `source/02_casting/voice_mapping.json` - 音色分配

## 输出
- `source/03_segmentation/attributed_chapters.json` - 带有对话归属的章节

## 执行指令

当此 skill 被调用时，**由 Claude 直接阅读章节内容并手动归属对话**，而不是运行自动化脚本。

1. **加载数据**
   - 读取 `source/01_extracted/chapters.json` 获取章节内容
   - 读取 `source/02_casting/character_list.json` 了解角色信息
   - 读取 `source/02_casting/voice_mapping.json` 获取角色到音色的映射

2. **逐章分析**
   对于每个章节：
   - 仔细阅读章节内容，理解情节发展
   - 识别对话和旁白的边界
   - 根据上下文判断每段对话的说话者
   - 注意对话标记（引号、冒号等）和归属提示（"XX说"、"XX道"等）

3. **归属对话**
   对于每一段文本：
   - **旁白**：叙述性文字，没有引号，描述场景、动作、心理活动
   - **对话**：有引号或明确的说话标记，归属到具体角色
   - 使用上下文线索判断说话者（前后对话、场景、角色关系）
   - 对于连续对话，根据对话内容和语气判断是否换人

4. **构建归属内容结构**
   手动创建详细的归属数据：
   ```json
   {
     "total_chapters": 10,
     "attribution_date": "2026-01-26T16:00:00Z",
     "chapters": [
       {
         "chapter_id": "ch_001",
         "chapter_number": 1,
         "title": "章节标题",
         "segments": [
           {
             "segment_id": "ch_001_seg_001",
             "type": "narration",
             "speaker_id": "narrator",
             "text": "那是一个寒冷的冬天早晨。",
             "word_count": 10
           },
           {
             "segment_id": "ch_001_seg_002",
             "type": "dialogue",
             "speaker_id": "char_001",
             "speaker_name": "张三",
             "text": "今天天气真冷啊。",
             "word_count": 7,
             "emotion": "neutral"
           }
         ]
       }
     ]
   }
   ```

5. **情绪标注**
   - 根据对话内容和上下文判断情绪
   - 可用情绪标签：neutral, happy, sad, angry, surprised, fearful
   - 保持情绪强度为 "low"（克制风格）
   - 不确定时使用 "neutral"

6. **保存输出**
   - 写入到 `source/03_segmentation/attributed_chapters.json`
   - 确保所有对话都有明确的说话者
   - 保持段落的自然边界

7. **报告结果**
   输出清晰的总结：
   - 处理的章节总数
   - 创建的片段总数
   - 对话与旁白的比例
   - 每个角色的对话数量统计

## 验证
- 所有对话都有说话者归属
- 说话者 ID 与角色列表匹配
- 没有孤立的对话
- 情绪标签有效
