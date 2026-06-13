# Voices

This folder holds the reference audio used for **voice cloning** (optional).

Voice cloning pins an exact narrator by giving OmniVoice a short reference clip
plus its transcript. It usually sounds more natural (and more stable day to day)
than the tag-based "voice design" default.

## How to add a cloning reference

1. Record a clean **20-40 second** clip of a single speaker (yourself, or audio
   you are licensed to use) and save it here, e.g. `voices/narrator.wav`.
   You can extract + transcribe one from a longer file with:

   ```bash
   python scripts/extract_clone_ref.py SOURCE.mp3 START_SEC DURATION_SEC narrator
   ```

   That writes `voices/narrator.wav` and `voices/narrator.txt` (the transcript).

2. Point the TTS engine at it in `config.yaml`:

   ```yaml
   tts:
     omnivoice:
       ref_audio: "voices/narrator.wav"
       ref_text: ""        # empty -> read the transcript from voices/narrator.txt
   ```

The audio files (`*.wav`, `*.mp3`) and their `*.txt` transcripts are personal and
git-ignored, so they never end up in the repository.
