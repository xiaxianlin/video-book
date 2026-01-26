---
name: extract-chapters
description: Extract chapter structure from Markdown novel source files and save as structured chapter data. Use when starting the audiobook production pipeline or when the user requests to extract chapters from input/source.md.
---

# 章节提取 Skill

## 目的
从 Markdown 小说源文件中提取章节结构，并保存为结构化的章节数据。

## 输入
- `input/source.md` - Markdown 格式的小说文件

## 输出
- `source/01_extracted/chapters.json` - 结构化的章节数据

## 执行指令

当此 skill 被调用时，执行以下步骤：

### 1. 运行提取脚本

使用 skill 目录下的 `scripts/extract_chapters.py` 脚本：

```bash
python3 .claude/skills/extract-chapters/scripts/extract_chapters.py
```

脚本会自动：
- 读取 `input/source.md`
- 识别章节边界（匹配 `## 第X章：标题` 格式）
- 提取章节元数据（编号、标题、内容、字数、预估时长）
- 生成结构化 JSON 输出到 `source/01_extracted/chapters.json`

### 2. 输出格式

脚本生成的 JSON 格式：
```json
{
  "total_chapters": 10,
  "extraction_date": "2026-01-26T14:00:00Z",
  "source_file": "input/source.md",
  "novel_title": "小说标题",
  "chapters": [
    {
      "chapter_id": "ch_001",
      "chapter_number": 1,
      "title": "章节标题",
      "content": "完整章节文本...",
      "word_count": 2500,
      "estimated_duration_minutes": 16.7
    }
  ]
}
```

### 3. 报告结果

脚本执行后会输出：
- 提取的章节总数
- 总字数
- 预估总时长
- 输出文件路径

### 4. 自定义路径（可选）

如需使用自定义路径：
```bash
python3 .claude/skills/extract-chapters/scripts/extract_chapters.py <源文件> <输出文件>
```

## 验证
- 确保所有章节都有唯一的 ID
- 验证没有空章节
- 检查章节编号是否连续
