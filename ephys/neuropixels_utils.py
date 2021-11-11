from ephys.readSGLX import readMeta, SampRate, makeMemMapRaw, ExtractDigital, GainCorrectIM, GainCorrectNI, ChannelCountsNI
import numpy as np


def extract_sync(file_path):
    dw = 0
    dLineList = list(range(16))
    meta = readMeta(file_path)
    sRate = SampRate(meta)

    firstSamp = 0
    lastSamp = int(sRate * float(meta['fileTimeSecs'])) - 1
    rawData = makeMemMapRaw(file_path, meta)

    # get digital data for the selected lines
    digArray = ExtractDigital(rawData, firstSamp, lastSamp, dw, dLineList, meta)
    return digArray

def extract_analog(file_path, channels):
    # For analog channels: zero-based index of a channel to extract,
    # gain correct and plot (plots first channel only)
    chanList = channels

    # Read in metadata; returns a dictionary with string for values
    meta = readMeta(file_path)

    # parameters common to NI and imec data
    sRate = SampRate(meta)
    firstSamp = 0
    lastSamp = int(sRate * float(meta['fileTimeSecs'])) - 1

    rawData = makeMemMapRaw(file_path, meta)

    selectData = rawData[chanList, firstSamp:lastSamp+1]
    if meta['typeThis'] == 'imec':
        # apply gain correction and convert to uV
        convData = 1e6*GainCorrectIM(selectData, chanList, meta)
    else:
        MN, MA, XA, DW = ChannelCountsNI(meta)
        # print("NI channel counts: %d, %d, %d, %d" % (MN, MA, XA, DW))
        # apply gain coorection and conver to mV
        convData = 1e3*GainCorrectNI(selectData, chanList, meta)
    return convData

def get_ap_analog(file_path, start, end, window, channels=None):
    """ Retrieves raw signals for given channels within the given time window """
    # For analog channels: zero-based index of a channel to extract,
    # gain correct and plot (plots first channel only)
    if channels == None:
        chanList = list(range(0, 374, 1))
    else:
        chanList = channels

    # For a digital channel: zero based index of the digital word in
    # the saved file. For imec data there is never more than one digital word.
    dw = 0

    # Zero-based Line indicies to read from the digital word and plot.
    # For 3B2 imec data: the sync pulse is stored in line 6.
    dLineList = [0, 1, 6]
    # Read in metadata; returns a dictionary with string for values
    meta = readMeta(file_path)

    rawData = makeMemMapRaw(file_path, meta)

    # parameters common to NI and imec data
    sRate = SampRate(meta)
    firstSamp = start+window[0]
    lastSamp = end+window[1]

    # array of times for plot
    tDat = np.arange(firstSamp, lastSamp+1)
    tDat = 1000*tDat/sRate      # plot time axis in msec

    print(firstSamp, lastSamp)
    selectData = rawData[chanList, firstSamp:lastSamp+1]
    if meta['typeThis'] == 'imec':
        # apply gain correction and convert to uV
        convData = 1e6*GainCorrectIM(selectData, chanList, meta)
    else:
        MN, MA, XA, DW = ChannelCountsNI(meta)
        # print("NI channel counts: %d, %d, %d, %d" % (MN, MA, XA, DW))
        # apply gain coorection and conver to mV
        convData = 1e3*GainCorrectNI(selectData, chanList, meta)
    import matplotlib.pyplot as plt
    # Plot the first of the extracted channels
    fig, ax = plt.subplots()
    ax.plot(tDat, convData[0, :])
    plt.show()
    return convData


def get_trialgroup_stimulus_info(sync_trace):
    s2 = np.diff(sync_trace, prepend=0)

    # These are the channels used by Katja in her recordings
    info = {}
    info['subsession_triggers'] = np.where(s2[7] == 1)[0]
    try:
        info['trials_start'] = np.where(s2[0] == 1)[0][0]  # Trial start in the entire session
    except IndexError as e:
        print("Error occurred when loading events start.", str(e))
        info['trials_start'] = -1
    try:
        info['trials_end'] = np.where(s2[3] == 1)[0][0]  # TODO change absolute to relative end?
    except IndexError as e:
        print("Error occurred when loading events end.", str(e))
        info['trials_end'] = -1
    return info


def get_trial_clusters(spike_times, start, length, spike_clusters):
    trial_spike_times = spike_times[(spike_times >= start) & (
                spike_times < start + length)] - start  # -start so that the times are relative to the trial
    trial_spike_clusters = spike_clusters[
        (spike_times >= start) & (spike_times < start + length)]  # TODO: make efficient
    data = {}
    for cluster in np.unique(spike_clusters):
        cl_spike_times = np.squeeze(trial_spike_times[trial_spike_clusters == cluster])
        data[cluster] = cl_spike_times
    return data