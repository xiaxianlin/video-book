# 章节提取脚本

## 功能

从 Markdown 格式的小说源文件中提取章节结构，生成结构化的 JSON 数据。

## 使用方法

### 基本用法

从项目根目录执行：

```bash
python3 .claude/skills/extract-chapters/scripts/extract_chapters.py
```

默认会：
- 读取 `input/source.md`
- 输出到 `source/01_extracted/chapters.json`

### 自定义路径

```bash
python3 .claude/skills/extract-chapters/scripts/extract_chapters.py <源文件路径> <输出文件路径>
```

示例：
```bash
python3 .claude/skills/extract-chapters/scripts/extract_chapters.py my_novel.md output.json
```

## 输入格式要求

源文件应使用以下格式：

```markdown
# 小说标题

## 第 1 章：章节标题

章节内容...

## 第 2 章：章节标题

章节内容...
```

支持的章节标题格式：
- `## 第 1 章：标题` (中文冒号)
- `## 第 1 章:标题` (英文冒号)

## 输出格式

生成的 JSON 包含：

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

## 字段说明

- `total_chapters`: 章节总数
- `extraction_date`: 提取时间 (UTC)
- `source_file`: 源文件路径
- `novel_title`: 小说标题（从第一个一级标题提取）
- `chapters`: 章节数组
  - `chapter_id`: 章节唯一标识 (ch_001, ch_002, ...)
  - `chapter_number`: 章节序号
  - `title`: 章节标题
  - `content`: 章节完整文本内容
  - `word_count`: 字数统计（中文字符 + 英文单词）
  - `estimated_duration_minutes`: 预估朗读时长（按每分钟 150 字计算）

## 依赖

- Python 3.6+
- 标准库：json, re, sys, datetime, pathlib

无需安装额外依赖包。
