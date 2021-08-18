
config_Ania = {
    'wavesurfer_path': "{experiment_id}/{mouse_id}/{session_id}/wavesurfer",
    'sorted_path': "{experiment_id}/{mouse_id}/{session_id}/sorted",
    'ephys_path': "{experiment_id}/{mouse_id}/{session_id}/SpikeGLX",
    'stimlog_path': "{experiment_id}/{mouse_id}/{session_id}/StimLog",
    'facecam_path': "{experiment_id}/{mouse_id}/{session_id}/eyecam"
}

config_Arnau = {
    'session_path': "{experiment_id}/neuropixel/{session_id}",
    'wavesurfer_path': "{experiment_id}/neuropixel/{session_id}",
    'facecam_path': "{experiment_id}/neuropixel/eyecam/{session_id}",
    'sorted_path': "{experiment_id}/neuropixel/{session_id}/sorted",
    'ephys_path': "{experiment_id}/neuropixel/{session_id}/spikeGLX",
    'stimlog_path': "{experiment_id}/neuropixel/{session_id}/StimLog"
}


def get_config(name):
    if name == 'Ania':
        return config_Ania
    elif name == 'Arnau':
        return config_Arnau