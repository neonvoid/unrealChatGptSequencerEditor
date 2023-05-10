import unreal
import math 
import random 
import json
import openai
import os 
import credsGPT

main_sequencer = unreal.EditorAssetLibrary().load_asset('/Game/anims/2pplconvo/skel2split/2peopleSeq')

if not unreal.Paths.file_exists('D:/unreal_projects/pythonThesisGround/Content/chatgptSeqs/dupes/dupe3.uasset'):
    dupe_seq = unreal.EditorAssetLibrary().duplicate_asset(
        source_asset_path='/Game/anims/2pplconvo/skel2split/2peopleSeq',
        destination_asset_path='/Game/chatgptSeqs/dupes/dupe3'
    )
else:
    pass

seqBindEx = unreal.MovieSceneBindingExtensions()
seqEx = unreal.MovieSceneSequenceExtensions()

seq_binds=main_sequencer.get_bindings()
seq_tracks = main_sequencer.get_master_tracks()

for t in seq_tracks:
    if t.get_display_name() == 'Camera Cuts':
        cameraCutsTrack = t

def setup():

    all_actors = unreal.EditorLevelLibrary().get_all_level_actors()
    for actor in all_actors:
        if 'bp_tracking_2' in actor.get_name():
            attach_cube2 = actor
        elif 'bp_tracking' in actor.get_name():
            attach_cube = actor


    bodies={}
    for c in seq_binds:
        if c.get_display_name()=="Body": 
            body_dict = {'body_instance':c,'attatch_cube':attach_cube2}
            bodies['Body'] = body_dict

        elif c.get_display_name()=='KBody':
            Kbody_dict = {'body_instance':c,'attatch_cube':attach_cube}
            bodies['KBody'] = Kbody_dict

    for b,value in bodies.items():
        animsChildTracks = seqBindEx.get_tracks(value['body_instance'])[0]
        animsChildSection = animsChildTracks.get_sections()

        value['anim_section'] = animsChildSection

        controlRigChannels = seqBindEx.get_tracks(value['body_instance'])[1].get_sections()[0].get_channels()
        head_loc = []
        # lhand_loc = []
        # rhand_loc = []

        for c in controlRigChannels:
            if 'head_ctrl.Location' in c.get_name():
                head_loc.append(c)

        # elif 'hand_l_fk_ctrl.Location' in c.get_name():
        #     lhand_loc.append(c)
        # elif 'hand_r_fk_ctrl.Location' in c.get_name():
        #     rhand_loc.append(c)
        framerate = seqEx.get_display_rate(main_sequencer)
        xRange = head_loc[0].compute_effective_range()
        yRange = head_loc[1].compute_effective_range()
        zRange = head_loc[2].compute_effective_range()

        x = dict(enumerate(head_loc[0].evaluate_keys(xRange,framerate)))
        y = dict(enumerate(head_loc[1].evaluate_keys(yRange,framerate)))
        z = dict(enumerate(head_loc[2].evaluate_keys(zRange,framerate)))
        value['head_loc_x'] = x
        value['head_loc_y'] = y
        value['head_loc_z'] = z

    return bodies

def get_keyframes(loc):
    framerate = seqEx.get_display_rate(main_sequencer)
    xRange = loc[0].compute_effective_range()
    yRange = loc[1].compute_effective_range()
    zRange = loc[2].compute_effective_range()

    x = dict(enumerate(loc[0].evaluate_keys(xRange,framerate)))
    y = dict(enumerate(loc[1].evaluate_keys(yRange,framerate)))
    z = dict(enumerate(loc[2].evaluate_keys(zRange,framerate)))
    return x,y,z

def getAnimSections(bodies):
    sections = []

    for key,val in bodies.items():
        for s in val['anim_section']:
            anims = dict(actor=val['body_instance'].get_name(), 
                         action=s.params.animation.get_name(),
                         action_start=s.get_start_frame(),
                         action_end=s.get_end_frame())
            sections.append(anims)
    cleanSecs = cleanupSections(sections)
    return cleanSecs

def cleanupSections(sections):
    cleanedSec = []
    sections_copy = sections.copy()
    for i, item1 in enumerate(sections_copy):
        for j, item2 in enumerate(sections_copy):
            if i != j:  # don't compare an item to itself
                for key,value in item1.items():
                    if abs(item1['action_start'] - item2['action_start'])<10:
                        choice = random.choice([item1,item2])
                        if item1 not in cleanedSec and item2 not in cleanedSec:
                            cleanedSec.append(choice)
    
    return cleanedSec

def circleSpawn(shottype,center):
    distances = {'CU':100,'MS':500,'WS':1000,'TS':random.uniform(100,1000)}
    radius = distances.get(shottype)
    if radius is None:
        pass

    theta = random.uniform(0,2*math.pi)

    x = center[0] + radius * math.cos(theta)
    y = center[1] + radius * math.sin(theta) 
    z = center[2] + random.uniform(-100,150) 

    if shottype == 'TS':
        return (x,y,z)
    
    else:
        vector = unreal.Vector(x,y,z)
        return vector

def get_shotlist():
    with open('D:\python_unreal\ChatGPTSequencer\query5.json','r') as f:
        shotlist=json.load(f)
    return shotlist

def generate_shotlist(action_list):
    try:
        openai.api_key = credsGPT.key
        query = [
        {'role':'system','content':'you are a film shotlist generator, you will take in an input list of actions and generate a shotlist using any of these shot types: CU,MS,WS,TS. Make sure the shotlist is numbered starting from 1 and make sure you go all the way to the final end_frame but not beyond. Make sure that the start_frame of a cut is the end_frame of the previous cut, the first cut which starts at 0, no empty gaps between shots. The shotlist has a range of 3-25 shots. Return the list in a python dictionary format with double quotations instead of single ones'},
        {'role':'system','content':'each shot will be in this format: "{\n  \"1\": {\n    \"shot_type\": \"WS\",\n    \"actor\": \"Body\",\n    \"action\": \"actout5_01\",\n    \"start_frame\": 0,\n    \"end_frame\": 110\n},"'},
        {'role':'system','content':'only return the dictionary'},
        ]
        query.append({'role':'user','content':action_list})
        with unreal.ScopedSlowTask(1,'chatgpt generating shotlist...',enabled=True) as slow:
            slow.make_dialog(True)
            slow.enter_progress_frame(work=1,desc='calling chatgpt api')
            
            queryResponse = openai.ChatCompletion.create(
            model='gpt-3.5-turbo',
            messages=query
            )
        reply = queryResponse.choices[0].message.content
        start_pos = reply.index('{')
        end_pos = reply.rindex('}')
        dictString = reply[start_pos:end_pos+1]
        data = json.loads(dictString)
        data = parseShotList(data)
        with open('D:\python_unreal\ChatGPTSequencer\shot_list.json','w') as f:
            json.dump(data,f)
        with open('D:\python_unreal\ChatGPTSequencer\ReplyFull.txt','w') as f:
            f.write(str(queryResponse))
        return data
    
    except json.JSONDecodeError as e:
        print(f'jsondecodeerror: {e}, try calling again')

def edit(shotlist,bodies,sequencer):
    seq_tracks =sequencer.get_master_tracks()
    for t in seq_tracks:
        if t.get_display_name() == 'Camera Cuts':
            cameraCutsTrack = t

    cam = unreal.CineCameraActor()
    for i in range(len(shotlist)):

        currentpos= shotlist[f'{i+1}']['end_frame']
        currActor = shotlist[f'{i+1}']['actor']
        center = (bodies[f'{currActor}']['head_loc_x'][currentpos],bodies[f'{currActor}']['head_loc_y'][currentpos],bodies[f'{currActor}']['head_loc_z'][currentpos])

        if shotlist[f'{i+1}']['shot_type']=='TS': 

            cam = unreal.EditorLevelLibrary().spawn_actor_from_object(cam,unreal.Vector(0,0,0),unreal.Rotator(0,0,0),False)
            cam_binding = sequencer.add_possessable(cam)
            cam_binding_id = unreal.MovieSceneObjectBindingID()
            cam_binding_id.set_editor_property('guid',cam_binding.get_id())
            cameraCutsSection = cameraCutsTrack.add_section()
            cameraCutsSection.set_range(shotlist[f'{i+1}']['start_frame'],shotlist[f'{i+1}']['end_frame'])
            cameraCutsSection.set_camera_binding_id(cam_binding_id)
            transformtrack = seqBindEx.add_track(cam_binding,unreal.MovieScene3DTransformTrack)
            transformSection = transformtrack.add_section()
            transformSection.set_range(shotlist[f'{i+1}']['start_frame'],shotlist[f'{i+1}']['end_frame'])
            channels = transformSection.get_channels()
            camLocX = channels[0]
            camLocY = channels[1]
            camLocZ = channels[2]


            grabVal=True
            if (grabVal):
                offSetVec = circleSpawn('TS',center)
                grabVal=False

            for x in range(shotlist[f'{i+1}']['start_frame'],shotlist[f'{i+1}']['end_frame']):
                camLocX.add_key(unreal.FrameNumber(x),bodies[f'{currActor}']['head_loc_x'][x] + offSetVec[0])
                camLocY.add_key(unreal.FrameNumber(x),bodies[f'{currActor}']['head_loc_y'][x] + offSetVec[1])
                camLocZ.add_key(unreal.FrameNumber(x),bodies[f'{currActor}']['head_loc_z'][currentpos] + offSetVec[2])

        else:
            cam = unreal.EditorLevelLibrary().spawn_actor_from_object(cam,circleSpawn(shotlist[f'{i+1}']['shot_type'],center),unreal.Rotator(0,0,0),False)
            cam_binding = sequencer.add_possessable(cam)
            cam_binding_id = unreal.MovieSceneObjectBindingID()
            cam_binding_id.set_editor_property('guid',cam_binding.get_id())
            cameraCutsSection = cameraCutsTrack.add_section()
            cameraCutsSection.set_range(shotlist[f'{i+1}']['start_frame'],shotlist[f'{i+1}']['end_frame'])
            cameraCutsSection.set_camera_binding_id(cam_binding_id)
        
        trackingSettings = unreal.CameraLookatTrackingSettings()
        trackingSettings.set_editor_property('enable_look_at_tracking',True)
        trackingSettings.set_editor_property('actor_to_track', bodies[f'{currActor}']['attatch_cube'])
        trackingSettings.set_editor_property('look_at_tracking_interp_speed',25)
        cam.lookat_tracking_settings = trackingSettings

        fs = cam.get_cine_camera_component().get_editor_property('focus_settings')
        fs.set_editor_property('focus_method', unreal.CameraFocusMethod.DISABLE)
        fb = cam.get_cine_camera_component().get_editor_property('filmback')
        fb.set_editor_property('sensor_width',12.52)
        fb.set_editor_property('sensor_height',7.58)

#headx,heady,headz = get_keyframes(head_loc)
#lhandx,lhandy,lhandz = get_keyframes(lhand_loc)
#rhandx,rhandy,rhandz = get_keyframes(rhand_loc)

#headLoc =[headx,heady,headz]
#lHandLoc = [lhandx,lhandy,lhandz]
#rHandLoc = [rhandx,rhandy,rhandz]

bodies = setup()
def bodiestest():
    print(bodies['KBody']['head_loc_x'][928],bodies['KBody']['head_loc_y'][928],bodies['KBody']['head_loc_z'][928])

def createFirstSeq():
    newAnims = getAnimSections(bodies)
    action_list = f"'{newAnims}'"
    print(action_list)
    shot_list = generate_shotlist(action_list)
    edit(shot_list,bodies,main_sequencer)
    return shot_list

def widgetUpdate(shotlist):
    shot_counts={
        'CU':0,
        'MS':0,
        'MCU':0,
        'WS':0,
        'TS':0
    }

    for x in range(len(shotlist)):
        shottype = shotlist[f'{x+1}']['shot_type']
        if shottype in shot_counts:
            shot_counts[shottype] +=1


def generateVersions(amt):
    for x in range(amt):
        dupe_seq = unreal.EditorAssetLibrary().duplicate_asset(
            source_asset_path='/Game/chatgptSeqs/dupes/dupe3',
            destination_asset_path=f'/Game/chatgptSeqs/dupes/toRender/var{x}'
        )
        edit(shotlist,bodies,dupe_seq)

def parseShotList(data):
    for i in range(len(data)):
        if i ==0:
            data[f'{i+1}']['start_frame'] = 0
            data[f'{i+1}']['end_frame'] = data[f'{i+2}']['start_frame'] 
        elif not i == len(data) -1:
            data[f'{i+2}']['start_frame'] = data[f'{i+1}']['end_frame']

    for key,val in data.items():
        print(f'startframes: {val["start_frame"]}')
        print(f'end frames:{val["end_frame"]}')

    return data

shotlist = None
def main():
    global shotlist
    shotlist = createFirstSeq()
    widgetUpdate(shotlist)

