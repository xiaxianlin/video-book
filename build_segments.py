#!/usr/bin/env python3
"""
构建 TTS 片段
将归属的章节内容转换为符合 TTS 要求的片段，严格遵守 75 秒时长和单一说话人约束
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

# 配置
WORDS_PER_SECOND = 2.5  # 中文语速：每秒约 2.5 字
TARGET_DURATION = 75  # 目标时长：75 秒
MAX_WORDS_PER_SEGMENT = int(TARGET_DURATION * WORDS_PER_SECOND)  # 约 187 字

# 路径配置
SOURCE_DIR = Path("source")
SEGMENTATION_DIR = SOURCE_DIR / "03_segmentation"
CASTING_DIR = SOURCE_DIR / "02_casting"
CONFIG_FILE = Path("configs/default_config.json")

def load_config() -> Dict[str, Any]:
    """加载配置文件"""
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_voice_mapping() -> Dict[str, str]:
    """加载音色映射"""
    voice_file = CASTING_DIR / "voice_mapping.json"
    with open(voice_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        return data.get('voice_assignments', {})

def load_character_descriptions() -> Dict[str, str]:
    """加载角色描述"""
    voice_file = CASTING_DIR / "voice_mapping.json"
    with open(voice_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        return data.get('character_descriptions', {})

def load_attributed_chapter(chapter_id: str) -> Dict[str, Any]:
    """加载归属的章节文件"""
    chapter_file = SEGMENTATION_DIR / f"{chapter_id}_attributed.json"
    with open(chapter_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def calculate_duration(word_count: int) -> float:
    """计算预估时长（秒）"""
    return word_count / WORDS_PER_SECOND

def build_tts_segments(config: Dict[str, Any], voice_mapping: Dict[str, str],
                       character_descriptions: Dict[str, str]) -> tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """构建 TTS 片段"""

    # 获取所有归属章节文件
    attributed_files = sorted(SEGMENTATION_DIR.glob("ch_*_attributed.json"))

    all_segments = []
    segment_counter = 1

    # 统计信息
    stats = {
        "total_segments": 0,
        "total_duration_seconds": 0,
        "segments_by_chapter": {},
        "segments_by_speaker": {},
        "chapters_processed": 0
    }

    for chapter_file in attributed_files:
        chapter_id = chapter_file.stem.replace("_attributed", "")
        print(f"处理章节: {chapter_id}")

        chapter_data = load_attributed_chapter(chapter_id)
        chapter_segments = chapter_data.get('segments', [])

        # 按说话人分组连续片段
        grouped_segments = []
        current_group = []
        current_speaker = None
        current_word_count = 0

        for seg in chapter_segments:
            speaker_id = seg.get('speaker_id')
            word_count = seg.get('word_count', 0)

            # 如果说话人改变或超过目标时长，开始新组
            if speaker_id != current_speaker or (current_word_count + word_count > MAX_WORDS_PER_SEGMENT):
                if current_group:
                    grouped_segments.append({
                        'speaker_id': current_speaker,
                        'segments': current_group,
                        'total_word_count': current_word_count
                    })
                current_group = [seg]
                current_speaker = speaker_id
                current_word_count = word_count
            else:
                current_group.append(seg)
                current_word_count += word_count

        # 添加最后一组
        if current_group:
            grouped_segments.append({
                'speaker_id': current_speaker,
                'segments': current_group,
                'total_word_count': current_word_count
            })

        # 为每组创建 TTS 片段
        chapter_segment_count = 0
        for group in grouped_segments:
            speaker_id = group['speaker_id']
            segments = group['segments']
            total_word_count = group['total_word_count']

            # 合并文本
            combined_text = ''.join([s.get('text', '') for s in segments])

            # 获取音色
            voice = voice_mapping.get(speaker_id, 'default_voice')

            # 获取说话人名称
            speaker_name = character_descriptions.get(speaker_id, speaker_id)

            # 计算预估时长
            estimated_duration = calculate_duration(total_word_count)

            # 创建 TTS 片段
            tts_segment = {
                "segment_id": f"seg_{segment_counter:05d}",
                "chapter_id": chapter_id,
                "speaker_id": speaker_id,
                "speaker_name": speaker_name,
                "voice": voice,
                "text": combined_text,
                "word_count": total_word_count,
                "estimated_duration_seconds": round(estimated_duration, 2),
                "emotion": "neutral",
                "emotion_intensity": config.get('segment', {}).get('emotion_intensity', 'low'),
                "sequence_number": segment_counter,
                "source_segment_ids": [s.get('segment_id') for s in segments]
            }

            all_segments.append(tts_segment)

            # 更新统计
            stats["total_duration_seconds"] += estimated_duration
            stats["segments_by_speaker"][speaker_id] = stats["segments_by_speaker"].get(speaker_id, 0) + 1

            segment_counter += 1
            chapter_segment_count += 1

        # 更新章节统计
        stats["segments_by_chapter"][chapter_id] = chapter_segment_count
        stats["chapters_processed"] += 1

        print(f"  - 生成 {chapter_segment_count} 个 TTS 片段")

    stats["total_segments"] = len(all_segments)
    stats["total_duration_seconds"] = round(stats["total_duration_seconds"], 2)

    return all_segments, stats

def main():
    """主函数"""
    print("=" * 60)
    print("构建 TTS 片段")
    print("=" * 60)

    # 加载配置
    print("\n1. 加载配置...")
    config = load_config()
    voice_mapping = load_voice_mapping()
    character_descriptions = load_character_descriptions()
    print(f"   - 目标时长: {config['segment']['target_duration_seconds']} 秒")
    print(f"   - 严格说话人分离: {config['segment']['strict_speaker_separation']}")
    print(f"   - 情绪强度: {config['segment']['emotion_intensity']}")

    # 构建片段
    print("\n2. 构建 TTS 片段...")
    segments, stats = build_tts_segments(config, voice_mapping, character_descriptions)

    # 保存输出
    print("\n3. 保存输出文件...")

    # 保存 tts_segments.json
    output_file = SEGMENTATION_DIR / "tts_segments.json"
    output_data = {
        "creation_date": datetime.now().isoformat(),
        "total_segments": stats["total_segments"],
        "total_duration_seconds": stats["total_duration_seconds"],
        "target_duration_per_segment": TARGET_DURATION,
        "words_per_second": WORDS_PER_SECOND,
        "strict_speaker_separation": config['segment']['strict_speaker_separation'],
        "segments": segments
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    print(f"   - 已保存: {output_file}")

    # 保存 segment_manifest.json
    manifest_file = SEGMENTATION_DIR / "segment_manifest.json"
    manifest_data = {
        "creation_date": datetime.now().isoformat(),
        "total_segments": stats["total_segments"],
        "total_duration_seconds": stats["total_duration_seconds"],
        "total_duration_minutes": round(stats["total_duration_seconds"] / 60, 2),
        "average_segment_duration": round(stats["total_duration_seconds"] / stats["total_segments"], 2) if stats["total_segments"] > 0 else 0,
        "chapters_processed": stats["chapters_processed"],
        "segments_by_chapter": stats["segments_by_chapter"],
        "segments_by_speaker": stats["segments_by_speaker"]
    }

    with open(manifest_file, 'w', encoding='utf-8') as f:
        json.dump(manifest_data, f, ensure_ascii=False, indent=2)
    print(f"   - 已保存: {manifest_file}")

    # 验证和报告
    print("\n4. 验证结果...")
    validation_passed = True

    # 检查所有片段是否 <= 75 秒
    over_limit = [s for s in segments if s['estimated_duration_seconds'] > TARGET_DURATION]
    if over_limit:
        print(f"   ⚠️  警告: {len(over_limit)} 个片段超过 {TARGET_DURATION} 秒")
        validation_passed = False
    else:
        print(f"   ✓ 所有片段都在 {TARGET_DURATION} 秒以内")

    # 检查每个片段是否只有一个说话人（已通过设计保证）
    print(f"   ✓ 每个片段恰好有一个说话人（严格分离）")

    # 检查所有片段是否有音色分配
    missing_voice = [s for s in segments if not s.get('voice') or s['voice'] == 'default_voice']
    if missing_voice:
        print(f"   ⚠️  警告: {len(missing_voice)} 个片段缺少音色分配")
        validation_passed = False
    else:
        print(f"   ✓ 所有片段都有音色分配")

    # 报告结果
    print("\n" + "=" * 60)
    print("构建完成！")
    print("=" * 60)
    print(f"\n总片段数: {stats['total_segments']}")
    print(f"总时长: {stats['total_duration_seconds']} 秒 ({manifest_data['total_duration_minutes']} 分钟)")
    print(f"平均片段时长: {manifest_data['average_segment_duration']} 秒")
    print(f"处理章节数: {stats['chapters_processed']}")

    print("\n按章节分布:")
    for chapter_id, count in sorted(stats['segments_by_chapter'].items()):
        print(f"  - {chapter_id}: {count} 个片段")

    print("\n按说话人分布:")
    for speaker_id, count in sorted(stats['segments_by_speaker'].items(), key=lambda x: x[1], reverse=True):
        speaker_name = character_descriptions.get(speaker_id, speaker_id)
        print(f"  - {speaker_name} ({speaker_id}): {count} 个片段")

    if validation_passed:
        print("\n✓ 验证通过！所有片段符合要求。")
    else:
        print("\n⚠️  验证发现问题，请检查上述警告。")

    print("\n下一步: 运行 /generate-tts-audio 生成音频文件")

if __name__ == "__main__":
    main()


