import json
import re
import sys
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path

from faster_whisper import WhisperModel


ASS_HEADER = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Montserrat SemiBold,57,&H00FFFFFF,&H000000FF,&H00000000,&H8C000000,1,0,0,0,100,100,0,0,3,3,0,2,57,57,198,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def normalize(value: str) -> str:
    value = unicodedata.normalize("NFKD", value.lower())
    value = "".join(character for character in value if not unicodedata.combining(character))
    return re.sub(r"[^a-z0-9]+", " ", value).strip()


def fmt_time(seconds: float) -> str:
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    whole = int(seconds % 60)
    centiseconds = int(round((seconds - int(seconds)) * 100))
    return f"{hours}:{minutes:02d}:{whole:02d}.{centiseconds:02d}"


def wrap_caption(value: str, max_chars=30) -> str:
    words = value.split()
    lines = []
    current = ""
    for word in words:
        candidate = word if not current else f"{current} {word}"
        if len(candidate) <= max_chars:
            current = candidate
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return r"\N".join(lines)


def transcribe_words(audio_path: str, model_name: str = "base"):
    model = WhisperModel(model_name, device="cpu", compute_type="int8")
    segments, _ = model.transcribe(
        audio_path,
        language="vi",
        vad_filter=True,
        word_timestamps=True,
        beam_size=5,
    )
    words = []
    transcript = []
    for segment in segments:
        transcript.append(segment.text.strip())
        for word in segment.words or []:
            token = normalize(word.word)
            if token:
                words.append({
                    "token": token,
                    "raw": word.word.strip(),
                    "start": float(word.start),
                    "end": float(word.end),
                })
    return words, " ".join(transcript)


def align_phrases(words, phrases):
    aligned = []
    cursor = 0
    previous_end = 0.0
    for phrase in phrases:
        target_tokens = normalize(phrase["spoken"]).split()
        target_text = " ".join(target_tokens)
        expected = len(target_tokens)
        best_start = cursor
        best_end = min(len(words), cursor + expected)
        best_score = -1.0
        max_start = min(len(words) - 1, cursor + 14)
        for candidate_start in range(cursor, max_start + 1):
            min_end = min(len(words), candidate_start + max(1, expected - 8))
            max_end = min(len(words), candidate_start + expected + 10)
            for candidate_end in range(min_end, max_end + 1):
                candidate_text = " ".join(word["token"] for word in words[candidate_start:candidate_end])
                score = SequenceMatcher(None, target_text, candidate_text).ratio()
                if score > best_score:
                    best_score = score
                    best_start = candidate_start
                    best_end = candidate_end
        if cursor >= len(words) or best_end <= best_start:
            raise RuntimeError(f"Could not align phrase: {phrase['display']}")
        start = max(words[best_start]["start"], previous_end + 0.07)
        end = max(start + 0.45, words[best_end - 1]["end"] - 0.07)
        aligned.append({
            "start": round(start, 3),
            "end": round(end, 3),
            "text": phrase["display"],
            "match_score": round(best_score, 3),
        })
        previous_end = end
        cursor = best_end
    return aligned


def write_ass(aligned, output_path: str):
    lines = [ASS_HEADER]
    for item in aligned:
        text = wrap_caption(item["text"])
        lines.append(
            f"Dialogue: 0,{fmt_time(item['start'])},{fmt_time(item['end'])},"
            f"Default,,0,0,0,,{text}"
        )
    Path(output_path).write_text("\n".join(lines), encoding="utf-8")


def main():
    audio_path = sys.argv[1]
    phrase_path = sys.argv[2]
    output_json = sys.argv[3]
    output_ass = sys.argv[4]
    raw_output = sys.argv[5]
    model_name = sys.argv[6] if len(sys.argv) > 6 else "base"
    phrases = json.loads(Path(phrase_path).read_text(encoding="utf-8"))
    words, transcript = transcribe_words(audio_path, model_name)
    Path(raw_output).write_text(transcript, encoding="utf-8")
    aligned = align_phrases(words, phrases)
    Path(output_json).write_text(json.dumps(aligned, ensure_ascii=False, indent=2), encoding="utf-8")
    write_ass(aligned, output_ass)
    print(f"Aligned {len(aligned)} subtitle phrases")
    print(f"Minimum match score: {min(item['match_score'] for item in aligned):.3f}")


if __name__ == "__main__":
    main()
