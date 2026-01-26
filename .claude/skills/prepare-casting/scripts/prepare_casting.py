#!/usr/bin/env python3
"""
角色配音准备脚本
识别小说中的角色并为每个角色分配合适的音色。
"""

import json
import re
import sys
from pathlib import Path
from collections import Counter
from typing import Dict, List, Set, Tuple


def load_voices(voices_file: str) -> List[Dict]:
    """加载可用音色列表"""
    with open(voices_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_chapters(chapters_file: str) -> Dict:
    """加载章节数据"""
    with open(chapters_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def extract_characters(chapters_data: Dict) -> Dict[str, Dict]:
    """
    从章节内容中提取角色

    识别规则：
    1. 对话模式："角色名说："、"角色名道："、"角色名问："等
    2. 统计每个角色的出现次数
    3. 识别主要角色和次要角色
    """
    characters = {}

    # 对话模式：匹配 "XXX说："、"XXX道："、"XXX问："等
    # 使用更严格的模式，确保动词紧跟在角色名后面，中间没有其他字
    dialogue_pattern = r'([^，。！？："""\n]{2,4})(说|道|问|答|喊|叫)[:：]'

    # 常见的非角色词和动词形容词
    exclude_words = {
        '他', '她', '它', '我', '你', '这', '那', '什么', '怎么', '谁', '哪',
        '小声', '大声', '轻声', '低声', '高声',
        '冷笑', '苦笑', '微笑', '大笑', '狂笑',
        '尴尬', '强撑', '淡淡', '刚要', '还没', '正要', '忽然',
        '地上', '天上', '心里', '眼里', '手里',
        '突然', '忽然', '立刻', '马上', '赶紧',
    }

    # 常见的动词和形容词后缀
    exclude_suffixes = ['地', '着', '了', '过', '起', '下', '出', '进', '回']

    for chapter in chapters_data['chapters']:
        content = chapter['content']
        chapter_id = chapter['chapter_id']

        # 提取对话中的角色名
        matches = re.findall(dialogue_pattern, content)
        for match in matches:
            char_name = match[0].strip()

            # 过滤规则
            # 1. 长度检查
            if len(char_name) < 2 or len(char_name) > 4:
                continue

            # 2. 排除常见非角色词
            if char_name in exclude_words:
                continue

            # 3. 排除包含动词形容词后缀的
            if any(char_name.endswith(suffix) for suffix in exclude_suffixes):
                continue

            # 4. 排除包含常见动词的
            if any(word in char_name for word in ['尴尬', '强撑', '淡淡', '刚要', '还没', '正要']):
                continue

            # 5. 只保留看起来像人名的（至少包含一个常见姓氏或名字字）
            # 常见姓氏
            common_surnames = '赵钱孙李周吴郑王冯陈褚卫蒋沈韩杨朱秦尤许何吕施张孔曹严华金魏陶姜戚谢邹喻柏水窦章云苏潘葛奚范彭郎鲁韦昌马苗凤花方俞任袁柳酆鲍史唐费廉岑薛雷贺倪汤滕殷罗毕郝邬安常乐于时傅皮卞齐康伍余元卜顾孟平黄和穆萧尹姚邵湛汪祁毛禹狄米贝明臧计伏成戴谈宋茅庞熊纪舒屈项祝董梁杜阮蓝闵席季麻强贾路娄危江童颜郭梅盛林刁钟徐邱骆高夏蔡田樊胡凌霍虞万支柯昝管卢莫经房裘缪干解应宗丁宣贲邓郁单杭洪包诸左石崔吉钮龚程嵇邢滑裴陆荣翁荀羊於惠甄麴家封芮羿储靳汲邴糜松井段富巫乌焦巴弓牧隗山谷车侯宓蓬全郗班仰秋仲伊宫宁仇栾暴甘钭厉戎祖武符刘景詹束龙叶幸司韶郜黎蓟薄印宿白怀蒲邰从鄂索咸籍赖卓蔺屠蒙池乔阴鬱胥能苍双闻莘党翟谭贡劳逄姬申扶堵冉宰郦雍郤璩桑桂濮牛寿通边扈燕冀郏浦尚农温别庄晏柴瞿阎充慕连茹习宦艾鱼容向古易慎戈廖庾终暨居衡步都耿满弘匡国文寇广禄阙东欧殳沃利蔚越夔隆师巩厍聂晁勾敖融冷訾辛阚那简饶空曾毋沙乜养鞠须丰巢关蒯相查后荆红游竺权逯盖益桓公'

            # 检查是否包含常见姓氏
            has_surname = any(char_name.startswith(surname) for surname in common_surnames)

            # 如果不包含常见姓氏，跳过（除非出现次数很多）
            if not has_surname:
                continue

            if char_name not in characters:
                characters[char_name] = {
                    'name': char_name,
                    'appearances': 0,
                    'first_chapter': chapter_id,
                    'chapters': set()
                }

            characters[char_name]['appearances'] += 1
            characters[char_name]['chapters'].add(chapter_id)

    # 转换 set 为 list 以便 JSON 序列化
    for char in characters.values():
        char['chapters'] = sorted(list(char['chapters']))
        char['chapter_count'] = len(char['chapters'])

    return characters


def classify_characters(characters: Dict[str, Dict]) -> Dict[str, List[str]]:
    """
    将角色分类为主角、配角、次要角色

    分类规则：
    - 主角：出现次数 > 50 或出现在 50% 以上章节
    - 配角：出现次数 > 20 或出现在 30% 以上章节
    - 次要角色：其他
    """
    total_chapters = max([char['chapter_count'] for char in characters.values()]) if characters else 1

    classification = {
        'protagonist': [],
        'supporting': [],
        'minor': []
    }

    for name, char in characters.items():
        appearances = char['appearances']
        chapter_ratio = char['chapter_count'] / total_chapters

        if appearances > 50 or chapter_ratio > 0.5:
            classification['protagonist'].append(name)
        elif appearances > 20 or chapter_ratio > 0.3:
            classification['supporting'].append(name)
        else:
            classification['minor'].append(name)

    return classification


def assign_voices(characters: Dict[str, Dict],
                 classification: Dict[str, List[str]],
                 voices: List[Dict]) -> List[Dict]:
    """
    为角色分配音色

    分配策略：
    1. 主角使用高质量音色（beta 版本）
    2. 根据角色名推测性别
    3. 确保主要角色使用不同的音色
    """
    # 按性别分类音色
    male_voices = []
    female_voices = []
    neutral_voices = []

    for voice in voices:
        voice_id = voice['voice_id']
        voice_name = voice['voice_name']

        # 跳过粤语和英语音色
        if 'Cantonese' in voice_id or 'English' in voice_id:
            continue

        # 根据音色名称判断性别
        if 'male' in voice_id.lower() or any(k in voice_name for k in ['男', '青年', '大爷', '弟弟', '学长', '少爷', '高管', '主播']):
            if '女' not in voice_name:  # 排除"女主播"等
                male_voices.append(voice)
        elif 'female' in voice_id.lower() or any(k in voice_name for k in ['女', '少女', '御姐', '学妹', '学姐', '闺蜜', '小姐', '大婶', '奶奶']):
            female_voices.append(voice)
        else:
            neutral_voices.append(voice)

    # 优先使用 beta 版本的音色给主角
    male_beta = [v for v in male_voices if 'jingpin' in v['voice_id'] or 'beta' in v['voice_name']]
    female_beta = [v for v in female_voices if 'jingpin' in v['voice_id'] or 'beta' in v['voice_name']]

    assignments = []
    used_voices = set()

    # 添加旁白
    narrator_voice = neutral_voices[0] if neutral_voices else male_voices[0]
    assignments.append({
        'character_id': 'narrator',
        'character_name': '旁白',
        'voice_id': narrator_voice['voice_id'],
        'voice_name': narrator_voice['voice_name'],
        'role': 'narrator'
    })
    used_voices.add(narrator_voice['voice_id'])

    # 为角色分配音色
    char_id = 1
    for role_type in ['protagonist', 'supporting', 'minor']:
        for char_name in classification[role_type]:
            char_data = characters[char_name]

            # 推测性别
            is_female = any(k in char_name for k in ['女', '妻', '母', '姐', '妹', '婶', '姨', '奶'])
            is_male = any(k in char_name for k in ['男', '父', '兄', '弟', '叔', '伯', '爷'])

            # 选择音色池
            if role_type == 'protagonist':
                voice_pool = female_beta if is_female else male_beta if is_male else male_beta + female_beta
            else:
                voice_pool = female_voices if is_female else male_voices if is_male else male_voices + female_voices

            # 选择未使用的音色
            selected_voice = None
            for voice in voice_pool:
                if voice['voice_id'] not in used_voices:
                    selected_voice = voice
                    used_voices.add(voice['voice_id'])
                    break

            # 如果所有音色都用完了，重新使用
            if not selected_voice:
                selected_voice = voice_pool[0] if voice_pool else male_voices[0]

            assignments.append({
                'character_id': f'char_{char_id:03d}',
                'character_name': char_name,
                'voice_id': selected_voice['voice_id'],
                'voice_name': selected_voice['voice_name'],
                'role': role_type,
                'appearances': char_data['appearances'],
                'chapter_count': char_data['chapter_count']
            })
            char_id += 1

    return assignments


def main():
    """主函数"""
    # 默认路径
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent.parent.parent.parent

    chapters_file = project_root / "source" / "01_extracted" / "chapters.json"
    voices_file = project_root / "configs" / "voices.json"
    output_dir = project_root / "source" / "02_casting"

    # 支持命令行参数
    if len(sys.argv) > 1:
        chapters_file = Path(sys.argv[1])
    if len(sys.argv) > 2:
        voices_file = Path(sys.argv[2])
    if len(sys.argv) > 3:
        output_dir = Path(sys.argv[3])

    try:
        # 加载数据
        print("正在加载章节数据...")
        chapters_data = load_chapters(str(chapters_file))

        print("正在加载音色列表...")
        voices = load_voices(str(voices_file))
        print(f"  - 可用音色: {len(voices)} 个")

        # 提取角色
        print("\n正在分析角色...")
        characters = extract_characters(chapters_data)
        print(f"  - 识别出角色: {len(characters)} 个")

        # 分类角色
        classification = classify_characters(characters)
        print(f"  - 主角: {len(classification['protagonist'])} 个")
        print(f"  - 配角: {len(classification['supporting'])} 个")
        print(f"  - 次要角色: {len(classification['minor'])} 个")

        # 分配音色
        print("\n正在分配音色...")
        assignments = assign_voices(characters, classification, voices)

        # 创建输出目录
        output_dir.mkdir(parents=True, exist_ok=True)

        # 保存角色列表
        character_list = {
            'total_characters': len(characters),
            'classification': classification,
            'characters': [
                {
                    'name': name,
                    **data
                }
                for name, data in sorted(characters.items(),
                                        key=lambda x: x[1]['appearances'],
                                        reverse=True)
            ]
        }

        character_list_file = output_dir / "character_list.json"
        with open(character_list_file, 'w', encoding='utf-8') as f:
            json.dump(character_list, f, ensure_ascii=False, indent=2)

        # 保存音色映射
        voice_mapping = {
            'total_assignments': len(assignments),
            'voice_assignments': assignments
        }

        voice_mapping_file = output_dir / "voice_mapping.json"
        with open(voice_mapping_file, 'w', encoding='utf-8') as f:
            json.dump(voice_mapping, f, ensure_ascii=False, indent=2)

        # 输出结果
        print("\n✓ 配音准备完成")
        print(f"  - 角色总数: {len(characters)}")
        print(f"  - 音色分配: {len(assignments)}")
        print(f"  - 角色列表: {character_list_file}")
        print(f"  - 音色映射: {voice_mapping_file}")

        # 显示主要角色的音色分配
        print("\n主要角色音色分配:")
        for assignment in assignments[:10]:  # 显示前10个
            print(f"  - {assignment['character_name']}: {assignment['voice_name']} ({assignment['voice_id']})")

        return 0

    except Exception as e:
        print(f"✗ 配音准备失败: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
