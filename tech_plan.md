
# 小说 Markdown → C 档多角色有声书
## 全流程技术方案（Claude Code 工作流）

版本：v1.0

---

## 1. 总体目标

将 Markdown 小说，通过可复现、可重跑、可审计的 Claude Code 工作流，生成 **多角色、克制风格** 的专业级有声书音频资产。

输出包括：
- 章节级 MP3
- 可选全书合并 MP3
- 完整元数据与发布目录

---

## 2. 输入与输出

### 输入
- `input/source.md` 小说正文（Markdown）
- 明确的角色名单
- 配音与情绪规则配置

### 最终输出
```
release/
  meta.json
  chapters.json
  audio/
    chapters/
      ch_001.mp3
      ch_002.mp3
    full_book.mp3 (可选)
```

---

## 3. 项目目录规范

```
audiobook_project/
├─ input/
├─ config/
├─ build/
│  ├─ 01_extracted/
│  ├─ 02_casting/
│  ├─ 03_segmentation/
│  ├─ 04_tts_raw/
│  └─ 05_post/
└─ release/
```

---

## 4. 全流程步骤

1. extract_chapters（章节抽取）
2. prepare_casting（角色与音色映射）
3. attribute_dialogue（对白归属）
4. split_scenes（场景拆分）
5. build_segments（Segment 构建，75 秒，严格分离）
6. generate_tts_audio（OpenAI 云 TTS）
7. postprocess_audio（合并、响度、压制）
8. package_release（发布打包）

---

## 5. Segment 策略（已定）

- 目标时长：75 秒
- 严格分离：一个 Segment 只允许一个 speaker
- 情绪存在但强度 low（克制）

---

## 6. 云 TTS（OpenAI）

- 接口：/v1/audio/speech
- 模型：gpt-4o-mini-tts
- 输出：WAV → 后处理 → MP3
- 支持幂等、重试、失败清单

---

## 7. 音频后处理标准

- 段首静音：200ms
- 段尾静音：300ms
- 章节响度：-18 LUFS
- True Peak：-1.0 dBTP
- MP3：Mono / 192kbps

---

## 8. 发布与维护

- 所有步骤均可按 chapter / scene / segment 重跑
- 可替换 TTS Provider
- 可升级 SSML / 句级情绪
- 可接入平台上传 API

---

## 9. 结语

本方案是一条 **长期可维护、可扩展的有声书生产流水线**，适用于个人作者与自动化内容生产。
