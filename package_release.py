#!/usr/bin/env python3
"""
打包发布脚本
生成最终发布包的元数据和文档
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# 路径配置
PROJECT_ROOT = Path(__file__).parent
RELEASE_DIR = PROJECT_ROOT / 'release'
AUDIO_DIR = RELEASE_DIR / 'audio' / 'chapters'
SOURCE_DIR = PROJECT_ROOT / 'source'

# 加载源数据
CHAPTERS_FILE = SOURCE_DIR / '01_extracted' / 'chapters.json'
VOICE_MAPPING_FILE = SOURCE_DIR / '02_casting' / 'voice_mapping.json'
SEGMENT_MANIFEST_FILE = SOURCE_DIR / '03_segmentation' / 'segment_manifest.json'
PROCESSING_LOG_FILE = SOURCE_DIR / '05_post' / 'processing_log.json'

def load_json(file_path: Path) -> Dict[str, Any]:
    """加载 JSON 文件"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def format_duration(seconds: float) -> str:
    """格式化时长为可读格式"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)

    if hours > 0:
        return f"{hours}h {minutes}m {secs}s"
    elif minutes > 0:
        return f"{minutes}m {secs}s"
    else:
        return f"{secs}s"

def get_audio_file_info(file_path: Path) -> Dict[str, Any]:
    """获取音频文件信息"""
    stat = file_path.stat()
    return {
        'file_size_bytes': stat.st_size,
        'file_size_mb': round(stat.st_size / (1024 * 1024), 2)
    }

def generate_meta_json() -> Dict[str, Any]:
    """生成 meta.json"""
    print("生成 meta.json...")

    # 加载源数据
    chapters_data = load_json(CHAPTERS_FILE)
    voice_mapping = load_json(VOICE_MAPPING_FILE)
    segment_manifest = load_json(SEGMENT_MANIFEST_FILE)
    processing_log = load_json(PROCESSING_LOG_FILE)

    # 计算总时长
    total_duration = segment_manifest['total_duration_seconds']

    # 统计字数
    total_word_count = sum(ch.get('word_count', 0) for ch in chapters_data.get('chapters', []))

    meta = {
        'project': {
            'name': 'audiobook_project',
            'version': '1.0.0',
            'generation_date': datetime.now().isoformat(),
            'pipeline_version': 'v1.0'
        },
        'source': {
            'input_file': 'input/source.md',
            'total_chapters': chapters_data.get('total_chapters', 0),
            'total_word_count': total_word_count
        },
        'audio': {
            'total_duration_seconds': total_duration,
            'total_duration_formatted': format_duration(total_duration),
            'format': 'MP3',
            'bitrate': '192kbps',
            'channels': 'mono',
            'sample_rate': '32000Hz',
            'loudness_lufs': -18,
            'true_peak_dbtp': -1.0
        },
        'production': {
            'tts_provider': 'minimax',
            'total_segments': segment_manifest['total_segments'],
            'target_loudness_lufs': -18,
            'characters_count': len(voice_mapping.get('voice_assignments', {}))
        },
        'characters': []
    }

    # 添加角色信息
    voice_assignments = voice_mapping.get('voice_assignments', {})
    character_descriptions = voice_mapping.get('character_descriptions', {})
    segments_by_speaker = segment_manifest.get('segments_by_speaker', {})

    for char_id, voice_id in voice_assignments.items():
        meta['characters'].append({
            'character_id': char_id,
            'name': character_descriptions.get(char_id, char_id),
            'voice': voice_id,
            'total_segments': segments_by_speaker.get(char_id, 0)
        })

    return meta

def generate_chapters_json() -> Dict[str, Any]:
    """生成 chapters.json"""
    print("生成 chapters.json...")

    chapters_data = load_json(CHAPTERS_FILE)
    segment_manifest = load_json(SEGMENT_MANIFEST_FILE)

    chapters_list = []

    for chapter in chapters_data.get('chapters', []):
        chapter_id = chapter['chapter_id']
        chapter_number = chapter['chapter_number']
        title = chapter.get('title', f'Chapter {chapter_number}')

        # 获取音频文件信息
        audio_file = AUDIO_DIR / f'{chapter_id}.mp3'
        if audio_file.exists():
            file_info = get_audio_file_info(audio_file)

            # 估算时长（基于片段数）
            segment_count = segment_manifest['segments_by_chapter'].get(chapter_id, 0)
            avg_duration = segment_manifest['total_duration_seconds'] / segment_manifest['total_segments']
            estimated_duration = segment_count * avg_duration

            chapters_list.append({
                'chapter_number': chapter_number,
                'chapter_id': chapter_id,
                'title': title,
                'audio_file': f'audio/chapters/{chapter_id}.mp3',
                'duration_seconds': round(estimated_duration, 2),
                'duration_formatted': format_duration(estimated_duration),
                'word_count': chapter.get('word_count', 0),
                'file_size_mb': file_info['file_size_mb'],
                'segment_count': segment_count
            })

    return {
        'total_chapters': len(chapters_list),
        'chapters': chapters_list
    }

def generate_readme() -> str:
    """生成 README.md"""
    print("生成 README.md...")

    meta = load_json(RELEASE_DIR / 'meta.json')
    chapters = load_json(RELEASE_DIR / 'chapters.json')

    readme = f"""# 有声书发布

## 项目信息
- **生成日期**: {meta['project']['generation_date'][:10]}
- **总章节数**: {meta['source']['total_chapters']}
- **总时长**: {meta['audio']['total_duration_formatted']}
- **总字数**: {meta['source']['total_word_count']:,}

## 音频规格
- **格式**: {meta['audio']['format']}
- **比特率**: {meta['audio']['bitrate']}
- **声道**: {meta['audio']['channels']}
- **采样率**: {meta['audio']['sample_rate']}
- **响度**: {meta['audio']['loudness_lufs']} LUFS (播客标准)
- **真峰值**: {meta['audio']['true_peak_dbtp']} dBTP

## 内容

### 章节列表

"""

    for ch in chapters['chapters']:
        readme += f"{ch['chapter_number']}. **{ch['title']}** - {ch['duration_formatted']} ({ch['file_size_mb']} MB)\n"

    readme += f"""

## 音频文件

所有章节音频文件位于 `audio/chapters/` 目录：

"""

    for ch in chapters['chapters']:
        readme += f"- `{ch['audio_file']}` - {ch['title']}\n"

    readme += f"""

## 技术规格

### TTS 生成
- **提供商**: {meta['production']['tts_provider']}
- **总片段数**: {meta['production']['total_segments']}
- **片段目标时长**: 75 秒
- **严格说话人分离**: 是

### 音频处理
- 静音填充: 开头 200ms, 结尾 300ms
- 响度标准化: EBU R128
- 目标响度: {meta['production']['target_loudness_lufs']} LUFS
- MP3 编码: LAME, VBR

## 角色与音色

本有声书包含 {meta['production']['characters_count']} 个角色/说话人：

"""

    for char in meta['characters']:
        readme += f"- **{char['name']}** ({char['character_id']}): {char['total_segments']} 个片段\n"

    readme += """

## 使用方法

### 播放章节
按顺序播放 `audio/chapters/` 目录中的 MP3 文件。

### 播放器兼容性
这些 MP3 文件与所有标准音频播放器兼容，包括：
- iTunes / Apple Music
- VLC Media Player
- Windows Media Player
- 移动设备音乐应用
- 播客应用

## 文件结构

```
release/
├── audio/
│   └── chapters/
│       ├── ch_001.mp3
│       ├── ch_002.mp3
│       └── ...
├── meta.json          # 完整项目元数据
├── chapters.json      # 章节信息
└── README.md          # 本文档
```

## 生成信息

本有声书使用自动化流水线生成：
1. 章节提取
2. 角色识别与音色分配
3. 对话归属
4. 场景分割
5. TTS 片段构建
6. TTS 音频生成
7. 音频后处理（静音、响度标准化、MP3 编码）
8. 打包发布

---

生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

    return readme

def main():
    """主函数"""
    print("=" * 60)
    print("打包发布")
    print("=" * 60)

    # 生成 meta.json
    print("\n1. 生成元数据...")
    meta = generate_meta_json()
    with open(RELEASE_DIR / 'meta.json', 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    print("   ✓ meta.json 已生成")

    # 生成 chapters.json
    print("\n2. 生成章节信息...")
    chapters = generate_chapters_json()
    with open(RELEASE_DIR / 'chapters.json', 'w', encoding='utf-8') as f:
        json.dump(chapters, f, ensure_ascii=False, indent=2)
    print("   ✓ chapters.json 已生成")

    # 生成 README.md
    print("\n3. 生成文档...")
    readme = generate_readme()
    with open(RELEASE_DIR / 'README.md', 'w', encoding='utf-8') as f:
        f.write(readme)
    print("   ✓ README.md 已生成")

    # 验证
    print("\n4. 验证发布包...")
    audio_files = list(AUDIO_DIR.glob('*.mp3'))
    print(f"   ✓ 音频文件: {len(audio_files)} 个")

    total_size = sum(f.stat().st_size for f in audio_files)
    print(f"   ✓ 总大小: {round(total_size / (1024 * 1024), 2)} MB")

    # 报告
    print("\n" + "=" * 60)
    print("打包完成！")
    print("=" * 60)
    print(f"\n发布目录: {RELEASE_DIR}")
    print(f"章节数: {len(audio_files)}")
    print(f"总大小: {round(total_size / (1024 * 1024), 2)} MB")
    print(f"总时长: {meta['audio']['total_duration_formatted']}")
    print("\n发布包已准备就绪，可以分发！")

if __name__ == "__main__":
    main()
