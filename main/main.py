from flask import Flask, jsonify
import threading
import time
import os
import dotenv
import requests
from services.pinata_services import PinataService
from services.audio import record_audio, test_audio_recording
from services.video import record_video, test_video_recording

dotenv.load_dotenv()

# Pinata settings
pinata_secret_key = os.getenv("PINATA_API_KEY")
pinata_jwt = os.getenv("PINATA_JWT")
pinata_gateway = os.getenv("PINATA_GATEWAY")
pinata_group_id = "01933748-f918-7e94-8c17-7564581a5188"
processing_server_url = "https://0280-72-225-33-153.ngrok-free.app/process_video_from_cid"

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


def test_recording():
    print("Running recording test...")
    if not os.path.exists('test_recordings'):
        os.makedirs('test_recordings')

    # Test video recording
    if not test_video_recording(camera_ip, 'test_recordings/test_video.mp4', FPS, 15):  # 15 frames = 1 second at 15 FPS
        return False

    # Test audio recording
    if not test_audio_recording(camera_ip, 'test_recordings/test_audio.wav'):
        return False

    print("Recording test completed successfully")
    return True

def send_to_processing_server(video_cid):
    start_time = time.time()
    try:
        response = requests.post(
            processing_server_url,
            json={"video_cid": video_cid},
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        elapsed_time = time.time() - start_time
        print(f"Video CID {video_cid} sent to processing server successfully. Time taken: {elapsed_time:.2f} seconds")
        return True
    except requests.RequestException as e:
        elapsed_time = time.time() - start_time
        print(f"Error sending video CID to processing server: {str(e)}. Time taken: {elapsed_time:.2f} seconds")
        return False

def record_video_audio():
    global recording

    if not os.path.exists('recordings'):
        os.makedirs('recordings')

    while recording:
        video_filename = f'recordings/video_{int(time.time())}.mp4'
        audio_filename = f'recordings/audio_{int(time.time())}.wav'

        video_thread = threading.Thread(target=record_video, args=(camera_ip, video_filename, FPS, FRAME_COUNT))
        audio_thread = threading.Thread(target=record_audio, args=(camera_ip, audio_filename, DURATION))

        video_thread.start()
        audio_thread.start()

        video_thread.join()
        audio_thread.join()

        print(f"Recording stopped after {FRAME_COUNT} frames and {DURATION:.2f} seconds")

        # Upload video and audio to Pinata
        start_time = time.time()
        with open(video_filename, 'rb') as video_file:
            video_cid = pinata_service.upload_file_to_group(pinata_group_id, os.path.basename(video_filename), video_file.read())
        video_upload_time = time.time() - start_time
        print(f"Video upload time: {video_upload_time:.2f} seconds")

        start_time = time.time()
        with open(audio_filename, 'rb') as audio_file:
            audio_cid = pinata_service.upload_file_to_group(pinata_group_id, os.path.basename(audio_filename), audio_file.read())
        audio_upload_time = time.time() - start_time
        print(f"Audio upload time: {audio_upload_time:.2f} seconds")

        print(f"Video ID (CID): {video_cid}")
        print(f"Audio ID (CID): {audio_cid}")

        # Send video CID to processing server
        if send_to_processing_server(video_cid):
            print("Video sent for processing.")
        else:
            print("Failed to send video for processing.")

        break

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
        app.run(port="5001", debug=True)
    else:
        print("Test recording failed. Please check your IP webcam connection and try again.")
        exit(1)

print("Script execution completed.")