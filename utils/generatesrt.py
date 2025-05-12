from datetime import timedelta
from forcealign import ForceAlign

def generate_srt(transcript, audiofile):
  align = ForceAlign(audio_file=audiofile, transcript=transcript)
  words = align.inference()
  return convert_objects_to_srt(words)

def to_srt_time(seconds: float) -> str:
    td = timedelta(seconds=seconds)
    total_seconds = int(td.total_seconds())
    millis = int((seconds - total_seconds) * 1000)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    return f"{hours:02}:{minutes:02}:{secs:02},{millis:03}"

def convert_objects_to_srt(words: list) -> str:
    srt_lines = []

    for idx, element in enumerate(words):
        # I: 0.0 -- 0.56(s)
        getword = str(element).split(':', 1)
        timings = getword[1].split(' ', 3)
        endtime = timings[3].split('(', 1)
        start_time = to_srt_time(float(str(timings[1])))
        end_time = to_srt_time(float(str(endtime[0])))

        srt_lines.append(f"{idx}\n{start_time} --> {end_time}\n{str(getword[0]).lower()}\n")

    return "\n".join(srt_lines)
