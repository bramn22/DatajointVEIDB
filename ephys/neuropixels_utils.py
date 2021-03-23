from ephys.readSGLX import readMeta, SampRate, makeMemMapRaw, ExtractDigital
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
    for cluster in np.unique(trial_spike_clusters):
        cl_spike_times = np.squeeze(trial_spike_times[trial_spike_clusters == cluster])
        data[cluster] = cl_spike_times
    return data