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
    
    # Each frame will have a dictionary (events_by_frame) that stores a dictionary (pixel_intensity) that stores the coordinates
    # as a key, and its 'intensity' (overall polarity if multiple events occur there)
    events_by_frame = defaultdict(lambda: defaultdict(int))
    pixel_intensity = defaultdict(list)
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
            # Finds correct frame index if not already correct
            while not (curr_frame['start'] <= ts < curr_frame['end']):
                index += 1
                if index < size:
                    curr_frame = frame_windows[index]
                else:
                    break
            
            events_by_frame[curr_frame['frame']][(x, y)] += 1 if pol == 1 else -1
            # for frame, coord_dict in events_by_frame.items():
            #     print(f"Frame {frame}:")
            #     for coord, val in coord_dict.items():
            #         print(f"  Coordinate {coord} → Value {val}")

    
    output_dir = seq + "_output"
    os.makedirs(output_dir, exist_ok=True)
    f = open(seq + '.txt', 'w')
    intensity_step = 80
    # Plays video
    for frame in frame_windows:
        img_path = os.path.join(seq_path, 'img', frame['frame'])
        original_img = cv2.imread(img_path)

        # Create a blank image (same size, black background)
        event_img = np.zeros_like(original_img)

        # Draw each event as a pixel
        for (x, y), val in events_by_frame[frame['frame']].items():
            if 0 <= x < event_img.shape[1] and 0 <= y < event_img.shape[0]:
                green = val < 0
                rgb_val = min(255, abs(val) * intensity_step)
                color = (0, rgb_val, 0) if green else (0, 0, rgb_val)  # green for pol 1, red for 0
                event_img[y, x] = color

        # Combine original and event-only images side by side
        combined_img = np.hstack((original_img, event_img))

        # Save result
        output_path = os.path.join(output_dir, frame['frame'])
        cv2.imwrite(output_path, combined_img)

        start_time = frame['start']
        end_time = frame['end']
        duration = end_time - start_time

        f.write('file \'' + output_path + '\'\nduration ' + str(duration) + '\n')
    
        delay = duration / 1_000 if duration > 100 else 33  # fallback delay

        # Show frame (same as before)
        # cv2.imshow("Video", img)
        # if cv2.waitKey(int(delay)) & 0xFF == ord('q'):
        #     break
    f.close()