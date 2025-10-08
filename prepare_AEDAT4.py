import os
import json
import dv  # pip install dv
import cv2
import numpy as np

print("[INFO] prepare_AEDAT4.py - Preparing AEDAT4 file for video generation")

def process_sequence(input_path):
    # Check if we're given a folder or an AEDAT4 file
    print(f"[INFO] Processing input: {input_path}")
    if os.path.isdir(input_path):
        meta_path = os.path.join(input_path, "meta.txt")
        if not os.path.exists(meta_path):
            raise FileNotFoundError(f"meta.txt not found in {input_path}")
        print(f"[INFO] Found prepared data at {input_path}, skipping extraction.")
        return

    if not input_path.endswith(".aedat4"):
        raise ValueError("Input must be either a folder or an .aedat4 file")

    base_dir = os.path.dirname(input_path)
    # Use AEDAT4 filename to determine sequence name, e.g. events-sp1-balanced.aedat4 -> seq_sp1_balanced
    seq_name = os.path.splitext(os.path.basename(input_path))[0].replace('-', '_').replace('.', '_')
    output_dir = os.path.join(base_dir, seq_name)
    os.makedirs(output_dir, exist_ok=True)

    events_aedat4_path = os.path.join(output_dir, "events.aedat4")
    meta_txt_path = os.path.join(output_dir, "meta.txt")
    img_dir = os.path.join(output_dir, "img")
    os.makedirs(img_dir, exist_ok=True)



    frames_meta = []
    event_count = 0
    events_txt_path = os.path.join(output_dir, "events.txt")

    print(f"[INFO] Extracting data from {input_path}...")

    # Copy AEDAT4 file to output as events.aedat4
    import shutil
    shutil.copy2(input_path, events_aedat4_path)

    with dv.AedatFile(input_path) as f:
        # Extract frames (if present)
        for i, frame in enumerate(f['frames']):
            frame_name = f"frame_{i:05d}.png"
            frame_path = os.path.join(img_dir, frame_name)
            cv2.imwrite(frame_path, frame.image)
            frames_meta.append({
                'ts': int(frame.timestamp),
                'classical_frame': frame_name
            })

        # Extract events and save to events.txt
        if "events" in f.names:
            with open(events_txt_path, "w") as event_file:
                for packet in f["events"]:
                    try:
                        for e in packet:
                            event_file.write(f"{e.timestamp} {e.x} {e.y} {1 if e.polarity else 0}\n")
                            event_count += 1
                    except TypeError:
                        # If packet is a single event
                        e = packet
                        event_file.write(f"{e.timestamp} {e.x} {e.y} {1 if e.polarity else 0}\n")
                        event_count += 1

    # Save meta.txt in Python dict format for ast.literal_eval
    meta_data = {
        'frames': frames_meta
    }
    with open(meta_txt_path, "w") as meta_file:
        meta_file.write(str(meta_data))

    print(f"[INFO] Extraction complete!")
    print(f"[INFO] Total frames: {len(frames_meta)}")
    print(f"[INFO] Total events: {event_count}")
    print(f"[INFO] Prepared data saved in {output_dir}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Prepare AEDAT4 file for video generation.")
    parser.add_argument("aedat_file", type=str, help="Path to AEDAT4 file to process.")
    args = parser.parse_args()
    process_sequence(args.aedat_file)
