import dv

# Open the AEDAT4 file
aedat_file = dv.AedatFile("Datasets/EV fan experiment/events-sp1-balanced.aedat4")

# List available streams
print("Available streams:", aedat_file.names)

# Inspect first few events
if "events" in aedat_file.names:
    print("[INFO] Sample events:")
    for i, event in enumerate(aedat_file["events"]):
        print(event.timestamp, event.x, event.y, event.polarity)
        if i >= 4:  # print first 5 events
            break

# Inspect first few frames if available
if "frames" in aedat_file.names:
    print("[INFO] First few frames:")
    for i, frame in enumerate(aedat_file["frames"]):
        print("Frame", i, "timestamp:", frame.timestamp)
        if i >= 2:
            break
