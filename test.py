import ffmpeg

from video_creation.final_video import ProgressFfmpeg

srt_file = f'assets/temp/test/subtitles.srt'
srt_style = 'Fontname=Caveat Brush,FontSize=32,PrimaryColour=&HFF0000,OutlineColour=&H0,Alignment=10,Shadow=5'

background_clip = f'assets/temp/test/background_noaudio.mp4'
final_audio = f'assets/temp/test/audio.mp3'
path = f'assets/temp/test/test.mp4'
background_clip = ffmpeg.input(background_clip)
final_audio = ffmpeg.input(final_audio)
from tqdm import tqdm

pbar = tqdm(total=100, desc="Progress: ", bar_format="{l_bar}{bar}", unit=" %")
def on_update_example(progress) -> None:
        status = round(progress * 100, 2)
        old_percentage = pbar.n
        pbar.update(status - old_percentage)
print('Making video...')
pixel_format = "yuva420p"  # Choose a single format
total_duration = 5  # Total video duration (seconds)
fade_duration = 0.5  # Fade-out duration (seconds)

with ProgressFfmpeg(50, on_update_example) as progress:# Prevent a error by limiting the path length, do not change this.
        try:
          # Process the image (scale, format, etc.)
          image_clip = (
              ffmpeg.input(
                  "assets/temp/ibud0x/png/title.png",
                  loop=1,
                  framerate=60,
                  t=total_duration  # Total duration of the image display
              )["v"]
              .filter("scale", 1080, -1)  # Scale to width=1080, auto height
              .filter("format", "yuva420p")  # Ensure transparency support
          )
          background = ffmpeg.input("color=black:s=1080x1920", f="lavfi", t=total_duration)["v"]
          video = background.overlay(
                image_clip,
                enable=f"between(t,0,{total_duration})",
                x="(main_w-overlay_w)/2",
                y="(main_h-overlay_h)/2"
            ).filter("fade", type="out", start_time=total_duration - fade_duration, duration=fade_duration)

# Output the video
          output = (
              ffmpeg.output(
                  video,
                  path,
                  f="mp4",
                  **{
                      "c:v": "h264_nvenc",
                      "b:v": "20M",
                      # Remove "b:a" since there's no audio
                  },
              )
              .overwrite_output()
              .global_args("-progress", progress.output_file.name)
              .run(quiet=True, overwrite_output=True)
          )
        except ffmpeg.Error as e:
            print(e.stderr.decode("utf8"))
            exit(1)