from forcealign import ForceAlign
import textwrap

def to_ass_time(seconds: float) -> str:
    """
    Convert a float number of seconds to ASS timestamp H:MM:SS.CS (centiseconds).
    """
    # total centiseconds
    cs_total = int(round(seconds * 100))
    hours, rem_cs = divmod(cs_total, 3600 * 100)
    minutes, rem_cs = divmod(rem_cs, 60 * 100)
    secs, centis = divmod(rem_cs, 100)
    return f"{hours:d}:{minutes:02d}:{secs:02d}.{centis:02d}"

def convert_objects_to_ass(words: list, offset: float) -> str:
    header = textwrap.dedent(r"""[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
Timer: 100.0000

[V4+ Styles]
Format: Alignment, Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour,\
Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow,\
MarginL, MarginR, MarginV, Encoding
Style: 5, Default,Playpen Sans Bold,128,&H03FFFFFF,&H00000000,&H03000000,&H4D000000,\
0,0,0,0,100,100,0,0,1,2,4,10,10,10,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
""")

    events = []
    for idx, element in enumerate(words):

        # str(element) looks like "WORD: 1.23 -- 2.34(s)"
        raw = str(element)
        word_text, rest = raw.split(":", 1)
        parts = rest.strip().split()
        # parts[0] is start time string, parts[2] is end time plus "(s)"
        start_s = float(parts[0])
        end_s   = float(parts[2].split("(")[0])
        start_s += offset
        end_s += offset
            
        # Convert floats -> ASS timestamps just once
        t0 = to_ass_time(start_s)
        t1 = to_ass_time(end_s)

        # ASS per-line override:
        #  \fad(200,200)      fade in/out 100ms
        #  \fs32              enforce 32pt
        #  \fscx120\fscy120   start at 110% scale
        #  \t(0,200,...)      tween back to 100% in first 100ms
        ovl = r"{\shad4\bord8\blur1\fad(50,50)\fscx110\fscy110\t(0,100,\fscx100,\fscy100)}"

        events.append(f"Dialogue: 0,{t0},{t1},Default,,0,0,0,,{ovl}{word_text.lower()}")

    return header + '\n' + "\n".join(events)

def generate_ass(transcript_path: str, audiofile: str, ass_path="output.ass", offset=0.0):
    align = ForceAlign(audio_file=audiofile, transcript=transcript_path)
    words = align.inference()
    ass_data = convert_objects_to_ass(words, offset)
    with open(ass_path, "w", encoding="utf-8") as f:
        f.write(ass_data)
    print(f"Wrote ASS subtitles to {ass_path}")

# Usage:
# generate_ass("mytranscript.txt", "myspeech.wav", "subtitles.ass")
# generate_ass(f'assets/testing/transcript.txt')