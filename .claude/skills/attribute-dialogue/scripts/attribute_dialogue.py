#!/usr/bin/env python3
"""
对白归属脚本
分析章节内容，将每段文本归属到旁白或具体角色。
"""

import json
import re
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple


def load_json(file_path: str) -> Dict:
    """加载JSON文件"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json(data: Dict, file_path: str):
    """保存JSON文件"""
    Path(file_path).parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def build_character_map(voice_mapping: Dict) -> Dict[str, Dict]:
    """构建角色名到角色信息的映射"""
    char_map = {}
    for assignment in voice_mapping['voice_assignments']:
        if assignment['character_id'] != 'narrator':
            char_map[assignment['character_name']] = {
                'character_id': assignment['character_id'],
                'speaker_name': assignment['character_name']
            }
    return char_map


def split_into_segments(content: str, char_map: Dict[str, Dict]) -> List[Dict]:
    """
    将章节内容分割为片段，并归属对话到角色

    识别模式：
    1. "对话内容" - 纯对话
    2. 角色名+动词+"对话内容" - 带说话人标记的对话
    3. 其他 - 旁白
    """
    segments = []

    # 按段落分割
    paragraphs = content.split('\n\n')

    # 用于跟踪上一个说话者（处理连续对话）
    last_speaker = None

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        # 检查是否包含引号（对话标记）
        if '"' in para or '"' in para or '"' in para:
            # 尝试提取对话和说话人
            result = extract_dialogue_and_speaker(para, char_map, last_speaker)

            if result:
                # 添加提取的片段
                for seg in result:
                    segments.append(seg)
                    # 更新最后的说话者
                    if seg['type'] == 'dialogue' and seg.get('speaker_id') != 'narrator':
                        last_speaker = seg.get('speaker_id')
            else:
                # 无法解析，作为旁白
                segments.append({
                    'type': 'narration',
                    'speaker_id': 'narrator',
                    'text': para,
                    'word_count': len(para)
                })
        else:
            # 没有引号，纯旁白
            segments.append({
                'type': 'narration',
                'speaker_id': 'narrator',
                'text': para,
                'word_count': len(para)
            })

    return segments


def extract_dialogue_and_speaker(para: str, char_map: Dict[str, Dict], last_speaker: str = None) -> List[Dict]:
    """
    从段落中提取对话和说话人

    返回片段列表，包含旁白和对话
    """
    segments = []

    # 匹配模式：角色名 + 动作动词 + 引号内容
    # 例如：周启明说："对话内容"
    # 例如：沈知夏冷笑："对话内容"
    pattern = r'([^，。！？：\n]{2,5}?)(说|道|问|答|喊|叫|笑|冷笑|苦笑|叹气|回|补|打断|叫住|看着|盯着|压着|咬牙|强撑|硬撑|开口|继续|接话|解释|急忙|猛地|忽然|终于)([^：]*?)[:：]?[""]([^"""]+)[""]'

    matches = list(re.finditer(pattern, para))

    if matches:
        last_end = 0

        for match in matches:
            # 对话前的旁白
            if match.start() > last_end:
                narration_text = para[last_end:match.start()].strip()
                if narration_text:
                    segments.append({
                        'type': 'narration',
                        'speaker_id': 'narrator',
                        'text': narration_text,
                        'word_count': len(narration_text)
                    })

            # 提取说话人和对话
            speaker_name = match.group(1).strip()
            action = match.group(2)
            action_suffix = match.group(3).strip()
            dialogue_text = match.group(4).strip()

            # 构建动作描述（作为旁白）
            action_text = speaker_name + action + action_suffix
            if action_text and action_text != speaker_name:
                segments.append({
                    'type': 'narration',
                    'speaker_id': 'narrator',
                    'text': action_text + '：',
                    'word_count': len(action_text) + 1
                })

            # 查找角色
            char_info = char_map.get(speaker_name)
            if char_info:
                # 找到角色，归属对话
                segments.append({
                    'type': 'dialogue',
                    'speaker_id': char_info['character_id'],
                    'speaker_name': speaker_name,
                    'text': dialogue_text,
                    'word_count': len(dialogue_text),
                    'emotion': infer_emotion(dialogue_text, action)
                })
            else:
                # 未识别的角色，作为旁白
                segments.append({
                    'type': 'narration',
                    'speaker_id': 'narrator',
                    'text': f'"{dialogue_text}"',
                    'word_count': len(dialogue_text) + 2
                })

            last_end = match.end()

        # 对话后的旁白
        if last_end < len(para):
            narration_text = para[last_end:].strip()
            if narration_text:
                segments.append({
                    'type': 'narration',
                    'speaker_id': 'narrator',
                    'text': narration_text,
                    'word_count': len(narration_text)
                })
    else:
        # 没有匹配到"角色+动词+对话"模式
        # 检查是否有纯引号对话
        pure_dialogue_pattern = r'[""]([^"""]+)[""]'
        pure_matches = list(re.finditer(pure_dialogue_pattern, para))

        if pure_matches:
            last_end = 0
            for match in pure_matches:
                # 对话前的文本
                if match.start() > last_end:
                    text_before = para[last_end:match.start()].strip()
                    if text_before:
                        segments.append({
                            'type': 'narration',
                            'speaker_id': 'narrator',
                            'text': text_before,
                            'word_count': len(text_before)
                        })

                # 纯对话（使用上一个说话者，或标记为未知）
                dialogue_text = match.group(1).strip()
                if last_speaker:
                    # 使用上一个说话者
                    speaker_name = None
                    for name, info in char_map.items():
                        if info['character_id'] == last_speaker:
                            speaker_name = name
                            break

                    if speaker_name:
                        segments.append({
                            'type': 'dialogue',
                            'speaker_id': last_speaker,
                            'speaker_name': speaker_name,
                            'text': dialogue_text,
                            'word_count': len(dialogue_text),
                            'emotion': 'neutral'
                        })
                    else:
                        segments.append({
                            'type': 'narration',
                            'speaker_id': 'narrator',
                            'text': f'"{dialogue_text}"',
                            'word_count': len(dialogue_text) + 2
                        })
                else:
                    # 无法确定说话者，作为旁白
                    segments.append({
                        'type': 'narration',
                        'speaker_id': 'narrator',
                        'text': f'"{dialogue_text}"',
                        'word_count': len(dialogue_text) + 2
                    })

                last_end = match.end()

            # 对话后的文本
            if last_end < len(para):
                text_after = para[last_end:].strip()
                if text_after:
                    segments.append({
                        'type': 'narration',
                        'speaker_id': 'narrator',
                        'text': text_after,
                        'word_count': len(text_after)
                    })
        else:
            # 完全没有对话，整段作为旁白
            segments.append({
                'type': 'narration',
                'speaker_id': 'narrator',
                'text': para,
                'word_count': len(para)
            })

    return segments


def infer_emotion(text: str, action: str) -> str:
    """根据对话内容和动作推断情绪"""
    # 简单的情绪推断规则
    if any(word in action for word in ['冷笑', '咬牙', '火', '怒']):
        return 'angry'
    elif any(word in action for word in ['苦笑', '叹气', '哽']):
        return 'sad'
    elif any(word in text for word in ['！', '？', '什么', '怎么']):
        if any(word in action for word in ['喊', '叫']):
            return 'surprised'
        elif any(word in action for word in ['冷笑', '咬牙']):
            return 'angry'

    return 'neutral'


def process_chapters(chapters_data: Dict, char_map: Dict) -> Dict:
    """处理所有章节"""
    attributed_chapters = []

    for chapter in chapters_data['chapters']:
        print(f"处理章节 {chapter['chapter_number']}: {chapter['title']}")

        segments = split_into_segments(chapter['content'], char_map)

        # 添加segment_id
        for i, segment in enumerate(segments, 1):
            segment['segment_id'] = f"{chapter['chapter_id']}_seg_{i:03d}"

        attributed_chapters.append({
            'chapter_id': chapter['chapter_id'],
            'chapter_number': chapter['chapter_number'],
            'title': chapter['title'],
            'segments': segments
        })

        print(f"  - 创建了 {len(segments)} 个片段")

    return {
        'total_chapters': len(attributed_chapters),
        'attribution_date': datetime.utcnow().isoformat() + 'Z',
        'chapters': attributed_chapters
    }


def main():
    """主函数"""
    # 获取项目根目录
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent.parent.parent.parent

    # 输入文件
    chapters_file = project_root / "source" / "01_extracted" / "chapters.json"
    voice_mapping_file = project_root / "source" / "02_casting" / "voice_mapping.json"

    # 输出文件
    output_file = project_root / "source" / "03_segmentation" / "attributed_chapters.json"

    try:
        print("正在加载数据...")
        chapters_data = load_json(str(chapters_file))
        voice_mapping = load_json(str(voice_mapping_file))

        print(f"  - 章节数: {chapters_data['total_chapters']}")
        print(f"  - 角色数: {voice_mapping['total_assignments'] - 1}")  # 减去旁白

        # 构建角色映射
        char_map = build_character_map(voice_mapping)
        print(f"  - 角色映射: {list(char_map.keys())}")

        # 处理章节
        print("\n开始处理章节...")
        result = process_chapters(chapters_data, char_map)

        # 统计信息
        total_segments = sum(len(ch['segments']) for ch in result['chapters'])
        dialogue_count = sum(
            sum(1 for seg in ch['segments'] if seg['type'] == 'dialogue')
            for ch in result['chapters']
        )
        narration_count = total_segments - dialogue_count

        # 角色对话统计
        char_dialogue_count = {}
        for chapter in result['chapters']:
            for segment in chapter['segments']:
                if segment['type'] == 'dialogue':
                    speaker = segment.get('speaker_name', 'unknown')
                    char_dialogue_count[speaker] = char_dialogue_count.get(speaker, 0) + 1

        # 保存结果
        print(f"\n保存结果到 {output_file}")
        save_json(result, str(output_file))

        # 输出统计
        print("\n✓ 对白归属完成")
        print(f"  - 处理章节: {result['total_chapters']}")
        print(f"  - 总片段数: {total_segments}")
        print(f"  - 对话片段: {dialogue_count} ({dialogue_count/total_segments*100:.1f}%)")
        print(f"  - 旁白片段: {narration_count} ({narration_count/total_segments*100:.1f}%)")
        print(f"\n角色对话统计:")
        for char, count in sorted(char_dialogue_count.items(), key=lambda x: x[1], reverse=True):
            print(f"  - {char}: {count} 次")

        return 0

    except Exception as e:
        print(f"✗ 处理失败: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
