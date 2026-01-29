#!/usr/bin/env python3
"""
音频后处理脚本
对原始 TTS 文件应用专业音频处理：添加静音、标准化响度、编码为 MP3
"""

import os
import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 路径配置
PROJECT_ROOT = Path(__file__).parent
INPUT_DIR = PROJECT_ROOT / 'source' / '04_tts_raw'
OUTPUT_SEGMENTS_DIR = PROJECT_ROOT / 'source' / '05_post' / 'segments'
OUTPUT_CHAPTERS_DIR = PROJECT_ROOT / 'source' / '05_post' / 'chapters'
SEGMENTS_FILE = PROJECT_ROOT / 'source' / '03_segmentation' / 'tts_segments.json'
CONFIG_FILE = PROJECT_ROOT / 'configs' / 'default_config.json'
LOG_FILE = PROJECT_ROOT / 'source' / '05_post' / 'processing_log.json'

# 音频处理参数
SILENCE_START_MS = 200
SILENCE_END_MS = 300
TARGET_LUFS = -18
TRUE_PEAK_DBTP = -1.0
MP3_BITRATE = '192k'

def load_config() -> Dict[str, Any]:
    """加载配置文件"""
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_segments() -> Dict[str, Any]:
    """加载片段元数据"""
    with open(SEGMENTS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def process_segment(input_file: Path, output_file: Path) -> Dict[str, Any]:
    """处理单个音频片段"""
    try:
        # 构建 ffmpeg 命令：添加静音 + 标准化响度 + 编码为 MP3
        cmd = [
            'ffmpeg',
            '-i', str(input_file),
            '-af', f'adelay={SILENCE_START_MS}|{SILENCE_START_MS},apad=pad_dur={SILENCE_END_MS}ms,loudnorm=I={TARGET_LUFS}:TP={TRUE_PEAK_DBTP}:LRA=11',
            '-codec:a', 'libmp3lame',
            '-b:a', MP3_BITRATE,
            '-ac', '1',  # mono
            '-y',  # 覆盖已存在的文件
            str(output_file)
        ]

        # 执行命令
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode != 0:
            logger.error(f"处理失败: {input_file.name}")
            logger.error(result.stderr)
            return {
                'success': False,
                'error': result.stderr
            }

        # 获取输出文件信息
        file_size = output_file.stat().st_size

        return {
            'success': True,
            'input_file': str(input_file),
            'output_file': str(output_file),
            'file_size_bytes': file_size,
            'file_size_mb': round(file_size / (1024 * 1024), 2)
        }

    except subprocess.TimeoutExpired:
        logger.error(f"处理超时: {input_file.name}")
        return {'success': False, 'error': 'Timeout'}
    except Exception as e:
        logger.error(f"处理错误: {input_file.name} - {str(e)}")
        return {'success': False, 'error': str(e)}

def merge_chapter(chapter_id: str, segment_ids: List[str]) -> Dict[str, Any]:
    """合并片段为章节文件"""
    try:
        # 创建文件列表
        filelist_path = OUTPUT_CHAPTERS_DIR / f'{chapter_id}_filelist.txt'
        with open(filelist_path, 'w') as f:
            for seg_id in segment_ids:
                seg_file = OUTPUT_SEGMENTS_DIR / f'{seg_id}.mp3'
                if seg_file.exists():
                    f.write(f"file '{seg_file.absolute()}'\n")

        # 合并文件
        output_file = OUTPUT_CHAPTERS_DIR / f'{chapter_id}.mp3'
        cmd = [
            'ffmpeg',
            '-f', 'concat',
            '-safe', '0',
            '-i', str(filelist_path),
            '-c', 'copy',
            '-y',
            str(output_file)
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120
        )

        # 删除临时文件列表
        filelist_path.unlink()

        if result.returncode != 0:
            logger.error(f"合并失败: {chapter_id}")
            return {'success': False, 'error': result.stderr}

        file_size = output_file.stat().st_size

        return {
            'success': True,
            'chapter_id': chapter_id,
            'output_file': str(output_file),
            'file_size_mb': round(file_size / (1024 * 1024), 2)
        }

    except Exception as e:
        logger.error(f"合并错误: {chapter_id} - {str(e)}")
        return {'success': False, 'error': str(e)}

def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("音频后处理开始")
    logger.info("=" * 60)

    # 加载配置和片段信息
    logger.info("\n1. 加载配置...")
    config = load_config()
    segments_data = load_segments()
    segments = segments_data['segments']

    logger.info(f"   - 总片段数: {len(segments)}")
    logger.info(f"   - 目标响度: {TARGET_LUFS} LUFS")
    logger.info(f"   - MP3 比特率: {MP3_BITRATE}")

    # 处理所有片段
    logger.info("\n2. 处理音频片段...")
    processed_segments = []
    failed_segments = []
    total_size = 0

    for i, segment in enumerate(segments, 1):
        segment_id = segment['segment_id']
        input_file = INPUT_DIR / f'{segment_id}.wav'
        output_file = OUTPUT_SEGMENTS_DIR / f'{segment_id}.mp3'

        # 跳过已存在的文件
        if output_file.exists():
            logger.info(f"   [{i}/{len(segments)}] 跳过 {segment_id} (已存在)")
            processed_segments.append({
                'segment_id': segment_id,
                'skipped': True
            })
            continue

        if not input_file.exists():
            logger.warning(f"   [{i}/{len(segments)}] 输入文件不存在: {segment_id}")
            failed_segments.append(segment_id)
            continue

        logger.info(f"   [{i}/{len(segments)}] 处理 {segment_id}...")
        result = process_segment(input_file, output_file)

        if result['success']:
            total_size += result['file_size_bytes']
            processed_segments.append({
                'segment_id': segment_id,
                **result
            })
        else:
            failed_segments.append(segment_id)

    logger.info(f"\n   ✓ 处理完成: {len(processed_segments)} 个片段")
    logger.info(f"   ✗ 失败: {len(failed_segments)} 个片段")
    logger.info(f"   总大小: {round(total_size / (1024 * 1024), 2)} MB")

    # 按章节组织片段
    logger.info("\n3. 合并章节...")
    chapters = {}
    for segment in segments:
        chapter_id = segment['chapter_id']
        if chapter_id not in chapters:
            chapters[chapter_id] = []
        chapters[chapter_id].append(segment['segment_id'])

    merged_chapters = []
    for chapter_id in sorted(chapters.keys()):
        logger.info(f"   合并 {chapter_id}...")
        result = merge_chapter(chapter_id, chapters[chapter_id])
        if result['success']:
            merged_chapters.append(result)
            logger.info(f"      ✓ {result['file_size_mb']} MB")
        else:
            logger.error(f"      ✗ 失败")

    # 生成处理日志
    logger.info("\n4. 生成处理日志...")
    log_data = {
        'processing_date': datetime.now().isoformat(),
        'segments_processed': len(processed_segments),
        'segments_failed': len(failed_segments),
        'chapters_created': len(merged_chapters),
        'processing_stats': {
            'total_segments': len(segments),
            'successful_segments': len([s for s in processed_segments if not s.get('skipped')]),
            'skipped_segments': len([s for s in processed_segments if s.get('skipped')]),
            'total_output_size_mb': round(total_size / (1024 * 1024), 2)
        },
        'chapters': merged_chapters,
        'failed_segments': failed_segments
    }

    with open(LOG_FILE, 'w', encoding='utf-8') as f:
        json.dump(log_data, f, ensure_ascii=False, indent=2)

    logger.info(f"   ✓ 日志已保存: {LOG_FILE}")

    # 报告结果
    logger.info("\n" + "=" * 60)
    logger.info("音频后处理完成！")
    logger.info("=" * 60)
    logger.info(f"\n处理的片段: {len(processed_segments)}")
    logger.info(f"创建的章节: {len(merged_chapters)}")
    logger.info(f"失败的片段: {len(failed_segments)}")
    logger.info(f"\n输出位置:")
    logger.info(f"  - 片段: {OUTPUT_SEGMENTS_DIR}")
    logger.info(f"  - 章节: {OUTPUT_CHAPTERS_DIR}")
    logger.info(f"\n下一步: 运行 /package-release 打包最终发布")

if __name__ == "__main__":
    main()

