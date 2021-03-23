import os
import numpy as np
from pathlib import Path
from main_tables import Experiment, Session, Subsession
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
            channel_positions: longblob
            channel_map: longblob
    """

    def make(self, key):
        import pandas as pd
        # Find path with sorted data
        sorted_path = os.path.join(data_path,
                                 "{experiment_id}/{mouse_id}/{session_id}/sorted".format(**key))
        if not os.path.isdir(sorted_path):
            print('Neural recordings for {session_id} in {experiment_id} are not found'.format(**key))
            return
        possible_paths = [sorted_path]
        possible_paths.extend([os.path.join(sorted_path, path) for path in os.listdir(sorted_path) if os.path.isdir(os.path.join(sorted_path, path))])
        print(possible_paths)
        sorted_path = [path for path in possible_paths if os.path.isfile(os.path.join(path, 'phy.log'))]
        print(sorted_path)
        sorted_path = sorted_path[0]

        key['spike_times'] = np.load(os.path.join(sorted_path, 'spike_times.npy'))
        key['spike_clusters'] = np.load(os.path.join(sorted_path, 'spike_clusters.npy'))
        key['spike_templates'] = np.load(os.path.join(sorted_path, 'spike_templates.npy'))
        key['amplitudes'] = np.load(os.path.join(sorted_path, 'amplitudes.npy'))
        key['channel_positions'] = np.load(os.path.join(sorted_path, 'channel_positions.npy'))
        key['channel_map'] = np.load(os.path.join(sorted_path, 'channel_map.npy'))
        key['cluster_info'] = pd.read_csv(os.path.join(sorted_path, 'cluster_info.tsv'), sep='\t', header=0, index_col=0).to_dict()

        self.insert1(key)

        print('Populated sorted recordings for {session_id} in {experiment_id}'.format(**key))


@schema
class EphysRaw(dj.Imported):
    definition = """
            -> Subsession
            ---
            ap_path:  varchar(512)
            meta_path: varchar(512)
            sync_trace: blob@external_neuropixels
            subsession_type: varchar(128)
            length: int
            start: int                       
      """

    def make(self, key):
        # TODO: add file length as metadata

        base_path = r"{experiment_id}/{mouse_id}/{session_id}/SpikeGLX".format(**key)
        path = os.path.join(data_path, base_path)
        print(path)
        if not os.path.isdir(path):
            print('Neural recordings for {session_id} in {experiment_id} are not found'.format(**key))
            return

        subsession_type, subsession_iter = (Subsession() & key).fetch1('type', 'iteration')
        ap_files = [f for f in os.listdir(path) if f.endswith('.ap.bin') and f.split('_')[0]==subsession_type and f.split('_')[1] == f"{subsession_iter}"]
        ap_files.sort()
        print(ap_files)
        file = ap_files[0]

        starts, lengths = (EphysRaw() & {'experiment_id': key['experiment_id'], 'mouse_id': key['mouse_id'], 'session_id': key['session_id']}).fetch('start', 'length')
        print("Starts, lengths:", starts, lengths)
        if len(starts) == 0:
            start = 0
        else:
            last_idx = np.argmax(starts)
            start = starts[last_idx] + lengths[last_idx]


        rel_file_path = os.path.join(base_path, file)
        # id, stimulus_type = file.split('_')[:2]
        key['ap_path'] = rel_file_path
        key['meta_path'] = rel_file_path[:-3] + 'meta'
        key['subsession_type'] = subsession_type
        sync_trace = neuropixels_utils.extract_sync(Path(os.path.join(path, file)))
        key['sync_trace'] = sync_trace
        key['length'] = sync_trace.shape[1]
        key['start'] = start

        self.insert1(key)

        print('Populated neural recordings for {session_id} in {experiment_id}'.format(**key))


@schema
class SubsessionSpikes(dj.Computed):
    definition = """
            -> EphysRaw
            -> SpikeSorted
            ---
            subsession_type: varchar(128)
            start_abs: int
            clusters: longblob            
            cluster_annot: longblob
    """

    def make(self, key):
        experiment_id, session_id, subsession_type, start, length = \
            (EphysRaw() & key).fetch1('experiment_id', 'session_id', 'subsession_type', 'start', 'length')
        key['subsession_type'] = subsession_type
        key['start_abs'] = start
        spike_times, spike_clusters, cluster_info = \
            (SpikeSorted() & key).fetch1('spike_times', 'spike_clusters', 'cluster_info')
        # spike_times, spike_clusters, cluster_info = (
        #             SpikeSorted() & {'experiment_id': experiment_id, 'session_id': session_id}).fetch1('spike_times',
        #                                                                                                'spike_clusters',
        #                                                                                                'cluster_info')

        key['clusters'] = neuropixels_utils.get_trial_clusters(np.squeeze(spike_times), start, length, spike_clusters)
        key['cluster_annot'] = cluster_info['group']
        self.insert1(key)

        print('Populated a trial for {session_id} in {experiment_id}'.format(**key))


# # @schema
# class TrialSpikes(dj.Computed):
#     pass
#
# # @schema
# class StimPresSpikes(dj.Computed):
#     pass