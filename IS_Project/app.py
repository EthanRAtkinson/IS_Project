#-------CV code Motion Capture-----------------------
import cv2
import os
import requests
import json
import sys
import subprocess

# Define the output folder
output_folder = 'clips'

# Create the folder if it doesn't exist
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# Path to the input video file
video_path = 'TestFootage.mp4'  # Replace with your video file path

# Initialize video capture
cap = cv2.VideoCapture(video_path)

# Check if video opened successfully
if not cap.isOpened():
    print("Error opening video file.")
    exit(1)

# Read the first frame
ret, frame1 = cap.read()
if not ret:
    print("Failed to read video.")
    cap.release()
    exit(1)

# Convert first frame to grayscale
gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
gray1 = cv2.GaussianBlur(gray1, (21, 21), 0)

# Variables for recording
recording = False
out = None
clip_count = 0

while True:
    ret, frame2 = cap.read()
    if not ret:
        break

    # Convert frame to grayscale
    gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.GaussianBlur(gray2, (21, 21), 0)

    # Compute absolute difference between frames
    delta_frame = cv2.absdiff(gray1, gray2)
    thresh_frame = cv2.threshold(delta_frame, 25, 255, cv2.THRESH_BINARY)[1]
    thresh_frame = cv2.dilate(thresh_frame, None, iterations=2)

    # Find contours
    contours, _ = cv2.findContours(
        thresh_frame.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Check for motion
    motion_detected = False
    for contour in contours:
        if cv2.contourArea(contour) < 5000:
            continue
        motion_detected = True
        break

    if motion_detected:
        if not recording:
            recording = True
            clip_count += 1
            # Setup video writer
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            fps = cap.get(cv2.CAP_PROP_FPS) or 30
            frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            # Construct the full path for the video clip inside the output folder
            output_path = os.path.join(output_folder, f'clip_{clip_count}.mp4')
            out = cv2.VideoWriter(output_path, fourcc, fps, (frame_width, frame_height))
            print(f"Started recording {output_path}")
        out.write(frame2)
    else:
        if recording:
            recording = False
            out.release()
            out = None
            print(f"Stopped recording clip_{clip_count}.mp4")

    # Update previous frame
    gray1 = gray2

cap.release()
if out is not None:
    out.release()
#----------FFMpeg Clip Cutting-------------------------

# Specify the path to your video file inside the "clips" folder
video_file = os.path.join('clips', 'clip_5.mp4')  # Adjust the filename if needed

# Create a new folder called "frames" if it doesn't already exist
os.makedirs('frames', exist_ok=True)

# Specify the output pattern for the extracted frames in the new folder
output_pattern = os.path.join('frames', 'frame_%04d.png')  # Files will be saved as frames/frame_0001.png, etc.

# Set the frame rate (number of frames to extract per second)
frame_rate = 1  # Change this number to extract more or fewer frames per second

# Construct the ffmpeg command
command = [
    'ffmpeg',
    '-i', video_file,
    '-vf', f'fps={frame_rate}',
    output_pattern
]

# Run the ffmpeg command
subprocess.run(command)
#----------Platerecognizer  API to get plate number------------------
regions = ['in']  # Change to your country

# Provide the path of the image inside the "frames" folder
image_path = os.path.join('frames', 'frame_0002.png')

with open(image_path, 'rb') as fp:
    response = requests.post(
        'https://api.platerecognizer.com/v1/plate-reader/',
        data=dict(regions=regions),  # Optional
        files=dict(upload=fp),
        headers={'Authorization': 'Token 4107dfceaa6da29a76df9723769ae25e292f52a7'}
    )

plate_number = response.json()['results'][0]['plate']

print("Plate Number is : " + plate_number.upper())