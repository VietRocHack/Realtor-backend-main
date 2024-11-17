from flask import Flask, jsonify
import cv2
import requests
import threading
import time
import os
import wave
import io

app = Flask(__name__)

# Global variables
recording = False
thread = None

# Camera settings
camera_ip = "http://192.168.137.37:8080"

def record_audio(filename, duration):
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
            break

    audio_data.seek(0)
    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(44100)
        wf.writeframes(audio_data.read())

def test_recording():
    print("Testing video and audio recording...")
    if not os.path.exists('recordings'):
        os.makedirs('recordings')

    # Test video recording
    cap = cv2.VideoCapture(f"{camera_ip}/video")
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter('recordings/test_video.mp4', fourcc, 15.0, (640, 480))

    start_time = time.time()
    while time.time() - start_time < 1:  # Record for 1 second
        ret, frame = cap.read()
        if ret:
            out.write(frame)
        else:
            print("Failed to capture frame from IP webcam")
            cap.release()
            out.release()
            return False

    cap.release()
    out.release()

    # Test audio recording
    try:
        record_audio('recordings/test_audio.wav', 1)
    except Exception as e:
        print(f"Failed to record audio: {str(e)}")
        return False

    print("Test recording completed successfully")
    return True

def record_video_audio():
    global recording
    cap = cv2.VideoCapture(f"{camera_ip}/video")

    if not os.path.exists('recordings'):
        os.makedirs('recordings')

    while recording:
        video_filename = f'recordings/video_{int(time.time())}.mp4'
        audio_filename = f'recordings/audio_{int(time.time())}.wav'

        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(video_filename, fourcc, 15.0, (640, 480))

        audio_thread = threading.Thread(target=record_audio, args=(audio_filename, 10))
        audio_thread.start()

        start_time = time.time()
        while time.time() - start_time < 10 and recording:
            ret, frame = cap.read()
            if ret:
                out.write(frame)
            else:
                break

        out.release()
        audio_thread.join()

    cap.release()

@app.route('/api/start_session', methods=['POST'])
def start_session():
    global recording, thread
    if not recording:
        recording = True
        thread = threading.Thread(target=record_video_audio)
        thread.start()
        return jsonify({"message": "Recording started"}), 200
    else:
        return jsonify({"message": "Recording is already in progress"}), 400

@app.route('/api/end_session', methods=['POST'])
def end_session():
    global recording, thread
    if recording:
        recording = False
        if thread:
            thread.join()
        return jsonify({"message": "Recording stopped"}), 200
    else:
        return jsonify({"message": "No recording in progress"}), 400

if __name__ == '__main__':
    if test_recording():
        print("Test recording successful. Starting the server...")
        app.run(debug=True)
    else:
        print("Test recording failed. Please check your IP webcam connection and try again.")

print("Script execution completed.")