# Audiobook Production Workflow

## Overview
Complete workflow for converting Markdown novels into professional multi-character audiobooks using Claude Code skills.

## Prerequisites
- Claude Code CLI installed
- OpenAI API key set in environment: `export OPENAI_API_KEY=your_key`
- ffmpeg installed for audio processing
- Input novel file at `input/source.md`

## Workflow Steps

### Step 1: Extract Chapters
Extract chapter structure from source Markdown file.

```bash
# Invoke the extract-chapters skill
claude-code /extract-chapters
```

**Output**: `build/01_extracted/chapters.json`

**Verify**: Check that all chapters are extracted correctly
```bash
cat build/01_extracted/chapters.json | jq '.total_chapters'
```

---

### Step 2: Prepare Casting
Identify characters and assign voices.

```bash
# Invoke the prepare-casting skill
claude-code /prepare-casting
```

**Output**:
- `build/02_casting/character_list.json`
- `build/02_casting/voice_mapping.json`

**Verify**: Review character-to-voice assignments
```bash
cat build/02_casting/voice_mapping.json | jq '.voice_assignments'
```

**Manual Review**: Adjust voice assignments if needed

---

### Step 3: Attribute Dialogue
Analyze content and attribute each line to the correct speaker.

```bash
# Invoke the attribute-dialogue skill
claude-code /attribute-dialogue
```

**Output**: `build/03_segmentation/attributed_chapters.json`

**Verify**: Check attribution confidence
```bash
cat build/03_segmentation/attributed_chapters.json | jq '.chapters[0].segments[0]'
```

---

### Step 4: Split Scenes
Divide chapters into logical scenes.

```bash
# Invoke the split-scenes skill
claude-code /split-scenes
```

**Output**: `build/03_segmentation/scenes.json`

**Verify**: Review scene boundaries
```bash
cat build/03_segmentation/scenes.json | jq '.chapters[0].scenes | length'
```

---

### Step 5: Build Segments
Create TTS-ready segments with 75-second duration constraint.

```bash
# Invoke the build-segments skill
claude-code /build-segments
```

**Output**:
- `build/03_segmentation/tts_segments.json`
- `build/03_segmentation/segment_manifest.json`

**Verify**: Check segment statistics
```bash
cat build/03_segmentation/segment_manifest.json | jq '.total_segments'
```

---

### Step 6: Generate TTS Audio
Generate audio files using OpenAI TTS API.

```bash
# Ensure API key is set
echo $OPENAI_API_KEY

# Invoke the generate-tts-audio skill
claude-code /generate-tts-audio
```

**Output**:
- `build/04_tts_raw/*.wav`
- `build/04_tts_raw/generation_log.json`

**Verify**: Check generation success rate
```bash
cat build/04_tts_raw/generation_log.json | jq '.successful, .failed'
```

**Retry Failed**: If any segments failed, retry them
```bash
# Review failed segments
cat build/04_tts_raw/failed_segments.json

# Retry with the skill (it will skip successful ones)
claude-code /generate-tts-audio --retry-failed
```

---

### Step 7: Postprocess Audio
Apply professional audio processing and create chapter MP3s.

```bash
# Invoke the postprocess-audio skill
claude-code /postprocess-audio
```

**Output**:
- `build/05_post/segments/*.mp3`
- `build/05_post/chapters/*.mp3`
- `build/05_post/processing_log.json`

**Verify**: Check audio quality
```bash
# Check loudness levels
cat build/05_post/processing_log.json | jq '.processing_stats.average_loudness_lufs'

# Test play a chapter
ffplay build/05_post/chapters/ch_001.mp3
```

---

### Step 8: Package Release
Create final release package with metadata.

```bash
# Invoke the package-release skill
claude-code /package-release

# Optional: Create full book audio
claude-code /package-release --full-book
```

**Output**:
- `release/audio/chapters/*.mp3`
- `release/audio/full_book.mp3` (optional)
- `release/meta.json`
- `release/chapters.json`
- `release/README.md`

**Verify**: Check release package
```bash
ls -lh release/audio/chapters/
cat release/meta.json | jq '.audio.total_duration_formatted'
```

---

## Complete Pipeline (One Command)

To run the entire pipeline sequentially:

```bash
# Run all steps
claude-code /extract-chapters && \
claude-code /prepare-casting && \
claude-code /attribute-dialogue && \
claude-code /split-scenes && \
claude-code /build-segments && \
claude-code /generate-tts-audio && \
claude-code /postprocess-audio && \
claude-code /package-release
```

---

## Partial Re-runs

The pipeline supports re-running individual steps:

### Re-generate specific chapters
```bash
# Regenerate chapter 3 TTS
claude-code /generate-tts-audio --chapter ch_003

# Reprocess chapter 3 audio
claude-code /postprocess-audio --chapter ch_003
```

### Update voice assignments
```bash
# Edit voice mapping
vim build/02_casting/voice_mapping.json

# Regenerate from TTS step
claude-code /generate-tts-audio && \
claude-code /postprocess-audio && \
claude-code /package-release
```

---

## Troubleshooting

### Issue: API Rate Limiting
```bash
# Check failed segments
cat build/04_tts_raw/failed_segments.json

# Wait and retry
sleep 60
claude-code /generate-tts-audio --retry-failed
```

### Issue: Audio Quality Problems
```bash
# Check processing log
cat build/05_post/processing_log.json | jq '.processing_stats'

# Adjust config and reprocess
vim config/default_config.json
claude-code /postprocess-audio --force
```

### Issue: Character Attribution Errors
```bash
# Review attributed chapters
cat build/03_segmentation/attributed_chapters.json | jq '.chapters[0].segments[0:5]'

# Manually fix and continue from build-segments
vim build/03_segmentation/attributed_chapters.json
claude-code /build-segments && \
claude-code /generate-tts-audio && \
claude-code /postprocess-audio && \
claude-code /package-release
```

---

## Project Structure

```
audiobook_project/
├── input/
│   └── source.md                    # Input novel
├── config/
│   ├── default_config.json          # Main configuration
│   └── casting_config.json          # Voice assignments
├── build/
│   ├── 01_extracted/
│   │   └── chapters.json
│   ├── 02_casting/
│   │   ├── character_list.json
│   │   └── voice_mapping.json
│   ├── 03_segmentation/
│   │   ├── attributed_chapters.json
│   │   ├── scenes.json
│   │   ├── tts_segments.json
│   │   └── segment_manifest.json
│   ├── 04_tts_raw/
│   │   ├── *.wav
│   │   ├── generation_log.json
│   │   └── failed_segments.json
│   └── 05_post/
│       ├── segments/*.mp3
│       ├── chapters/*.mp3
│       └── processing_log.json
├── release/
│   ├── audio/
│   │   ├── chapters/*.mp3
│   │   └── full_book.mp3
│   ├── meta.json
│   ├── chapters.json
│   └── README.md
└── skills/
    ├── extract-chapters.md
    ├── prepare-casting.md
    ├── attribute-dialogue.md
    ├── split-scenes.md
    ├── build-segments.md
    ├── generate-tts-audio.md
    ├── postprocess-audio.md
    └── package-release.md
```

---

## Maintenance & Upgrades

### Update TTS Provider
Edit `config/default_config.json`:
```json
{
  "tts": {
    "provider": "elevenlabs",
    "model": "eleven_multilingual_v2"
  }
}
```

Then update the generate-tts-audio skill accordingly.

### Add SSML Support
Enhance build-segments skill to generate SSML markup for better prosody control.

### Implement Sentence-Level Emotions
Upgrade attribute-dialogue skill to detect emotions at sentence level instead of segment level.

---

## Cost Estimation

### OpenAI TTS Pricing (as of 2026)
- Model: gpt-4o-mini-tts
- Cost: ~$0.015 per 1000 characters

### Example Calculation
- Novel: 25,000 words ≈ 150,000 characters
- Estimated cost: $2.25

---

## Quality Checklist

Before final release:
- [ ] All chapters extracted correctly
- [ ] Character voices are distinct and appropriate
- [ ] Dialogue attribution is accurate
- [ ] No audio clipping or distortion
- [ ] Loudness normalized to -18 LUFS
- [ ] Chapter transitions are smooth
- [ ] Metadata is complete and accurate
- [ ] README is informative
- [ ] All files are playable

---

## Next Steps

1. Place your novel at `input/source.md`
2. Set your OpenAI API key: `export OPENAI_API_KEY=your_key`
3. Run the complete pipeline
4. Review and adjust as needed
5. Distribute your audiobook!
