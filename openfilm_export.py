"""Isolated offline OpenFilm exporter for already prepared montage plans. No Hermes."""
import argparse
import json
import math
import shutil
from pathlib import Path


def number(v):
    try:
        n = float(v)
    except (TypeError, ValueError):
        raise ValueError("Invalid timestamp")
    if not math.isfinite(n) or n < 0:
        raise ValueError("Invalid timestamp")
    return n


def vtt_time(s):
    m = round(s * 1000)
    h, m = divmod(m, 3600000)
    mi, m = divmod(m, 60000)
    sec, ms = divmod(m, 1000)
    return f"{h:02}:{mi:02}:{sec:02}.{ms:03}"


def export(plan, destination):
    if not isinstance(plan, dict):
        raise ValueError("Plan must be object")
    src = Path(plan['video']).expanduser().resolve()
    if src.suffix.lower() not in ('.mp4', '.mov', '.webm') or not src.is_file():
        raise ValueError("Video must be existing MP4, MOV, or WebM")
    start, end = number(plan.get('start', 0)), number(plan['end'])
    if end <= start or end - start > 1200:
        raise ValueError("Clip range must be positive and <= 1200s")
    fit = plan.get('fit', 'contain')
    if fit not in ('contain', 'cover'):
        raise ValueError("Unsupported fit")
    cues = plan.get('captions', [])
    if not isinstance(cues, list) or len(cues) > 120:
        raise ValueError("Invalid captions")
    if cues and plan.get('captions_reviewed') is not True:
        raise ValueError("Caption timings not reviewed")
    intervals, previous = [], 0.0
    for cue in cues:
        a, b = number(cue['start']), number(cue['end'])
        text = cue['text']
        if not isinstance(text, str) or not text.strip() or len(text) > 300:
            raise ValueError("Invalid caption")
        if a < previous - 0.00001 or b <= a or b > end - start + 0.005:
            raise ValueError("Invalid caption timestamps")
        intervals.append((a, b, text.strip()))
        previous = b
    voice = plan.get('voice')
    if voice:
        voice = Path(voice).expanduser().resolve()
        if not voice.is_file() or voice.suffix.lower() not in ('.wav', '.mp3', '.m4a'):
            raise ValueError("Voice must be WAV/MP3/M4A")
    out = Path(destination).expanduser().resolve()
    if out.exists() and (not out.is_dir() or any(out.iterdir())):
        raise FileExistsError("Nonempty destination: user edits are protected")
    media = out / 'assets'
    media.mkdir(parents=True)
    shutil.copy2(src, media / ('source' + src.suffix.lower()))
    voice_track = ''
    if voice:
        filename = 'voice' + voice.suffix.lower()
        shutil.copy2(voice, media / filename)
        voice_track = '<section><audio id="voice" src="assets/' + filename + '#t=0,' + f'{end-start:.3f}' + '"></audio></section>'
    if intervals:
        origin = 0 if voice else start
        lines = ['WEBVTT', '']
        for a, b, sentence in intervals:
            lines += [vtt_time(origin+a) + ' --> ' + vtt_time(origin+b), sentence, '']
        (media / ('voice.vtt' if voice else 'source.vtt')).write_text('\n'.join(lines), encoding='utf-8')
    muted = ' volume="0"' if voice else ''
    doc = ('<!doctype html><html lang="ru"><head><meta charset="utf-8">'
           '<meta name="viewport" content="width=1080, height=1920"></head><body>'
           '<section><video id="main" src="assets/source' + src.suffix.lower() +
           f'#t={start:.3f},{end:.3f}"' + muted +
           ' style="left:0px;top:0px;width:1080px;height:1920px;object-fit:' +
           fit + ';"></video></section>' + voice_track + '</body></html>\n')
    (out / 'film.html').write_text(doc, encoding='utf-8')
    manifest = {'format': 'reels-openfilm-pilot-v1', 'duration': end-start,
                'captions': len(intervals), 'voice': bool(voice),
                'source': 'independent montage input, no semantic generation',
                'publication': 'never automatic'}
    (out / 'export.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return out


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    print(export(json.loads(Path(args.plan).read_text(encoding='utf-8')), args.out))
