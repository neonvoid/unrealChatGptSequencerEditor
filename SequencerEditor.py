import unreal
import math 
import random 

sequencer = unreal.EditorAssetLibrary().load_asset('/Game/testforlocationtracking')
seqBindEx = unreal.MovieSceneBindingExtensions()
seqEx = unreal.MovieSceneSequenceExtensions()
seq_binds=sequencer.get_bindings()
seq_tracks = sequencer.get_master_tracks()

all_actors = unreal.EditorLevelLibrary().get_all_level_actors()
for actor in all_actors:
    if 'bp_tracking' in actor.get_name():
        attach_cube = actor

for t in seq_tracks:
    if t.get_display_name() == 'Camera Cuts':
        cameraCutsTrack = t

for c in seq_binds:
    # if c.get_display_name()=='CineCameraActor18':
    #     tmpCam = c
    if c.get_display_name() == 'Body':
        body = c

# tmpCamTracks = seqBindEx.get_tracks(tmpCam)
# for t in tmpCamTracks:
#     print(t)

animsChildTracks = seqBindEx.get_tracks(body)[0]
animsChildSection = animsChildTracks.get_sections()

controlRigChannels = seqBindEx.get_tracks(body)[1].get_sections()[0].get_channels()
head_loc = []
lhand_loc = []
rhand_loc = []
for c in controlRigChannels:
    if 'head_ctrl.Location' in c.get_name():
        head_loc.append(c)
    elif 'hand_l_fk_ctrl.Location' in c.get_name():
        lhand_loc.append(c)
    elif 'hand_r_fk_ctrl.Location' in c.get_name():
        rhand_loc.append(c)

def get_keyframes(loc):
    framerate = seqEx.get_display_rate(sequencer)
    xRange = loc[0].compute_effective_range()
    yRange = loc[1].compute_effective_range()
    zRange = loc[2].compute_effective_range()

    x = dict(enumerate(loc[0].evaluate_keys(xRange,framerate)))
    y = dict(enumerate(loc[0].evaluate_keys(yRange,framerate)))
    z = dict(enumerate(loc[0].evaluate_keys(zRange,framerate)))
    return x,y,z

def getAnimSections():
    sections = []
    for s in animsChildSection:
        sections.append(dict(action=s.params.animation.get_name(),action_start=s.get_start_frame(),action_end=s.get_end_frame()))
    return sections

# how to access dicts in dicts print(shot_list['shot1']['type'])
def circleSpawn(shottype):
    theta = random.uniform(0,2*math.pi)
    if shottype == 'CU':
        distance = 100
    elif shottype == 'MCU':
        distance = 200
    elif shottype == 'MS':
        distance = 500
    elif shottype == 'WS':
        distance = 1000
    else:
        pass

    x=math.cos(theta)*distance
    y=math.sin(theta)*distance
    vector = unreal.Vector(x,y,200)
    return vector

def edit1(shotlist,loc):
    cam = unreal.CineCameraActor()
    for i in range(len(shotlist)):
        if shotlist[i+1]['shot_type']=='TS': #shotlist[f'shot{i+1}']['type']=='TS':
            cam = unreal.EditorLevelLibrary().spawn_actor_from_object(cam,unreal.Vector(0,0,0),unreal.Rotator(0,0,0),False)
            cam_binding = sequencer.add_possessable(cam)
            cam_binding_id = unreal.MovieSceneObjectBindingID()
            cam_binding_id.set_editor_property('guid',cam_binding.get_id())
            cameraCutsSection = cameraCutsTrack.add_section()
            cameraCutsSection.set_range(shotlist[i+1]['start_frame'],shotlist[i+1]['end_frame'])
            #cameraCutsSection.set_range(shotlist[f'shot{i+1}']['start'],shotlist[f'shot{i+1}']['end'])
            cameraCutsSection.set_camera_binding_id(cam_binding_id)
            transformtrack = seqBindEx.add_track(cam_binding,unreal.MovieScene3DTransformTrack)
            transformSection = transformtrack.add_section()
            transformSection.set_range(shotlist[i+1]['start_frame'],shotlist[i+1]['end_frame'])
            #transformSection.set_range(shot_list[f'shot{i+1}']['start'],shot_list[f'shot{i+1}']['end'])
            channels = transformSection.get_channels()
            camLocX = channels[0]
            camLocY = channels[1]
            camLocZ = channels[2]

            for x in range(shotlist[i+1]['start_frame'],shotlist[i+1]['end_frame']):
            #for x in range(shotlist[f'shot{i+1}']['start'],shotlist[f'shot{i+1}']['end']):
                camLocX.add_key(unreal.FrameNumber(x),loc[0][x] + 300)
                camLocY.add_key(unreal.FrameNumber(x),loc[1][x] + 300)
                camLocZ.add_key(unreal.FrameNumber(x),loc[2][x])

        else:
            cam = unreal.EditorLevelLibrary().spawn_actor_from_object(cam,circleSpawn(shotlist[i+1]['shot_type']),unreal.Rotator(0,0,0),False)
            #cam = unreal.EditorLevelLibrary().spawn_actor_from_object(cam,circleSpawn(shotlist[f'shot{i+1}']['type']),unreal.Rotator(0,0,0),False)
            cam_binding = sequencer.add_possessable(cam)
            cam_binding_id = unreal.MovieSceneObjectBindingID()
            cam_binding_id.set_editor_property('guid',cam_binding.get_id())
            cameraCutsSection = cameraCutsTrack.add_section()
            cameraCutsSection.set_range(shotlist[i+1]['start_frame'],shotlist[i+1]['end_frame'])
            #cameraCutsSection.set_range(shotlist[f'shot{i+1}']['start'],shotlist[f'shot{i+1}']['end'])
            cameraCutsSection.set_camera_binding_id(cam_binding_id)
        
        trackingSettings = unreal.CameraLookatTrackingSettings()
        trackingSettings.set_editor_property('enable_look_at_tracking',True)
        trackingSettings.set_editor_property('actor_to_track', attach_cube)
        trackingSettings.set_editor_property('look_at_tracking_interp_speed',25)
        cam.lookat_tracking_settings = trackingSettings

        fs = cam.get_cine_camera_component().get_editor_property('focus_settings')
        fs.set_editor_property('focus_method', unreal.CameraFocusMethod.DISABLE)
        fb = cam.get_cine_camera_component().get_editor_property('filmback')
        fb.set_editor_property('sensor_width',12.52)
        fb.set_editor_property('sensor_height',7.58)

#second ex shot list
shot_list = {
    'shot1': {'type': 'CU', 'action': 'actout5_01', 'start': 0, 'end': 110},
    'shot2': {'type': 'MS', 'action': 'armed_pose2_01', 'start': 78, 'end': 176},
    'shot3': {'type': 'MCU', 'action': 'dives2_01', 'start': 152, 'end': 295},
    'shot4': {'type': 'TS', 'action': 'frontflip_01', 'start': 264, 'end': 405}
}
#chatgpt api shotlist 1
apiShot_list = {
    1: {'shot_type': 'CU', 'action': 'actout5_01', 'start_frame': 0, 'end_frame': 20},
    2: {'shot_type': 'MS', 'action': 'actout5_01', 'start_frame': 20, 'end_frame': 50},
    3: {'shot_type': 'MCU', 'action': 'actout5_01', 'start_frame': 50, 'end_frame': 80},
    4: {'shot_type': 'WS', 'action': 'armed_pose2_01', 'start_frame': 78, 'end_frame': 120},
    5: {'shot_type': 'TS', 'action': 'armed_pose2_01', 'start_frame': 120, 'end_frame': 160},
    6: {'shot_type': 'MS', 'action': 'armed_pose2_01', 'start_frame': 160, 'end_frame': 176},
    7: {'shot_type': 'WS', 'action': 'dives2_01', 'start_frame': 152, 'end_frame': 200},
    8: {'shot_type': 'MCU', 'action': 'dives2_01', 'start_frame': 200, 'end_frame': 240},
    9: {'shot_type': 'CU', 'action': 'dives2_01', 'start_frame': 240, 'end_frame': 280},
    10: {'shot_type': 'TS', 'action': 'dives2_01', 'start_frame': 280, 'end_frame': 295},
    11: {'shot_type': 'CU', 'action': 'frontflip_01', 'start_frame': 264, 'end_frame': 280},
    12: {'shot_type': 'MS', 'action': 'frontflip_01', 'start_frame': 280, 'end_frame': 330},
    13: {'shot_type': 'MCU', 'action': 'frontflip_01', 'start_frame': 330, 'end_frame': 370},
    14: {'shot_type': 'TS', 'action': 'frontflip_01', 'start_frame': 370, 'end_frame': 405}
}

headx,heady,headz = get_keyframes(head_loc)
lhandx,lhandy,lhandz = get_keyframes(lhand_loc)
rhandx,rhandy,rhandz = get_keyframes(rhand_loc)

headLoc =[headx,heady,headz]
lHandLoc = [lhandx,lhandy,lhandz]
rHandLoc = [rhandx,rhandy,rhandz]

#print(headLoc[0][1])
edit1(apiShot_list,headLoc)