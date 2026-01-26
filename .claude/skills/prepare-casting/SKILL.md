---
name: prepare-casting
description: Manually identify characters and assign voices by reading chapter content. Claude reads the story, understands character personalities, and assigns appropriate voices from configs/voices.json. Use after chapter extraction when voice casting is needed.
---

# 角色配音准备 Skill

## 目的
为多角色有声书制作创建角色到音色的映射配置。

## 输入
- `source/01_extracted/chapters.json` - 提取的章节数据
- `configs/voices.json` - 可用音色列表
- `configs/default_config.json` - 项目配置（可选）

## 输出
- `source/02_casting/character_list.json` - 所有识别出的角色
- `source/02_casting/voice_mapping.json` - 角色到音色的分配

## 执行指令

当此 skill 被调用时，**由 Claude 直接阅读章节内容并手动决策**，而不是运行自动化脚本。

### 1. 阅读章节内容

读取 `source/01_extracted/chapters.json`，仔细阅读前几章的内容，理解故事情节和角色关系。

### 2. 识别主要角色

基于对故事的理解，识别出：
- **主角**：故事的核心人物，贯穿全文
- **配角**：重要的支持角色，多次出现
- **次要角色**：偶尔出现的角色

对每个角色记录：
- 姓名
- 性别
- 年龄段（青年/中年/老年）
- 性格特征
- 在故事中的作用

### 3. 加载可用音色

读取 `configs/voices.json`，了解所有可用的音色选项。

音色分类：
- **男性音色**：青涩青年、精英青年、霸道青年、大学生、沉稳高管、温润男声等
- **女性音色**：少女、御姐、成熟女性、甜美女性、新闻女声等
- **特殊音色**：儿童、老年人、播音员等

优先使用：
- 主角使用 **beta 版本**（高质量音色，如 `male-qn-badao-jingpin`）
- 旁白使用专业播音员音色
- 跳过粤语和英语音色（仅使用普通话）

### 4. 分配音色

根据角色特征手动分配音色：

**分配原则**：
- 主角优先使用高质量 beta 版本音色
- 根据角色性格选择合适的音色（如霸道角色用"霸道青年"，职业女性用"成熟女性"）
- 确保主要角色使用不同的音色，避免混淆
- 旁白使用中性、专业的播音员音色
- 为每个分配添加 `reason` 字段，说明选择该音色的理由

**示例分配**：
```json
{
  "character_id": "char_001",
  "character_name": "周启明",
  "voice_id": "male-qn-badao-jingpin",
  "voice_name": "霸道青年音色-beta",
  "role": "protagonist",
  "reason": "男主角，青年男性，性格自信霸道"
}
```

### 5. 创建输出文件

手动创建两个 JSON 文件：

**角色列表** (`source/02_casting/character_list.json`):
```json
{
  "total_characters": 7,
  "classification": {
    "protagonist": ["角色1", "角色2"],
    "supporting": ["角色3", "角色4"],
    "minor": ["角色5", "角色6"]
  },
  "characters": [
    {
      "name": "角色名",
      "role": "protagonist/supporting/minor",
      "gender": "male/female",
      "age_group": "青年/中年/老年",
      "personality": "性格描述",
      "estimated_appearances": "高频/中频/低频"
    }
  ]
}
```

**音色映射** (`source/02_casting/voice_mapping.json`):
```json
{
  "total_assignments": 8,
  "voice_assignments": [
    {
      "character_id": "narrator",
      "character_name": "旁白",
      "voice_id": "音色ID",
      "voice_name": "音色名称",
      "role": "narrator",
      "reason": "选择理由"
    },
    {
      "character_id": "char_001",
      "character_name": "角色名",
      "voice_id": "音色ID",
      "voice_name": "音色名称",
      "role": "protagonist/supporting/minor",
      "reason": "选择理由"
    }
  ]
}
```

### 6. 报告结果

输出清晰的总结：
- 识别出的角色总数
- 主角、配角、次要角色的数量
- 每个主要角色的音色分配
- 音色分配的理由

## 验证
- 确保所有角色都有音色分配
- 主要角色不使用重复的音色
- 旁白音色与角色音色有明显区别
