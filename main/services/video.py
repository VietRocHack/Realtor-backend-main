import cv2
import time
import os

def record_video(camera_ip, filename, fps, frame_count):
    cap = cv2.VideoCapture(f"{camera_ip}/video")
    if not cap.isOpened():
        print("Failed to open video stream")
        return False

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(filename, fourcc, fps, (640, 480))

    frames_recorded = 0
    start_time = time.time()
    while frames_recorded < frame_count:
        ret, frame = cap.read()
        if not ret:
            print("Failed to capture frame")
            cap.release()
            out.release()
            return False
        out.write(frame)
        frames_recorded += 1
        
        elapsed_time = time.time() - start_time
        expected_time = frames_recorded / fps
        if elapsed_time < expected_time:
            time.sleep(expected_time - elapsed_time)

    cap.release()
    out.release()
    return True

def test_video_recording(camera_ip, filename, fps, frame_count):
    print("Testing video recording...")
    if record_video(camera_ip, filename, fps, frame_count):
        print("Video recording test completed successfully")
        return True
    else:
        print("Failed to record video")
        return False