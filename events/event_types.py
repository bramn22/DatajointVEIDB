import scipy.io
import pandas as pd
import numpy as np
from events.stimtypes import EXPA, DIMM
import os


def extract(subsession_type, sync_raw, stimlog_folder, stimlog_iter):
    if subsession_type == 'EXD':  # Fix subsession names! This will currently not work because name is EXD1, EXD2, ...
        trials, trial_starts, trial_ends, trial_stimtypes, _, _, stimtriggers = EXDSubsession().extract(sync_raw, stimlog_folder, stimlog_iter)
    elif subsession_type == 'OPTS':
        trials, trial_starts, trial_ends, trial_stimtypes, _, _, stimtriggers = OPTSSubsession().extract(sync_raw, stimlog_folder, stimlog_iter)
    elif subsession_type == 'EXPA':
        trials, trial_starts, trial_ends, trial_stimtypes, _, _, stimtriggers = StationaryDotSubsession('EXPA').extract(sync_raw, stimlog_folder, stimlog_iter)
    elif subsession_type == 'EXPB':
        trials, trial_starts, trial_ends, trial_stimtypes, _, _, stimtriggers = StationaryDotSubsession('EXPB').extract(sync_raw, stimlog_folder, stimlog_iter)
    elif subsession_type == 'DIMM':
        trials, trial_starts, trial_ends, trial_stimtypes, _, _, stimtriggers = StationaryDotSubsession('DIMM').extract(sync_raw, stimlog_folder, stimlog_iter)
    elif subsession_type == 'EXPN':
        trials, trial_starts, trial_ends, trial_stimtypes, _, _, stimtriggers = StationaryDotSubsession('EXPN').extract(sync_raw, stimlog_folder, stimlog_iter)
    elif subsession_type == 'EXPK':
        trials, trial_starts, trial_ends, trial_stimtypes, _, _, stimtriggers = StationaryDotSubsession('EXPK').extract(sync_raw, stimlog_folder, stimlog_iter)
    elif subsession_type == 'EXPW':
        trials, trial_starts, trial_ends, trial_stimtypes, _, _, stimtriggers = StationaryDotSubsession('EXPW').extract(sync_raw, stimlog_folder, stimlog_iter)
    elif subsession_type == 'CHPE':
        trials, trial_starts, trial_ends, trial_stimtypes, _, _, stimtriggers = CHPESubsession().extract(sync_raw, stimlog_folder, stimlog_iter)
    else:
        raise RuntimeError('Subsession type not recognized:', subsession_type)
    return stimtriggers, trials, trial_starts, trial_ends, trial_stimtypes


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
        print(stimlog_folder, stimlog_iter)
        stimtriggers, trigger_idxs = self.get_stimtriggers(sync_raw)
        stimtypes = self.load_stimtypes_from_stimlog(stimlog_folder, 'EXPAandDIMM', stimlog_iter)
        # Subsession start trigger
        subsession_start = stimtriggers[0][trigger_idxs[0]]
        trigger_idxs[0] += 1

        trial_starts = []
        trial_ends = []
        trial_stimtypes = []
        trials = []
        for stimtype in stimtypes[::4]: # Always 4 iterations of the same stimulus presentation in each trial
            trial_stimtypes.append(self.stimtypes_dict[stimtype]().name)

            if trigger_idxs[7]+4*3+1+1+1 >= len(stimtriggers[7]):
                print("Number of trials in stimlog file exceeds number of triggers found in PXI log. Stims:", len(stimtypes), "Triggers:", len(stimtriggers[7]))
                break
            else:
                print("fine: Stims:", len(stimtypes), "Triggers:", len(stimtriggers[7]), "Current:", trigger_idxs[7]+4*3+1+1+1)
            trial_stims = []
            # Trial start trigger
            # print('stimtriggers', stimtriggers)
            # print('trigger_idxs', trigger_idxs)
            trial_starts.append(stimtriggers[7][trigger_idxs[7]])
            trigger_idxs[7] += 1
            for i in range(4):
                stim_pres, trigger_idxs = self.stimtypes_dict[stimtype]().extract(stimtriggers, trigger_idxs)
                trial_stims.append(stim_pres)

            # Trial stop trigger
            trial_ends.append(stimtriggers[7][trigger_idxs[7]])
            trigger_idxs[7] += 1
            if stimtype == 1:
                # Take into account the extra weird trigger for expanding
                trigger_idxs[7] += 1
            trials.append(trial_stims)
        # Subsession stop trigger
        try:
            subsession_stop = stimtriggers[0][trigger_idxs[0]]
        except:
            print("No subsession_stop trigger found on channel 0. Setting subsession_stop to -1.")
            subsession_stop = -1

        return trials, trial_starts, trial_ends, trial_stimtypes, subsession_start, subsession_stop, stimtriggers


class OPTSSubsession(SubsessionType):

    def extract(self, sync_raw, stimlog_folder, stimlog_iter):
        stimtriggers, trigger_idxs = self.get_stimtriggers(sync_raw)
        subsession_start = stimtriggers[0][trigger_idxs[0]]
        trigger_idxs[0] += 1

        trial_starts = []
        trial_ends = []
        trial_stimtypes = []
        trials = []

        while trigger_idxs[1] < len(stimtriggers[1]):
            trial_starts.append(stimtriggers[1][trigger_idxs[1]])
            trial = []
            while (trigger_idxs[1] < len(stimtriggers[1])-1) and (stimtriggers[1][trigger_idxs[1]+1]-stimtriggers[1][trigger_idxs[1]]<30000): # If difference between current and next is smaller than ~1 second
                trial.append(stimtriggers[1][trigger_idxs[1]])
                trigger_idxs[1] += 1
            trial_ends.append(stimtriggers[1][trigger_idxs[1]])
            trigger_idxs[1] += 1

            trial_stimtypes.append('OPTS')
            trials.append(trial)
        # while trigger_idxs[1]+50 < len(stimtriggers[1]):
        #     trial_starts.append(stimtriggers[1][trigger_idxs[1]])
        #     trial = []
        #     for i in range(50):
        #         trial.append(stimtriggers[1][trigger_idxs[1]])
        #         trigger_idxs[1] += 1
        #     trial_ends.append(stimtriggers[1][trigger_idxs[1]-1])
        #     trial_stimtypes.append('OPTS')
        #     trials.append(trial)
        try:
            subsession_stop = stimtriggers[0][trigger_idxs[0]]
        except:
            print("No subsession_stop trigger found on channel 0. Setting subsession_stop to -1.")
            subsession_stop = -1
        return trials, trial_starts, trial_ends, trial_stimtypes, subsession_start, subsession_stop, stimtriggers


class StationaryDotSubsession(SubsessionType):
    def __init__(self, name):
        self.name = name

    def extract(self, sync_raw, stimlog_folder, stimlog_iter):
        stimtriggers, trigger_idxs = self.get_stimtriggers(sync_raw)
        subsession_start = stimtriggers[0][trigger_idxs[0]]
        trigger_idxs[0] += 1
        stimtriggers[7] = stimtriggers[7][1:-2]

        trials = []
        trial_starts = stimtriggers[7][0::3]
        trial_ends = stimtriggers[7][2::3]
        for i in range(len(trial_starts)):
            trials.append(tuple(stimtriggers[7][i*3:i*3+3]))
        # trial_starts = stimtriggers[2]
        # trial_ends = stimtriggers[3]
        trial_stimtypes = [self.name for _ in trial_starts]

        try:
            subsession_stop = stimtriggers[3][trigger_idxs[3]]
        except:
            print("No subsession_stop trigger found on channel 0. Setting subsession_stop to -1.")
            subsession_stop = -1

        return trials, trial_starts, trial_ends, trial_stimtypes, subsession_start, subsession_stop, stimtriggers

class EXPASubsession(SubsessionType):
    def extract(self, sync_raw, stimlog_folder, stimlog_iter):
        stimtriggers, trigger_idxs = self.get_stimtriggers(sync_raw)
        subsession_start = stimtriggers[0][trigger_idxs[0]]
        trigger_idxs[0] += 1

        trials = []

        trial_starts = stimtriggers[7][0::3]
        trial_ends = stimtriggers[7][2::3]
        # trial_starts = stimtriggers[2]
        # trial_ends = stimtriggers[3]
        trial_stimtypes = ['DIMM' for _ in trial_starts]

        try:
            subsession_stop = stimtriggers[3][trigger_idxs[3]]
        except:
            print("No subsession_stop trigger found on channel 0. Setting subsession_stop to -1.")
            subsession_stop = -1

        return tuple(trials), trial_starts, trial_ends, trial_stimtypes, subsession_start, subsession_stop, stimtriggers


class DIMMSubsession(SubsessionType):
    def extract(self, sync_raw, stimlog_folder, stimlog_iter):
        stimtriggers, trigger_idxs = self.get_stimtriggers(sync_raw)
        subsession_start = stimtriggers[0][trigger_idxs[0]]
        trigger_idxs[0] += 1

        trials = []

        trial_starts = stimtriggers[7][0::3]
        trial_ends = stimtriggers[7][2::3]
        # trial_starts = stimtriggers[2]
        # trial_ends = stimtriggers[3]
        trial_stimtypes = ['DIMM' for _ in trial_starts]

        try:
            subsession_stop = stimtriggers[3][trigger_idxs[3]]
        except:
            print("No subsession_stop trigger found on channel 0. Setting subsession_stop to -1.")
            subsession_stop = -1

        return tuple(
            trials), trial_starts, trial_ends, trial_stimtypes, subsession_start, subsession_stop, stimtriggers


class CHPESubsession(SubsessionType):
    def extract(self, sync_raw, stimlog_folder, stimlog_iter):
        stimtriggers, trigger_idxs = self.get_stimtriggers(sync_raw)
        subsession_start = stimtriggers[0][trigger_idxs[0]]
        trigger_idxs[0] += 1

        trials = []

        trial_starts = stimtriggers[7][0::7] - 30000*2
        trial_ends = stimtriggers[7][6::7] + 30000*2
        # trial_starts = stimtriggers[2]
        # trial_ends = stimtriggers[3]
        trial_stimtypes = ['CHPE' for _ in trial_starts]

        try:
            subsession_stop = stimtriggers[3][trigger_idxs[3]]
        except:
            print("No subsession_stop trigger found on channel 0. Setting subsession_stop to -1.")
            subsession_stop = -1

        return tuple(trials), trial_starts, trial_ends, trial_stimtypes, subsession_start, subsession_stop, stimtriggers
