import json
import os

base_dir = 'eval/box/txt'

seq_dirs = [f"seq_{i:02d}" for i in range(6)] # stores each seq dir from seq_00 to seq_05

for seq in seq_dirs:
    seq_path = os.path.join(base_dir, seq)

    # Loads meta.txt file data
    meta_path = os.path.join(seq_path, 'meta.txt')
    with open(meta_path) as file:
        data = json.load(file)
    
    # Loads events.txt file data
    events_path = os.path.join(seq_path, 'events.txt')

    # Extracts frame times and names
    frames = data['frames']
    frame_windows = []
    for i in range(len(frames)):
        start_ts = frames[i-1]['ts'] if i > 0 else 0
        end_ts = frames[i]['ts']
        frame_name = frames[i]['classical_frame']
        frame_windows.append({'frame': frame_name, 'start': start_ts, 'end': end_ts})