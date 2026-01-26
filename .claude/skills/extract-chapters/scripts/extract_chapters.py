#!/usr/bin/env python3
"""
章节提取脚本
从 Markdown 小说源文件中提取章节结构，并保存为结构化的章节数据。
"""

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


def extract_chapters(source_file: str, output_file: str) -> dict:
    """
    从源文件提取章节信息

    Args:
        source_file: 源 Markdown 文件路径
        output_file: 输出 JSON 文件路径

    Returns:
        提取结果的统计信息
    """
    # 读取源文件
    source_path = Path(source_file)
    if not source_path.exists():
        raise FileNotFoundError(f"源文件不存在: {source_file}")

    with open(source_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 提取小说标题（第一个一级标题）
    title_match = re.search(r'^# (.+)$', content, re.MULTILINE)
    novel_title = title_match.group(1).strip() if title_match else "未命名小说"

    # 分割章节 - 匹配章节标题（只匹配同一行的标题）
    chapter_pattern = r'## 第 (\d+) 章[:：]([^\n]*)\n(.*?)(?=\n## 第 \d+ 章|$)'
    matches = list(re.finditer(chapter_pattern, content, re.DOTALL))

    chapters = []
    for match in matches:
        chapter_num = int(match.group(1))
        title = match.group(2).strip()
        content_text = match.group(3).strip()

        # 统计字数（中文字符 + 英文单词）
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', content_text))
        english_words = len(re.findall(r'[a-zA-Z]+', content_text))
        word_count = chinese_chars + english_words

        # 估算时长（每分钟 150 字）
        estimated_duration = round(word_count / 150, 1)

        chapters.append({
            "chapter_id": f"ch_{chapter_num:03d}",
            "chapter_number": chapter_num,
            "title": title,
            "content": content_text,
            "word_count": word_count,
            "estimated_duration_minutes": estimated_duration
        })

    # 构建输出数据
    output_data = {
        "total_chapters": len(chapters),
        "extraction_date": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_file": str(source_path),
        "novel_title": novel_title,
        "chapters": chapters
    }

    # 确保输出目录存在
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # 写入输出文件
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    # 返回统计信息
    total_words = sum(ch['word_count'] for ch in chapters)
    total_duration = sum(ch['estimated_duration_minutes'] for ch in chapters)

    return {
        "total_chapters": len(chapters),
        "total_words": total_words,
        "total_duration_minutes": round(total_duration, 1),
        "output_file": str(output_path)
    }


def main():
    """主函数"""
    # 默认路径 - 从脚本位置计算项目根目录
    # 脚本路径: .claude/skills/extract-chapters/scripts/extract_chapters.py
    # 需要向上 4 级到达项目根目录
    script_path = Path(__file__).resolve()  # 解析为绝对路径
    # scripts -> extract-chapters -> skills -> .claude -> project_root
    project_root = script_path.parent.parent.parent.parent.parent
    source_file = project_root / "input" / "source.md"
    output_file = project_root / "source" / "01_extracted" / "chapters.json"

    # 支持命令行参数覆盖
    if len(sys.argv) > 1:
        source_file = Path(sys.argv[1])
    if len(sys.argv) > 2:
        output_file = Path(sys.argv[2])

    try:
        # 执行提取
        stats = extract_chapters(str(source_file), str(output_file))

        # 输出结果
        print(f"✓ 提取完成")
        print(f"  - 章节数: {stats['total_chapters']}")
        print(f"  - 总字数: {stats['total_words']}")
        print(f"  - 预估时长: {stats['total_duration_minutes']} 分钟")
        print(f"  - 输出文件: {stats['output_file']}")

        return 0

    except Exception as e:
        print(f"✗ 提取失败: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
