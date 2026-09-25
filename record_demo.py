# record_demo.py
import asyncio
import os
import shutil
import numpy as np
from scipy.io import wavfile
from moviepy import VideoFileClip, AudioFileClip

def generate_lofi_audio(duration_sec=30, sample_rate=44100, filename="lofi_track.wav"):
    """Generates an upbeat lo-fi background track with a smooth chord progression and rhythm beat."""
    t = np.linspace(0, duration_sec, int(sample_rate * duration_sec), False)
    
    # 80 BPM tempo
    bpm = 80
    beat_dur = 60 / bpm
    
    # Smooth lo-fi chord progression (Cmaj7 -> Am7 -> Fmaj7 -> G7)
    chords = [
        [261.63, 329.63, 392.00, 493.88], # Cmaj7
        [220.00, 261.63, 329.63, 392.00], # Am7
        [174.61, 220.00, 261.63, 329.63], # Fmaj7
        [196.00, 246.94, 293.66, 349.23], # G7
    ]
    
    chord_dur = beat_dur * 4
    audio = np.zeros_like(t)
    
    # Synthesize chords
    for i, chord in enumerate(chords):
        chord_start = i * chord_dur
        for cycle in range(int(duration_sec / (chord_dur * len(chords))) + 1):
            start = chord_start + cycle * (chord_dur * len(chords))
            end = start + chord_dur
            mask = (t >= start) & (t < end)
            if not np.any(mask):
                continue
            sub_t = t[mask] - start
            env = np.sin(np.pi * sub_t / chord_dur) ** 0.5
            for freq in chord:
                audio[mask] += 0.08 * np.sin(2 * np.pi * freq * sub_t) * env
                
    # Add upbeat lofi kick & snare drum rhythm
    total_beats = int(duration_sec / beat_dur)
    for beat in range(total_beats):
        beat_time = beat * beat_dur
        mask = (t >= beat_time) & (t < beat_time + 0.15)
        if not np.any(mask):
            continue
        sub_t = t[mask] - beat_time
        
        # Kick on beat 0, 2
        if beat % 2 == 0:
            kick_freq = 60 * np.exp(-sub_t * 30)
            kick = 0.25 * np.sin(2 * np.pi * kick_freq * sub_t) * np.exp(-sub_t * 15)
            audio[mask] += kick
            
        # Snare/rim on beat 1, 3
        if beat % 2 == 1:
            snare_noise = (np.random.rand(len(sub_t)) - 0.5) * 0.12 * np.exp(-sub_t * 20)
            audio[mask] += snare_noise
            
    # Normalize audio
    audio = audio / (np.max(np.abs(audio)) + 1e-5)
    audio_int16 = (audio * 0.7 * 32767).astype(np.int16)
    wavfile.write(filename, sample_rate, audio_int16)
    print(f"Generated audio track: {filename}")
    return filename


async def main():
    from playwright.async_api import async_playwright
    
    output_dir = "recordings"
    os.makedirs(output_dir, exist_ok=True)
    
    print("Launching browser recording...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            record_video_dir=output_dir,
            record_video_size={"width": 1280, "height": 720},
            viewport={"width": 1280, "height": 720}
        )
        
        page = await context.new_page()
        print("Navigating to FitCoach AI frontend...")
        await page.goto("http://localhost:8080/index.html")
        await page.wait_for_timeout(2000)
        
        # Request 1: "Suggest a quick leg workout routine"
        print("Sending prompt 1: Suggest a quick leg workout routine")
        await page.fill("#input", "Suggest a quick leg workout routine")
        await page.wait_for_timeout(1000)
        await page.click("button[type='submit']")
        
        # Wait for agent response
        await page.wait_for_timeout(8000)
        
        # Request 2: "Generate a concept image for the Trail Runner X shoes"
        print("Sending prompt 2: Generate a concept image for the Trail Runner X shoes")
        await page.fill("#input", "Generate a concept image for the Trail Runner X shoes")
        await page.wait_for_timeout(1000)
        await page.click("button[type='submit']")
        
        # Wait for image generation and card rendering
        await page.wait_for_timeout(12000)
        
        # Save video file
        video = page.video
        await context.close()
        await browser.close()
        
        raw_video_path = await video.path()
        print(f"Recorded raw video to: {raw_video_path}")
        
        # Generate upbeat lofi audio track
        audio_file = generate_lofi_audio(duration_sec=30)
        
        # Merge video and upbeat lofi audio using moviepy
        print("Merging video and upbeat lo-fi audio track...")
        video_clip = VideoFileClip(raw_video_path)
        audio_clip = AudioFileClip(audio_file).subclipped(0, min(video_clip.duration, 30))
        
        final_clip = video_clip.with_audio(audio_clip)
        final_output = "demo_fitcoach_ai.mp4"
        final_clip.write_videofile(final_output, codec="libx264", audio_codec="aac")
        print(f"SUCCESS: Created final demo video at {final_output}")

if __name__ == "__main__":
    asyncio.run(main())
