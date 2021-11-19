
config_Ania = {
    'wavesurfer_path': "{experiment_id}/{mouse_id}/{session_id}/wavesurfer",
    'sorted_path': "{experiment_id}/{mouse_id}/{session_id}/sorted",
    'ephys_path': "{experiment_id}/{mouse_id}/{session_id}/SpikeGLX",
    'stimlog_path': "{experiment_id}/{mouse_id}/{session_id}/StimLog",
    'facecam_path': "{experiment_id}/{mouse_id}/{session_id}/eyecam",
    'event_types': "default"
}

config_Arnau = {
    'session_path': "{experiment_id}/neuropixel/{session_id}",
    'wavesurfer_path': "{experiment_id}/neuropixel/{session_id}",
    'facecam_path': "{experiment_id}/neuropixel/eyecam/{session_id}",
    'sorted_path': "{experiment_id}/neuropixel/{session_id}/sorted",
    'ephys_path': "{experiment_id}/neuropixel/{session_id}/spikeGLX",
    'stimlog_path': "{experiment_id}/neuropixel/{session_id}/StimLog",
    'event_types': "default"
}

config_ArnauV2 = {
    'session_path': "{experiment_id}/neuropixels/{session_id}",
    'wavesurfer_path': "{experiment_id}/neuropixels/{session_id}",
    'facecam_path': "{experiment_id}/neuropixels/eyecam/{session_id}",
    'sorted_path': "{experiment_id}/neuropixels/{session_id}/sorted",
    'ephys_path': "{experiment_id}/neuropixels/{session_id}/spikeGLX",
    'stimlog_path': "{experiment_id}/neuropixels/{session_id}/StimLog",
    'event_types': "norma"
}

def get_config(name):
    if name == 'Ania':
        return config_Ania
    elif name == 'Arnau':
        return config_Arnau
    elif name == 'ArnauV2':
        return config_ArnauV2