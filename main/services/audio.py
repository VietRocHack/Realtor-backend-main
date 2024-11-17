import requests
import wave
import io
import time

def record_audio(camera_ip, filename, duration):
    audio_url = f"{camera_ip}/audio.wav"
    start_time = time.time()
    audio_data = io.BytesIO()

    while time.time() - start_time < duration:
        try:
            response = requests.get(audio_url, stream=True, timeout=1)
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    audio_data.write(chunk)
                if time.time() - start_time >= duration:
                    break
        except requests.RequestException as e:
            print(f"Error streaming audio: {str(e)}")
            return False

    audio_data.seek(0)
    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(44100)
        wf.writeframes(audio_data.read())
    return True

def test_audio_recording(camera_ip, filename, duration=1):
    print("Testing audio recording...")
    if record_audio(camera_ip, filename, duration):
        print("Audio recording test completed successfully")
        return True
    else:
        print("Failed to record audio")
        return False