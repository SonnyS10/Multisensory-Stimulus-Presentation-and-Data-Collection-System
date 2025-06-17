import pyxdf
import pandas as pd
import os

#This script is used to load and process XDF files, specifically for EEG data.
#It provides functions to load an XDF file, print stream information, and save a specific stream to a CSV file.

def load_xdf_file(file_path):
    """
    Load an XDF file and return its streams.

    :param file_path: Path to the .xdf file.
    :return: A tuple containing the streams and file header.
    """
    try:
        streams, file_header = pyxdf.load_xdf(file_path)
        print(f"Successfully loaded {len(streams)} streams from {file_path}.")
        return streams, file_header
    except Exception as e:
        print(f"Error loading XDF file: {e}")
        return None, None

def print_stream_info(streams):
    """
    Print information about the streams in the XDF file.

    :param streams: List of streams loaded from the XDF file.
    """
    for i, stream in enumerate(streams):
        info = stream['info']
        print(f"Stream {i + 1}:")
        print(f"  Name: {info['name'][0]}")
        print(f"  Type: {info['type'][0]}")
        print(f"  Channel Count: {info['channel_count'][0]}")
        print(f"  Sampling Rate: {info['nominal_srate'][0]}")
        print(f"  Data Points: {len(stream['time_series'])}")
        print()

def save_stream_to_csv(stream, file_path):
    """
    Save a single stream's data to a CSV file.

    :param stream: The stream to save.
    :param file_path: Path to the output CSV file.
    """
    try:
        data = stream['time_series']
        timestamps = stream['time_stamps']
        columns = [f"Channel_{i + 1}" for i in range(len(data[0]))]
        df = pd.DataFrame(data, columns=columns)
        df['Timestamp'] = timestamps
        df.to_csv(file_path, index=False)
        print(f"Stream saved to {file_path}.")
    except Exception as e:
        print(f"Error saving stream to CSV: {e}")

if __name__ == "__main__":
    # Prompt the user for the .xdf file path
    file_path = input("Enter the path to the .xdf file: ").strip()

    # Check if the file exists
    if not os.path.exists(file_path):
        print(f"Error: File '{file_path}' does not exist.")
    else:
        streams, file_header = load_xdf_file(file_path)

        if streams:
            print_stream_info(streams)
            # Prompt the user to save a specific stream
            stream_index = int(input(f"Enter the stream index (1-{len(streams)}) to save as CSV: ")) - 1
            if 0 <= stream_index < len(streams):
                output_path = input("Enter the output CSV file path: ").strip()
                save_stream_to_csv(streams[stream_index], output_path)
            else:
                print("Invalid stream index.")