import scipy.io
import pandas as pd
import numpy as np
from events.stimtypes import EXPA, DIMM
import os


def extract(subsession_type, sync_raw, stimlog_folder, stimlog_iter):
    if subsession_type == 'EXD':  # Fix subsession names! This will currently not work because name is EXD1, EXD2, ...
        trials, _, _, stimtriggers = EXDSubsession().extract(sync_raw, stimlog_folder, stimlog_iter)
    elif subsession_type == 'OPTS':
        trials, _, _, stimtriggers = OPTSSubsession().extract(sync_raw, stimlog_folder, stimlog_iter)
    else:
        raise RuntimeError('Subsession type not recognized:', subsession_type)
    return stimtriggers, trials


class SubsessionType:

    def load_stimtypes_from_stimlog(self, stimlog_folder, stimlog_name, stimlog_iter):
        stimlogs = [filename for filename in os.listdir(stimlog_folder) if stimlog_name+f"{stimlog_iter:04d}" in filename]
        print(stimlogs)
        stimlog_path = os.path.join(stimlog_folder, stimlogs[0])
        mat = scipy.io.loadmat(stimlog_path, squeeze_me=True)
        stim_info = mat['StimLog']['Stim']
        stimtypes = np.atleast_1d(stim_info)[0]['StimType']
        return stimtypes

    def get_stimtriggers(self, sync_raw):
        """ Extracts and interprets events and returns event end index """
        sync = np.diff(sync_raw, prepend=0)
        stimtriggers = [np.where(sync[s_ch] == 1)[0] for s_ch in range(len(sync))]
        trigger_idxs = [0 for _ in range(len(sync))]
        return stimtriggers, trigger_idxs

    def extract(self, sync_raw, stimlog_folder, stimlog_iter):
        pass


class EXDSubsession(SubsessionType):
    stimtypes_dict = {
        1: EXPA,
        2: DIMM
    }

    def extract(self, sync_raw, stimlog_folder, stimlog_iter):
        stimtriggers, trigger_idxs = self.get_stimtriggers(sync_raw)
        stimtypes = self.load_stimtypes_from_stimlog(stimlog_folder, 'EXPAandDIMM', stimlog_iter)
        # Subsession start trigger
        subsession_start = stimtriggers[0][trigger_idxs[0]]
        trigger_idxs[0] += 1

        trial_starts = []
        trial_stops = []
        trials = []
        for stimtype in stimtypes[::4]: # Always 4 iterations of the same stimulus presentation in each trial
            trial_stims = []
            # Trial start trigger
            trial_starts.append(stimtriggers[0][trigger_idxs[0]])
            trigger_idxs[0] += 1
            for i in range(4):
                stim_pres, stimtriggers = self.stimtypes_dict[stimtype].extract(stimtriggers, trigger_idxs)
                trial_stims.append(stim_pres)
            # Trial stop trigger
            trial_stops.append(stimtriggers[0][trigger_idxs[0]])
            trigger_idxs[0] += 1
            # Take into account the extra weird trigger
            trials.append(trial_stims)
        # Subsession stop trigger
        subsession_stop = stimtriggers[0][trigger_idxs[0]]

        return trials, subsession_start, subsession_stop, stimtriggers


class OPTSSubsession(SubsessionType):

    def extract(self, stimtriggers, trigger_idxs, stimtypes):
        return None, None, None, None