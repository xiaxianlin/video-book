#!/usr/bin/env python3
"""
MiniMax TTS 生成脚本
使用 MiniMax API 为有声书片段生成语音
"""

import os
import json
import time
import requests
from pathlib import Path
from typing import Dict, List, Optional
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# MiniMax API 配置
MINIMAX_API_KEY = os.getenv('MINIMAX_API_KEY')
MINIMAX_API_URL = 'https://api.minimaxi.com/v1/t2a_v2'
MINIMAX_API_URL_BACKUP = 'https://api-bj.minimaxi.com/v1/t2a_v2'

# 项目路径配置
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent  # 回到项目根目录
SEGMENTS_FILE = PROJECT_ROOT / 'source' / '03_segmentation' / 'tts_segments.json'
OUTPUT_DIR = PROJECT_ROOT / 'source' / '04_tts_raw'
VOICE_MAPPING_FILE = PROJECT_ROOT / 'source' / '02_casting' / 'voice_mapping.json'
LOG_FILE = OUTPUT_DIR / 'generation_log.json'
FAILED_FILE = OUTPUT_DIR / 'failed_segments.json'

# TTS 配置
TTS_CONFIG = {
    'model': 'speech-2.8-hd',  # 使用最新的高清模型
    'audio_setting': {
        'sample_rate': 32000,
        'bitrate': 128000,
        'format': 'wav',
        'channel': 1  # 单声道
    },
    'stream': False  # 非流式输出
}

# 默认音色映射（如果 voice_mapping.json 不存在）
DEFAULT_VOICE_MAPPING = {
    'narrator': 'moss_audio_ce44fc67-7ce3-11f0-8de5-96e35d26fb85',
    'char_001': 'Chinese (Mandarin)_Lyrical_Voice',
    'char_002': 'Chinese (Mandarin)_Graceful_Lady',
    'char_003': 'Chinese (Mandarin)_Persuasive_Man',
    'char_004': 'Chinese (Mandarin)_Mature_Woman',
    'char_005': 'Chinese (Mandarin)_Steady_Man',
    'char_006': 'Chinese (Mandarin)_Professional_Man',
    'char_007': 'Chinese (Mandarin)_Young_Woman',
    'char_008': 'Chinese (Mandarin)_Neutral_Voice'
}

# 情感映射（将我们的情感标签映射到 MiniMax 支持的情感）
EMOTION_MAPPING = {
    'happy': 'happy',
    'sad': 'sad',
    'angry': 'angry',
    'fearful': 'fearful',
    'surprised': 'surprised',
    'calm': 'calm',
    'cold': 'calm',
    'nervous': 'fearful',
    'tense': 'fearful',
    'professional': 'calm',
    'desperate': 'sad',
    'shocked': 'surprised',
    'bitter': 'sad',
    'frustrated': 'angry',
    'panicked': 'fearful',
    'defensive': 'angry',
    'resigned': 'sad',
    'determined': 'calm',
    'threatening': 'angry',
    'pleading': 'sad',
    'sarcastic': 'calm',
    'mocking': 'happy',
    'whisper': 'whisper'
}


def load_voice_mapping() -> Dict[str, str]:
    """加载音色映射配置"""
    if VOICE_MAPPING_FILE.exists():
        with open(VOICE_MAPPING_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('voice_assignments', DEFAULT_VOICE_MAPPING)
    return DEFAULT_VOICE_MAPPING


def load_segments() -> List[Dict]:
    """加载 TTS 片段"""
    if not SEGMENTS_FILE.exists():
        raise FileNotFoundError(f"TTS segments file not found: {SEGMENTS_FILE}")

    with open(SEGMENTS_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
        return data.get('segments', [])


def generate_audio(text: str, voice_id: str, emotion: Optional[str] = None,
                   segment_id: str = '') -> Optional[bytes]:
    """
    使用 MiniMax API 生成音频

    Args:
        text: 要合成的文本
        voice_id: 音色ID
        emotion: 情感标签
        segment_id: 片段ID（用于日志）

    Returns:
        音频数据（bytes）或 None（失败时）
    """
    if not MINIMAX_API_KEY:
        raise ValueError("MINIMAX_API_KEY environment variable not set")

    # 构建请求参数
    voice_setting = {
        'voice_id': voice_id,
        'speed': 1.0,
        'vol': 1.0,
        'pitch': 0
    }

    # 添加情感（如果支持）
    if emotion and emotion in EMOTION_MAPPING:
        voice_setting['emotion'] = EMOTION_MAPPING[emotion]

    payload = {
        'model': TTS_CONFIG['model'],
        'text': text,
        'voice_setting': voice_setting,
        'audio_setting': TTS_CONFIG['audio_setting'],
        'stream': TTS_CONFIG['stream']
    }

    headers = {
        'Authorization': f'Bearer {MINIMAX_API_KEY}',
        'Content-Type': 'application/json'
    }

    # 尝试主 API 和备用 API
    for api_url in [MINIMAX_API_URL, MINIMAX_API_URL_BACKUP]:
        try:
            logger.info(f"Generating audio for segment {segment_id} using {voice_id}")
            response = requests.post(api_url, json=payload, headers=headers, timeout=60)

            if response.status_code == 200:
                result = response.json()

                # 检查响应状态
                if result.get('base_resp', {}).get('status_code') == 0:
                    # 获取音频数据（hex 编码）
                    audio_hex = result.get('data', {}).get('audio', '')
                    if audio_hex:
                        # 将 hex 转换为 bytes
                        audio_bytes = bytes.fromhex(audio_hex)
                        logger.info(f"Successfully generated {len(audio_bytes)} bytes for {segment_id}")
                        return audio_bytes
                    else:
                        logger.error(f"No audio data in response for {segment_id}")
                else:
                    error_msg = result.get('base_resp', {}).get('status_msg', 'Unknown error')
                    logger.error(f"API error for {segment_id}: {error_msg}")
            else:
                logger.error(f"HTTP {response.status_code} for {segment_id}: {response.text}")

        except requests.exceptions.Timeout:
            logger.warning(f"Timeout for {segment_id} on {api_url}, trying backup...")
            continue
        except Exception as e:
            logger.error(f"Error generating audio for {segment_id}: {e}")
            continue

    return None


def save_audio(audio_data: bytes, segment_id: str) -> bool:
    """保存音频文件"""
    try:
        output_file = OUTPUT_DIR / f"{segment_id}.wav"
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'wb') as f:
            f.write(audio_data)

        logger.info(f"Saved audio to {output_file}")
        return True
    except Exception as e:
        logger.error(f"Error saving audio for {segment_id}: {e}")
        return False


def main():
    """主函数"""
    logger.info("Starting MiniMax TTS generation")

    # 检查 API key
    if not MINIMAX_API_KEY:
        logger.error("MINIMAX_API_KEY environment variable not set")
        logger.error("Please set it with: export MINIMAX_API_KEY='your_api_key'")
        return

    # 创建输出目录
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 加载配置
    voice_mapping = load_voice_mapping()
    logger.info(f"Loaded voice mapping for {len(voice_mapping)} speakers")

    # 加载片段
    segments = load_segments()
    logger.info(f"Loaded {len(segments)} TTS segments")

    # 统计
    stats = {
        'total': len(segments),
        'successful': 0,
        'failed': 0,
        'skipped': 0
    }

    failed_segments = []

    # 处理每个片段
    for i, segment in enumerate(segments, 1):
        segment_id = segment.get('segment_id', f'unknown_{i}')
        text = segment.get('text', '')
        speaker_id = segment.get('speaker_id', 'narrator')
        emotion = segment.get('emotion')

        logger.info(f"Processing {i}/{len(segments)}: {segment_id}")

        # 检查是否已存在
        output_file = OUTPUT_DIR / f"{segment_id}.wav"
        if output_file.exists():
            logger.info(f"Skipping {segment_id} (already exists)")
            stats['skipped'] += 1
            continue

        # 获取音色
        voice_id = voice_mapping.get(speaker_id, voice_mapping.get('narrator'))

        # 生成音频
        audio_data = generate_audio(text, voice_id, emotion, segment_id)

        if audio_data:
            if save_audio(audio_data, segment_id):
                stats['successful'] += 1
            else:
                stats['failed'] += 1
                failed_segments.append({
                    'segment_id': segment_id,
                    'error': 'Failed to save audio'
                })
        else:
            stats['failed'] += 1
            failed_segments.append({
                'segment_id': segment_id,
                'error': 'Failed to generate audio'
            })

        # 速率限制：每次请求后等待一小段时间
        if i < len(segments):
            time.sleep(0.5)

    # 保存日志
    log_data = {
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'stats': stats,
        'failed_count': len(failed_segments)
    }

    with open(LOG_FILE, 'w', encoding='utf-8') as f:
        json.dump(log_data, f, ensure_ascii=False, indent=2)

    # 保存失败的片段
    if failed_segments:
        with open(FAILED_FILE, 'w', encoding='utf-8') as f:
            json.dump(failed_segments, f, ensure_ascii=False, indent=2)

    # 输出总结
    logger.info("=" * 60)
    logger.info("TTS Generation Complete")
    logger.info(f"Total segments: {stats['total']}")
    logger.info(f"Successful: {stats['successful']}")
    logger.info(f"Failed: {stats['failed']}")
    logger.info(f"Skipped: {stats['skipped']}")
    logger.info("=" * 60)

    if failed_segments:
        logger.warning(f"Failed segments saved to: {FAILED_FILE}")


if __name__ == '__main__':
    main()

