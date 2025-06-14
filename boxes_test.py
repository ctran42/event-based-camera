import ast
import os
from collections import defaultdict
import cv2
import numpy as np
import time

base_dir = 'eval/box/txt'

seq_dirs = [f"seq_{i:02d}" for i in range(1)] # stores each seq dir from seq_00 to seq_05

for seq in seq_dirs:
    seq_path = os.path.join(base_dir, seq)

    # Loads meta.txt file data
    meta_path = os.path.join(seq_path, 'meta.txt')
    with open(meta_path) as file:
        content = file.read()
        data = ast.literal_eval(content)
    
    # Loads events.txt file data
    events_path = os.path.join(seq_path, 'events.txt')

    # Gets only rgb frame data from meta.txt
    frames = data['frames']
    rgb_frames = [
        f for f in frames if 'classical_frame' in f
    ]

    # Extracts frame times and names
    frame_windows = []
    for i in range(len(rgb_frames)):
        start_ts = rgb_frames[i-1]['ts'] if i > 0 else 0
        end_ts = rgb_frames[i]['ts']
        frame_name = rgb_frames[i]['classical_frame']
        frame_windows.append({
            'frame': frame_name, 
            'start': start_ts, 
            'end': end_ts
        })
    
    events_by_frame = defaultdict(list)
    index = 0
    size = len(frame_windows)
    curr_frame = frame_windows[index]
    with open(events_path) as f:
        for line in f:
            ts, x, y, pol = line.strip().split()
            ts = float(ts)
            x = int(x)
            y = int(y)
            pol = int(pol)
            print(line)
            while not (curr_frame['start'] <= ts < curr_frame['end']):
                index += 1
                if index < size:
                    curr_frame = frame_windows[index]
                else:
                    break
            
            events_by_frame[curr_frame['frame']].append((ts, x, y, pol))

            # Find which frame this event belongs to
            for window in frame_windows:
                print
                if window['start'] <= ts < window['end']:
                    events_by_frame[window['frame']].append((ts, x, y, pol))
                    break

    # Plays video
    for frame in frame_windows:
        img_path = os.path.join(seq_path, 'img', frame['frame'])
        img = cv2.imread(img_path)

        for ts, x, y, pol in events_by_frame[frame['frame']]:
            color = (0, 255, 0) if pol == 1 else (0, 0, 255)
            cv2.circle(img, (x, y), 1, color, -1)

        start_time = frame['start']
        end_time = frame['end']
        duration = end_time - start_time  # in microseconds or milliseconds?
    
        delay = duration / 1_000 if duration > 100 else 33  # fallback delay

        # Show frame (same as before)
        cv2.imshow("Video", img)
        if cv2.waitKey(int(delay)) & 0xFF == ord('q'):
            break