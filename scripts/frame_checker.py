import cv2

def count_frames(video_path):
    # Open the video file
    video = cv2.VideoCapture(video_path)
    
    # Initialize frame count
    frame_count = 0
    
    # Loop through the video frames
    while True:
        # Read a frame
        ret, frame = video.read()
        
        # If frame is read correctly ret is True
        if not ret:
            break
        
        frame_count += 1
    
    # Release the video capture object
    video.release()
    
    return frame_count

# Example usage
video_path = './recordings/video_1731833702.mp4'  # Replace with your video file path
total_frames = count_frames(video_path)
print(f"Total number of frames in the video: {total_frames}")