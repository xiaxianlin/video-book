#!/bin/bash
# TTS 生成进度监控脚本

echo "TTS 音频生成进度监控"
echo "===================="
echo ""

while true; do
    # 统计已生成的文件数
    generated=$(ls source/04_tts_raw/*.wav 2>/dev/null | wc -l | tr -d ' ')
    total=542

    # 计算进度百分比
    if [ "$generated" -gt 0 ]; then
        percentage=$((generated * 100 / total))
    else
        percentage=0
    fi

    # 显示进度
    echo -ne "\r已生成: $generated/$total ($percentage%)  "

    # 如果完成，退出
    if [ "$generated" -eq "$total" ]; then
        echo ""
        echo "✓ 生成完成！"
        break
    fi

    # 等待 10 秒
    sleep 10
done
