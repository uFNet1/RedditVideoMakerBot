from pydub import AudioSegment
from pydub.effects import speedup
def change_pitch(path):
  audio = AudioSegment.from_file(path)
  new_sample_rate = int(audio.frame_rate * (2.0 ** (-2 / 12.0)))
  pitched = audio._spawn(audio.raw_data, overrides={'frame_rate': new_sample_rate}).set_frame_rate(audio.frame_rate)
  pitched = speedup(pitched, playback_speed=1.5)
  pitched.export(path, format='mp3')