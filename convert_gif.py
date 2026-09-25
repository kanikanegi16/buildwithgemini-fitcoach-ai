# convert_gif.py
import imageio_ffmpeg
import subprocess
import os

ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
input_file = "/config/Desktop/Session1/agent_demo.webm"
output_gif = "/config/Desktop/Session1/fitcoach-ai/agent_demo.gif"

if os.path.exists(input_file):
    print(f"Converting {input_file} to optimized GIF...")
    cmd = [
        ffmpeg_exe,
        "-y",
        "-i", input_file,
        "-vf", "fps=10,scale=800:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse",
        "-loop", "0",
        output_gif
    ]
    subprocess.run(cmd, check=True)
    print(f"SUCCESS: Created optimized looping GIF at {output_gif}")
else:
    print(f"Input file {input_file} not found yet.")
