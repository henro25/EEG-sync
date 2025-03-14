import matplotlib.pyplot as plt
import numpy as np
import scipy.io

def sync_streams(data_streams_1, data_streams_2, video_start_UNIX_times, task_start_UNIX_times, task_duration):
    """
    Sync the data by trimming time_stamp and time_series streams so that all EEG and Unicorn Streams begin at the same time
    
    Parameters:
    - data_streams_1: Stream data from WPI HCI Lab xdf file
    - data_streams_2: Stream data from CSL Lab xdf file
    - video_start_UNIX_time: Dictionary of the start OBS VIDEO time of each stream in Unix time
    - task_start_UNIX_time: Dictionary of the start TASK time of each stream in Unix time and the end time for for a stream as well
    """
    
    # Holds the 8 streams (4 OBS and 4 Unicorn)
    streams = {}
    
    # Create mappings of the 8 stream names to streams
    for stream in data_streams_1:
        stream_name = stream["info"]["name"][0]
        
        if stream_name in ["OBS_HCILab1", "Unicorn_HCILab1", "OBS_HCILab2", "Unicorn_HCILab2"]:
            streams[stream_name] = stream
    
    for stream in data_streams_2:
        stream_name = stream["info"]["name"][0]
        
        if stream_name in ["OBS_CSL_Laptop", "Unicorn_CSL_Laptop", "OBS_CSL_LabPC", "Unicorn_CSL_LabPC"]:
            streams[stream_name] = stream
    
    # Trim all the other streams based on the latest Unix timestamp
    for OBS_stream_name, EEG_stream_name in [("OBS_HCILab1", "Unicorn_HCILab1"), ("OBS_HCILab2", "Unicorn_HCILab2"), ("OBS_CSL_Laptop", "Unicorn_CSL_Laptop"), ("OBS_CSL_LabPC", "Unicorn_CSL_LabPC")]:
        if OBS_stream_name not in streams or EEG_stream_name not in streams or OBS_stream_name not in task_start_UNIX_times:
            continue
        
        OBS_stream = streams[OBS_stream_name]
        EEG_stream = streams[EEG_stream_name]
        
        # Debug with printing info
        # print("\n\n")
        # print("EEG stream name: " + EEG_stream_name)
        # print("EEG stream LR timestamps begin at: " + str(EEG_stream["time_stamps"][0]))
        # print("EEG stream LR timestamps end at: " + str(EEG_stream["time_stamps"][-1]))
        # print("OBS stream UNIX time stamps begin at: " + str(OBS_stream["time_series"][0][0]))
        # print("OBS stream UNIX time stamps end at: " + str(OBS_stream["time_series"][-1][0]))
        # print("OBS stream LR timestamps begin at: " + str(OBS_stream["time_stamps"][0]))
        # print("OBS stream LR timestamps end at: " + str(OBS_stream["time_stamps"][-1]))
        # print()
        
        # # Debug with printing info we have
        # print("video start UNIX time: " + str(video_start_UNIX_times[OBS_stream_name]))
        # print("task start UNIX time: " + str(task_start_UNIX_times[OBS_stream_name]))
        # print("task duration: " + str(task_duration))
        # print()
        
        # Find the UNIX timestamp that corresponds to the start of the EEG stream
        EEG_start_labrecorder_timestamp = EEG_stream["time_stamps"][0]
        EEG_start_index_in_OBS = np.searchsorted(OBS_stream["time_stamps"], EEG_start_labrecorder_timestamp)
        
        # Find the index in the OBS stream where the video starts
        OBS_unix_times = [ts[0] for ts in OBS_stream["time_series"]]
        video_start_index_in_OBS = np.searchsorted(OBS_unix_times, video_start_UNIX_times[OBS_stream_name])
        
        # Find the first available correspondence where both the EEG and OBS streams are available, find the corresponding UNIX timestamp, and use that to get the start
        shared_recording_start_index = max(EEG_start_index_in_OBS, video_start_index_in_OBS)
        
        # Use 250Hz as the sampling rate to find the start of the task
        recording_start_to_task_start_duation = task_start_UNIX_times[OBS_stream_name] - OBS_unix_times[shared_recording_start_index]
        
        start_labrecorder_index = shared_recording_start_index + round(30 * recording_start_to_task_start_duation)
        start_labrecorder_timestamp = OBS_stream["time_stamps"][start_labrecorder_index]
        # print("shared_recording_start_index: " + str(shared_recording_start_index) + ", video_start_index_in_OBS: " + str(video_start_index_in_OBS) + ", EEG_start_index_in_OBS: " + str(EEG_start_index_in_OBS))
        # print("recording_start_to_task_start_duation: " + str(recording_start_to_task_start_duation) + ", start_labrecorder_timestamp: " + str(start_labrecorder_timestamp))
        
        # Find the index in the EEG stream where this LabRecorder timestamp occurs
        start_EEG_index = np.searchsorted(EEG_stream["time_stamps"], start_labrecorder_timestamp)
        end_EEG_index = start_EEG_index + round(250 * task_duration)
        print("length of EEG stream: " + str(len(EEG_stream["time_series"])))
        print("start_EEG_index: " + str(start_EEG_index) + ", end_EEG_index: " + str(end_EEG_index))
        
        padded_start_EEG_index = start_EEG_index - 9000
        padded_end_EEG_index = end_EEG_index + 9000
        print("padded_start_EEG_index: " + str(padded_start_EEG_index) + ", padded_end_EEG_index: " + str(padded_end_EEG_index))
        
        start_cut_off_index = 9000
        if padded_start_EEG_index < 0:
            padded_start_EEG_index = 0
            start_cut_off_index = start_EEG_index
        
        # Trim all the data in the EEG streams based on this index
        OG_EEG_stream_len = len(EEG_stream["time_series"])
        EEG_stream["time_stamps"] = EEG_stream["time_stamps"][padded_start_EEG_index:padded_end_EEG_index]
        EEG_stream["time_series"] = EEG_stream["time_series"][padded_start_EEG_index:padded_end_EEG_index]
    
        acutal_end_EEG_index = len(EEG_stream["time_series"]) - max(0, min(OG_EEG_stream_len, padded_end_EEG_index) - end_EEG_index)
        print("actual end EEG index: " + str(acutal_end_EEG_index))
        if end_EEG_index >= OG_EEG_stream_len:
            print("[cut short] For EEG Stream " + EEG_stream_name + ", start cutoff index is " + str(start_cut_off_index) + " and end cutoff index is " + str(len(EEG_stream["time_series"])))
            assert len(EEG_stream["time_series"]) == acutal_end_EEG_index
        else:
            print("For EEG Stream " + EEG_stream_name + ", start cutoff index is " + str(start_cut_off_index) + " and end cutoff index is " + str(end_EEG_index - padded_start_EEG_index))
            assert acutal_end_EEG_index == end_EEG_index - padded_start_EEG_index
        print()
    
    return streams

def combine_streams(group_num, streams):
    # Disable scientific notation in NumPy globally
    np.set_printoptions(suppress=True)

    # find the max length of time_series in all EEG streams to establish dimensions for synced EEG streams
    max_length = 0
    num_streams = 0

    for stream_name in ["Unicorn_HCILab1", "Unicorn_HCILab2", "Unicorn_CSL_Laptop", "Unicorn_CSL_LabPC"]:
        if stream_name in streams:
            num_streams += 1
            max_length = max(max_length, len(streams[stream_name]["time_series"]))

    # Create an np array to hold the synced EEG data with dimensions (max_length, 4 * 8)
    synced_EEG_data = np.full((max_length, num_streams * 8), np.nan)

    # Fill in the synced EEG data
    for j, stream_name in enumerate(["Unicorn_HCILab1", "Unicorn_HCILab2", "Unicorn_CSL_Laptop", "Unicorn_CSL_LabPC"]):
        if stream_name not in streams:
            continue
        
        EEG_stream = streams[stream_name]
        
        eeg_stream_data = np.full((len(EEG_stream["time_series"]), 8), np.nan)
        for time_index, eeg_data in enumerate(EEG_stream["time_series"]):
            synced_EEG_data[time_index, j * 8:(j + 1) * 8] = eeg_data[0:8]
            eeg_stream_data[time_index, :] = eeg_data[0:8]
        
        # Visualize the EEG stream data
        time_indices = range(eeg_stream_data.shape[0])
        
        plt.figure(figsize=(20, 10))
        
        # Plot each channel as a separate line
        for channel_idx in range(eeg_stream_data.shape[1]):
            plt.plot(time_indices, eeg_stream_data[:, channel_idx], label=f'Channel {channel_idx+1}')

        plt.title(f"{stream_name} EEG Stream Data")
        plt.xlabel("Time Index")
        plt.ylabel("EEG Signal Amplitude")
        plt.legend()
        plt.grid(True)
        plt.show()

        # Download the EEG data as an .mat file
        # scipy.io.savemat(f'{stream_name}.mat', {f'{stream_name}': eeg_stream_data})

    # Visualize the synced EEG data
    plt.figure(figsize=(20, 10))
    plt.imshow(synced_EEG_data.T, aspect='auto', cmap='jet')
    plt.colorbar(format='%.2f')  # Ensures color bar does not use scientific notation
    plt.title("Synced EEG Data")
    plt.xlabel("Time Index")
    plt.ylabel("Channel Index")
    plt.show()

    print("Min:", np.nanmin(synced_EEG_data))
    print("Max:", np.nanmax(synced_EEG_data))
    print("Mean:", np.nanmean(synced_EEG_data))
    print("Standard Deviation:", np.nanstd(synced_EEG_data))

    # Download the EEG data as an .mat file
    scipy.io.savemat(f'padded_task_cutoff_EEG_data_{group_num}.mat', {f'padded_task_cutoff_EEG_data_{group_num}': synced_EEG_data})
