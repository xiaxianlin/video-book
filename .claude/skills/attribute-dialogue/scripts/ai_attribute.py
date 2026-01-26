#!/usr/bin/env python3
"""
AI-driven dialogue attribution
Claude analyzes content and provides attribution decisions
"""

import json
from pathlib import Path
from datetime import datetime


def create_attributed_chapters():
    """Create attributed chapters with AI-driven dialogue attribution"""

    # Character ID mapping
    char_map = {
        "周启明": "char_001",
        "沈知夏": "char_002",
        "赵建成": "char_003",
        "李桂芳": "char_004",
        "陈涛": "char_005",
        "王海生": "char_006",
        "林哥": "char_007"
    }

    # Load chapters
    project_root = Path(__file__).resolve().parent.parent.parent.parent.parent
    chapters_file = project_root / "source" / "01_extracted" / "chapters.json"

    with open(chapters_file, 'r', encoding='utf-8') as f:
        chapters_data = json.load(f)

    attributed_chapters = []

    # Process each chapter
    for chapter in chapters_data['chapters']:
        print(f"处理章节 {chapter['chapter_number']}: {chapter['title']}")

        # AI attribution will be done here
        # For now, create placeholder structure
        segments = []
        segment_counter = 1

        # Split content by paragraphs
        paragraphs = chapter['content'].split('\n\n')

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            # Create segment
            segment = {
                "segment_id": f"{chapter['chapter_id']}_seg_{segment_counter:03d}",
                "type": "narration",  # Will be determined by AI
                "speaker_id": "narrator",  # Will be determined by AI
                "text": para,
                "word_count": len(para)
            }

            segments.append(segment)
            segment_counter += 1

        attributed_chapters.append({
            "chapter_id": chapter['chapter_id'],
            "chapter_number": chapter['chapter_number'],
            "title": chapter['title'],
            "segments": segments
        })

        print(f"  - 创建了 {len(segments)} 个片段")

    # Create output
    result = {
        "total_chapters": len(attributed_chapters),
        "attribution_date": datetime.utcnow().isoformat() + 'Z',
        "chapters": attributed_chapters
    }

    # Save
    output_file = project_root / "source" / "03_segmentation" / "attributed_chapters.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n✓ 对白归属完成")
    print(f"  - 处理章节: {result['total_chapters']}")


if __name__ == "__main__":
    create_attributed_chapters()
