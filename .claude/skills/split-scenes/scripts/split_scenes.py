#!/usr/bin/env python3
"""
场景拆分脚本
将归属后的章节拆分为逻辑场景。
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List


def load_json(file_path: str) -> Dict:
    """加载JSON文件"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json(data: Dict, file_path: str):
    """保存JSON文件"""
    Path(file_path).parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def split_chapter_into_scenes(chapter: Dict, target_words: int = 600) -> List[Dict]:
    """
    将章节拆分为场景

    简化策略：
    - 按照目标字数（约4分钟）拆分
    - 在段落边界处拆分
    - 保持场景的完整性
    """
    scenes = []
    current_scene_segments = []
    current_word_count = 0
    scene_number = 1

    for segment in chapter['segments']:
        segment_words = segment['word_count']

        # 如果当前场景已经达到目标字数，且不是第一个片段，则创建新场景
        if current_word_count > 0 and current_word_count + segment_words > target_words:
            # 保存当前场景
            scene = create_scene(
                chapter['chapter_id'],
                scene_number,
                current_scene_segments,
                current_word_count
            )
            scenes.append(scene)

            # 开始新场景
            scene_number += 1
            current_scene_segments = [segment]
            current_word_count = segment_words
        else:
            # 添加到当前场景
            current_scene_segments.append(segment)
            current_word_count += segment_words

    # 保存最后一个场景
    if current_scene_segments:
        scene = create_scene(
            chapter['chapter_id'],
            scene_number,
            current_scene_segments,
            current_word_count
        )
        scenes.append(scene)

    return scenes


def create_scene(chapter_id: str, scene_number: int, segments: List[Dict], word_count: int) -> Dict:
    """创建场景对象"""
    scene_id = f"{chapter_id}_sc_{scene_number:03d}"

    # 估算时长（假设每分钟150字）
    estimated_duration = (word_count / 150) * 60

    return {
        'scene_id': scene_id,
        'scene_number': scene_number,
        'segments': segments,
        'total_word_count': word_count,
        'estimated_duration_seconds': int(estimated_duration)
    }


def process_chapters(attributed_data: Dict) -> Dict:
    """处理所有章节"""
    result_chapters = []
    total_scenes = 0

    for chapter in attributed_data['chapters']:
        print(f"处理章节 {chapter['chapter_number']}: {chapter['title']}")

        scenes = split_chapter_into_scenes(chapter)

        result_chapters.append({
            'chapter_id': chapter['chapter_id'],
            'chapter_number': chapter['chapter_number'],
            'title': chapter['title'],
            'scenes': scenes,
            'total_scenes': len(scenes)
        })

        total_scenes += len(scenes)
        print(f"  - 创建了 {len(scenes)} 个场景")

    return {
        'total_chapters': len(result_chapters),
        'total_scenes': total_scenes,
        'split_date': datetime.utcnow().isoformat() + 'Z',
        'chapters': result_chapters
    }


def main():
    """主函数"""
    # 获取项目根目录
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent.parent.parent.parent

    # 输入文件
    input_file = project_root / "source" / "03_segmentation" / "attributed_chapters.json"

    # 输出文件
    output_file = project_root / "source" / "03_segmentation" / "scenes.json"

    try:
        print("正在加载数据...")
        attributed_data = load_json(str(input_file))

        print(f"  - 章节数: {attributed_data['total_chapters']}")

        # 处理章节
        print("\n开始拆分场景...")
        result = process_chapters(attributed_data)

        # 统计信息
        scene_durations = []
        for chapter in result['chapters']:
            for scene in chapter['scenes']:
                scene_durations.append(scene['estimated_duration_seconds'])

        avg_duration = sum(scene_durations) / len(scene_durations) if scene_durations else 0
        min_duration = min(scene_durations) if scene_durations else 0
        max_duration = max(scene_durations) if scene_durations else 0

        # 保存结果
        print(f"\n保存结果到 {output_file}")
        save_json(result, str(output_file))

        # 输出统计
        print("\n✓ 场景拆分完成")
        print(f"  - 处理章节: {result['total_chapters']}")
        print(f"  - 总场景数: {result['total_scenes']}")
        print(f"  - 平均场景时长: {avg_duration:.1f} 秒 ({avg_duration/60:.1f} 分钟)")
        print(f"  - 场景时长范围: {min_duration:.0f}-{max_duration:.0f} 秒")

        return 0

    except Exception as e:
        print(f"✗ 处理失败: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
