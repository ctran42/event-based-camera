
import ast
import os
from collections import defaultdict
import cv2
import numpy as np
import argparse

def main():
    parser = argparse.ArgumentParser(description="Generate video from events and frames.")
    parser.add_argument('--meta', required=True, help='Path to meta.txt file')
    parser.add_argument('--events', required=True, help='Path to events.txt file')
    parser.add_argument('--img_dir', required=True, help='Path to directory containing frame images')
    parser.add_argument('--output_dir', required=True, help='Directory to save output images and ffmpeg list')
    parser.add_argument('--ffmpeg_list', default='frames.txt', help='Output ffmpeg concat list filename')
    args = parser.parse_args()

    # Load meta.txt
    with open(args.meta) as file:
        data = ast.literal_eval(file.read())

    frames = data['frames']
    rgb_frames = [f for f in frames if 'classical_frame' in f]

    # Extract time windows for each frame
    # Convert timestamps to seconds (assuming microseconds)
    frame_windows = []
    for i in range(len(rgb_frames)):
        start_ts = rgb_frames[i - 1]['ts'] if i > 0 else rgb_frames[0]['ts']
        end_ts = rgb_frames[i]['ts']
        # Convert to seconds
        start_ts_sec = start_ts / 1_000_000
        end_ts_sec = end_ts / 1_000_000
        frame_name = rgb_frames[i]['classical_frame']
        frame_windows.append({'frame': frame_name, 'start': start_ts_sec, 'end': end_ts_sec})

    # Prepare data structures
    # For each frame, accumulate only the events that fall within its time window
    events_by_frame = []
    # Read all events into a list (convert timestamps to seconds)
    all_events = []
    with open(args.events) as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) != 4:
                continue
            ts, x, y, pol = int(parts[0]), int(parts[1]), int(parts[2]), int(parts[3])
            ts_sec = ts / 1_000_000  # convert to seconds
            all_events.append((ts_sec, x, y, pol))

    # For each frame, accumulate events in its window
    event_idx = 0
    n_events = len(all_events)
    for frame in frame_windows:
        start, end = frame['start'], frame['end']
        frame_events = defaultdict(int)
        # Advance event_idx to first event in window
        while event_idx < n_events and all_events[event_idx][0] < start:
            event_idx += 1
        # Accumulate events in window
        idx = event_idx
        while idx < n_events and all_events[idx][0] < end:
            _, x, y, pol = all_events[idx]
            frame_events[(x, y)] += 1 if pol else -1
            idx += 1
        events_by_frame.append(frame_events)

    # Output directory for combined images
    os.makedirs(args.output_dir, exist_ok=True)

    ffmpeg_list = open(args.ffmpeg_list, 'w')
    intensity_step = 80

    # Get the directory where frames.txt will be saved
    ffmpeg_list_dir = os.path.dirname(os.path.abspath(args.ffmpeg_list))

    for i, frame in enumerate(frame_windows):
        img_path = os.path.join(args.img_dir, frame['frame'])
        original_img = cv2.imread(img_path)

        if original_img is None:
            continue

        # Blank image for events
        event_img = np.zeros_like(original_img)

        for (x, y), val in events_by_frame[i].items():
            if 0 <= x < event_img.shape[1] and 0 <= y < event_img.shape[0]:
                color_val = min(255, abs(val) * intensity_step)
                # Green for negative polarity, Red for positive polarity
                color = (0, color_val, 0) if val < 0 else (0, 0, color_val)
                event_img[y, x] = color

        # Combine side-by-side
        combined_img = np.hstack((original_img, event_img))

        # Save combined frame
        output_path = os.path.join(args.output_dir, frame['frame'])
        cv2.imwrite(output_path, combined_img)

        # Write path relative to frames.txt location
        rel_output_path = os.path.relpath(output_path, ffmpeg_list_dir)
        duration = frame['end'] - frame['start']
        ffmpeg_list.write(f"file '{rel_output_path}'\n")
        ffmpeg_list.write(f"duration {duration:.6f}\n")

    ffmpeg_list.close()

    print(f"Processing complete. Run ffmpeg to compile the video:")
    print(f"ffmpeg -f concat -safe 0 -i {args.ffmpeg_list} -vsync vfr -pix_fmt yuv420p output.mp4")

if __name__ == "__main__":
    main()
