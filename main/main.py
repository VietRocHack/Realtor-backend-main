from flask import Flask, jsonify
import cv2
import requests
import threading
import time
import os
import wave
import io
import dotenv
import os
from pinata_services import PinataService

dotenv.load_dotenv()

pinata_secret_key = os.getenv("PINATA_API_KEY")
pinata_jwt = os.getenv("PINATA_JWT")
pinata_gateway = os.getenv("PINATA_GATEWAY")

pinata_service = PinataService(pinata_secret_key, pinata_jwt, pinata_gateway)


app = Flask(__name__)

# Global variables
recording = False
thread = None

# Camera settings
camera_ip = "http://192.168.137.37:8080"

# Recording settings
FRAME_COUNT = 150
FPS = 15  # Set to 15 frames per second
DURATION = 10  # Total duration in seconds

# Pinata settings
group_id = "01933748-f918-7e94-8c17-7564581a5188"

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
            return False

    audio_data.seek(0)
    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(44100)
        wf.writeframes(audio_data.read())
    return True

def test_recording():
    print("Running recording test...")
    if not os.path.exists('test_recordings'):
        os.makedirs('test_recordings')

    # Test video recording
    cap = cv2.VideoCapture(f"{camera_ip}/video")
    if not cap.isOpened():
        print("Failed to open video stream")
        return False

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter('test_recordings/test_video.mp4', fourcc, FPS, (640, 480))

    frames_recorded = 0
    start_time = time.time()
    while frames_recorded < 15:  # Record 1 second of video
        ret, frame = cap.read()
        if not ret:
            print("Failed to capture frame")
            cap.release()
            out.release()
            return False
        out.write(frame)
        frames_recorded += 1

    cap.release()
    out.release()

    # Test audio recording
    if not record_audio('test_recordings/test_audio.wav', 1):
        print("Failed to record audio")
        return False

    print("Recording test completed successfully")
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
        out = cv2.VideoWriter(video_filename, fourcc, FPS, (640, 480))

        audio_thread = threading.Thread(target=record_audio, args=(audio_filename, DURATION))
        audio_thread.start()

        frames_recorded = 0
        start_time = time.time()
        while recording and frames_recorded < FRAME_COUNT:
            ret, frame = cap.read()
            if ret:
                out.write(frame)
                frames_recorded += 1
                
                elapsed_time = time.time() - start_time
                expected_time = frames_recorded / FPS
                if elapsed_time < expected_time:
                    time.sleep(expected_time - elapsed_time)
            else:
                break

        out.release()
        audio_thread.join()

        print(f"Recording stopped after {frames_recorded} frames and {time.time() - start_time:.2f} seconds")

        # Upload video and audio to Pinata
        with open(video_filename, 'rb') as video_file:
            video_cid = pinata_service.upload_file_to_group(group_id, os.path.basename(video_filename), video_file.read())
        
        with open(audio_filename, 'rb') as audio_file:
            audio_cid = pinata_service.upload_file_to_group(group_id, os.path.basename(audio_filename), audio_file.read())

        print(f"Video ID (CID): {video_cid}")
        print(f"Audio ID (CID): {audio_cid}")

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
        exit(1)

print("Script execution completed.")