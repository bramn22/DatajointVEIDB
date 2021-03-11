import os
import numpy as np
from pathlib import Path
from main_tables import Experiment, Session, TrialGroup
import datajoint as dj
from ephys import neuropixels_utils

drive_path = os.environ["DJ_DRIVE_PATH"]
data_path = os.environ["DATA_PATH"]
schema = dj.schema('VEIDB', locals())


@schema
class SpikeSorted(dj.Imported):
    definition = """
            -> Session
            ---
            spike_times: longblob
            spike_clusters: longblob
            cluster_info: longblob
            spike_templates: longblob
            amplitudes: longblob
            mean_waveforms: longblob
            channel_positions: longblob
            channel_map: longblob
    """

    def make(self, key):
        import pandas as pd
        # Find path with sorted data
        sorted_path = os.path.join(data_path,
                                 "{experiment_id}/{session_id}/sorted".format(**key)) # TODO: what does 000 indicate?
        if not os.path.isdir(sorted_path):
            print('Neural recordings for {session_id} in {experiment_id} are not found'.format(**key))
            return
        possible_paths = [sorted_path]
        possible_paths.extend([os.path.join(sorted_path, path) for path in os.listdir(sorted_path) if os.path.isdir(os.path.join(sorted_path, path))])
        print(possible_paths)
        sorted_path = [path for path in possible_paths if os.path.isfile(os.path.join(path, 'phy.log'))]
        print(sorted_path)
        sorted_path = sorted_path[0]

        key['spike_times'] = np.load(os.path.join(sorted_path, 'spike_times.npy')) # Close file?
        key['spike_clusters'] = np.load(os.path.join(sorted_path, 'spike_clusters.npy'))
        key['spike_templates'] = np.load(os.path.join(sorted_path, 'spike_templates.npy'))
        key['amplitudes'] = np.load(os.path.join(sorted_path, 'amplitudes.npy'))
        key['mean_waveforms'] = np.load(os.path.join(sorted_path, 'mean_waveforms.npy'))
        key['channel_positions'] = np.load(os.path.join(sorted_path, 'channel_positions.npy'))
        key['channel_map'] = np.load(os.path.join(sorted_path, 'channel_map.npy'))
        key['cluster_info'] = pd.read_csv(os.path.join(sorted_path, 'cluster_info.tsv'), sep='\t', header=0, index_col=0).to_dict()

        self.insert1(key)

        print('Populated sorted recordings for {session_id} in {experiment_id}'.format(**key))


@schema
class EphysRaw(dj.Imported):
    definition = """
            -> Session
            id: int
            ---
            ap_path:  varchar(512)
            meta_path: varchar(512)
            sync_trace: blob@external_neuropixels
            stimulus_type: varchar(128)
            length: int
            start: int                       
      """

    def make(self, key):
        # TODO: add file length as metadata

        base_path = r"{experiment_id}/{session_id}/spikeGLX".format(**key)
        path = os.path.join(data_path, base_path)
        print(path)
        if not os.path.isdir(path):
            print('Neural recordings for {session_id} in {experiment_id} are not found'.format(**key))
            return

        ap_files = [f for f in os.listdir(path) if f.endswith('.ap.bin')]
        ap_files.sort()
        cumulative_length = 0  # TODO: check whether start includes 0, or starts at 1

        for file in ap_files:
            rel_file_path = os.path.join(base_path, file)
            id, stimulus_type = file.split('_')[:2]
            key['id'] = id
            key['ap_path'] = rel_file_path
            key['meta_path'] = rel_file_path[:-3]+'meta'
            key['stimulus_type'] = stimulus_type
            sync_trace = neuropixels_utils.extract_sync(Path(os.path.join(path, file)))
            key['sync_trace'] = sync_trace
            key['length'] = sync_trace.shape[1]
            key['start'] = cumulative_length
            cumulative_length += sync_trace.shape[1]

            self.insert1(key)

        print('Populated neural recordings for {session_id} in {experiment_id}'.format(**key))


@schema
class Spikes(dj.Computed):
    definition = """
            -> EphysRaw
            ---
            stimulus_type: varchar(128)
            start_abs: int
            stim_trial_start: int
            stim_trial_end: int
            stim_triggers: longblob
            clusters: longblob            
            cluster_annot: longblob
    """

    def make(self, key):
        # TODO: all of this data is relative to the specific stimulus recording, change this, or add it elsewhere!
        # TODO: take into account specific stimulus types
        # TODO: link NeuralSorted explicitely
        experiment_id, session_id, stimulus_type, sync_trace, start, length = \
            (EphysRaw() & key).fetch1('experiment_id', 'session_id', 'stimulus_type', 'sync_trace', 'start', 'length')
        key['stimulus_type'] = stimulus_type
        key['start_abs'] = start
        info = neuropixels_utils.get_trial_stimulus_info(sync_trace)
        key.update(info)

        spike_times, spike_clusters, cluster_info = (SpikeSorted() & {'experiment_id': experiment_id, 'session_id': session_id}).fetch1('spike_times', 'spike_clusters', 'cluster_info')

        key['clusters'] = neuropixels_utils.get_trial_clusters(spike_times, start, length, spike_clusters)
        key['cluster_annot'] = cluster_info['group']
        self.insert1(key)

        print('Populated a trial for {session_id} in {experiment_id}'.format(**key))

# @schema
# class Trial(dj.Computed):
#     pass