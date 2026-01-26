---
name: split-scenes
description: Split attributed chapters into logical scenes for better audio production management. Use after dialogue attribution is complete or when the user requests scene segmentation.
---

# 场景拆分 Skill

## 目的
将归属后的章节拆分为逻辑场景，以便更好地管理音频制作。

## 输入
- `source/03_segmentation/attributed_chapters.json` - 归属后的对话和旁白

## 输出
- `source/03_segmentation/scenes.json` - 场景级结构

## 执行指令

当此 skill 被调用时：

1. **分析章节结构**
   - 读取归属后的章节
   - 识别场景边界：
     - 地点变化
     - 时间跳跃
     - 角色组变化
     - 带有上下文转换的段落分隔

2. **创建场景边界**
   将章节拆分为带有元数据的场景：
   ```json
   {
     "chapter_id": "ch_001",
     "scenes": [
       {
         "scene_id": "ch_001_sc_001",
         "scene_number": 1,
         "location": "张三的家",
         "time_of_day": "早晨",
         "characters_present": ["char_001", "char_002"],
         "segments": [
           {
             "segment_id": "ch_001_seg_001",
             "type": "narration",
             "speaker_id": "narrator",
             "text": "那是一个寒冷的冬天早晨。",
             "word_count": 10
           }
         ],
         "total_word_count": 450,
         "estimated_duration_seconds": 180
       }
     ]
   }
   ```

3. **优化场景长度**
   - 目标场景长度：3-5 分钟（450-750 字）
   - 避免短于 2 分钟的场景
   - 在自然断点处拆分过长的场景
   - 保持叙事连贯性

4. **添加场景元数据**
   - 场景地点/场景设置
   - 时间段
   - 在场角色
   - 情绪/氛围
   - 转场类型（切换、淡入淡出、连续）

5. **保存输出**
   - 写入到 `source/03_segmentation/scenes.json`
   - 包含场景统计信息
   - 保留所有片段归属

6. **报告结果**
   - 每章创建的场景总数
   - 平均场景时长
   - 场景长度分布
   - 需要人工审查的场景

## 验证
- 所有片段都分配到场景
- 场景边界合理
- 没有孤立的片段
- 场景时长合理
