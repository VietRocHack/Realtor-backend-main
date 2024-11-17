from flask import Flask, jsonify
import cv2
import threading
import time
import os

app = Flask(__name__)

# Global variables
recording = False
thread = None

camera_ip = "http://192.168.137.37:8080"

def test_recording():
    print("Testing video recording...")
    cap = cv2.VideoCapture(f'{camera_ip}/video')
    # cap = cv2.VideoCapture('http://11.20.7.214:8080/video')
    
    if not os.path.exists('recordings'):
        os.makedirs('recordings')
    
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
    print("Test recording completed successfully")
    return True

def record_video():
    global recording
    cap = cv2.VideoCapture(f'{camera_ip}/video')
    
    if not os.path.exists('recordings'):
        os.makedirs('recordings')
    
    while recording:
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(f'recordings/video_{int(time.time())}.mp4', fourcc, 15.00, (640, 480))
        
        start_time = time.time()
        while time.time() - start_time < 10 and recording:
            ret, frame = cap.read()
            if ret:
                out.write(frame)
            else:
                break
        
        out.release()
    
    cap.release()

@app.route('/api/start_session', methods=['POST'])
def start_session():
    global recording, thread
    if not recording:
        recording = True
        thread = threading.Thread(target=record_video)
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
