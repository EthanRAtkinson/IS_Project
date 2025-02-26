#-------CV code Motion Capture-----------------------
import cv2
import os
import requests
import json
import sys
import subprocess
import glob
import time

# Define the folder that contains the videos
video_folder = 'footage'

# Define the output folder for clips
output_folder = 'clips'
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

clip_count = 0  # Global clip counter

# Number of consecutive frames without motion needed to stop recording
frames_to_stop = 5

# Loop through all files in the video folder
for filename in os.listdir(video_folder):
    if not filename.endswith(".mp4"):
        continue  # Process only .mp4 files
        
    video_path = os.path.join(video_folder, filename)
    print(f"Processing video: {video_path}")
    
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Error opening video file {video_path}.")
        continue

    ret, frame1 = cap.read()
    if not ret:
        print(f"Failed to read video {video_path}.")
        cap.release()
        continue

    # Convert first frame to grayscale and apply blur
    gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
    gray1 = cv2.GaussianBlur(gray1, (21, 21), 0)

    recording = False
    out = None
    no_motion_count = 0  # counter for frames without motion

    # Start processing frames
    while True:
        ret, frame2 = cap.read()
        if not ret:
            break

        # Convert the current frame to grayscale and blur
        gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.GaussianBlur(gray2, (21, 21), 0)

        # Compute the absolute difference between current and previous frames
        delta_frame = cv2.absdiff(gray1, gray2)
        thresh_frame = cv2.threshold(delta_frame, 25, 255, cv2.THRESH_BINARY)[1]
        thresh_frame = cv2.dilate(thresh_frame, None, iterations=2)

        # Find contours to detect motion
        contours, _ = cv2.findContours(thresh_frame.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        motion_detected = False
        for contour in contours:
            if cv2.contourArea(contour) < 5000:
                continue
            motion_detected = True
            break

        if motion_detected:
            no_motion_count = 0  # reset no-motion counter if motion is found
            if not recording:
                recording = True
                clip_count += 1
                # Setup video writer
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                fps = cap.get(cv2.CAP_PROP_FPS) or 30
                frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                output_path = os.path.join(output_folder, f'clip_{clip_count}.mp4')
                out = cv2.VideoWriter(output_path, fourcc, fps, (frame_width, frame_height))
                print(f"Started recording {output_path}")
            # Write the frame to the clip
            out.write(frame2)
        else:
            # Increase the counter since no motion was found in this frame
            if recording:
                no_motion_count += 1
                # Write a few extra frames to capture end of motion, if needed.
                out.write(frame2)
                if no_motion_count >= frames_to_stop:
                    recording = False
                    out.release()
                    out = None
                    print(f"Stopped recording clip_{clip_count}.mp4")
                    no_motion_count = 0  # reset after finishing a clip

        # Update previous frame
        gray1 = gray2

    cap.release()
    if out is not None:
        out.release()

print("Processing complete.")

#----------FFMpeg Clip Cutting-------------------------

# Define the folder where videos are stored
video_folder = 'clips'

# Define the folder where frames will be saved and create it if it doesn't exist
frames_folder = 'frames'
os.makedirs(frames_folder, exist_ok=True)

# Set the frame rate (number of frames to extract per second)
frame_rate = 1  # Change this number to extract more or fewer frames per second

# Use glob to search for all mp4 files in the video folder (you can add other extensions if needed)
video_files = glob.glob(os.path.join(video_folder, '*.mp4'))

for video_file in video_files:
    # Get the base name of the video file without the extension
    video_basename = os.path.splitext(os.path.basename(video_file))[0]
    
    # Construct the output pattern incorporating the video base name
    # Files will be saved as "frames/video_basename_frame_0001.png", etc.
    output_pattern = os.path.join(frames_folder, f'{video_basename}_frame_%04d.png')
    
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
frames_folder = 'frames'

# Loop through all images in the frames folder
for filename in os.listdir(frames_folder):
    if filename.lower().endswith(('.png', '.jpg', '.jpeg')):  # process only image files
        image_path = os.path.join(frames_folder, filename)

        with open(image_path, 'rb') as fp:
            response = requests.post(
                'https://api.platerecognizer.com/v1/plate-reader/',
                data=dict(regions=regions),  # Optional
                files=dict(upload=fp),
                headers={'Authorization': 'Token 4107dfceaa6da29a76df9723769ae25e292f52a7'}
            )

        json_response = response.json()
        results = json_response.get('results', [])
        
        if results:
            plate_number = results[0].get('plate', '').upper()
            print("Plate Number for {} is: {}".format(filename, plate_number))
        else:
            print("No plate number detected for file {}".format(filename))
        
        time.sleep(1)  # wait 1 second between API calls