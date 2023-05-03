import subprocess
import os
import unreal
import cv2
import time
from moviepy.editor import*

def ffmpegSetup(input,output):
    framerate=24
    cmd=f'ffmpeg -r {framerate} -i "{input}" -pix_fmt yuv420p "{output}"'
    subprocess.check_output(cmd,shell=True)


def Render():
    contents = r'D:/unreal_projects/pythonThesisGround/versions'
    sequences = os.listdir(contents)
    sequenceFolders=[]

    for s in sequences:
        sequenceFolders.append(os.path.join(contents,s))

    for i,s in enumerate(sequenceFolders):
        firstFrame=os.listdir(sequenceFolders[i])[0]
        if 'var' in firstFrame:
            name=firstFrame[:firstFrame.index('.')]
            inputPath = fr"{s}/{name}.%04d.png"
        else:
            name='orig'
            inputPath = fr"{s}/ActionShot.%04d.png"
        outputPath = fr"D:/unreal_projects/pythonThesisGround/Renders/NoLabel/{name}.mp4"

        ffmpegSetup(inputPath,outputPath)
        
def tileVids():
    titlePath = 'D:/unreal_projects/pythonThesisGround/Renders/Labeled/'
    tileInputs = os.listdir(titlePath)
    outputPath = "D:/unreal_projects/pythonThesisGround/Renders/tiled/"

    inputs=[]
    for p in tileInputs:
        path = os.path.join(titlePath,p)
        inputs.append(path)
    if len(inputs) == 9:
        cmd = f'''ffmpeg
        -i {inputs[0]} -i {inputs[1]} -i {inputs[2]} -i {inputs[3]} -i {inputs[4]} -i {inputs[5]} -i {inputs[6]}
        -i {inputs[7]} -i {inputs[8]}
        -filter_complex "
            nullsrc=size=1920x1080 [base];
            [0:v] setpts=PTS-STARTPTS, scale=640x360 [upperleft];
            [1:v] setpts=PTS-STARTPTS, scale=640x360 [uppercenter];
            [2:v] setpts=PTS-STARTPTS, scale=640x360 [upperright];
            [3:v] setpts=PTS-STARTPTS, scale=640x360 [centerleft];
            [4:v] setpts=PTS-STARTPTS, scale=640x360 [centercenter];
            [5:v] setpts=PTS-STARTPTS, scale=640x360 [centerright];
            [6:v] setpts=PTS-STARTPTS, scale=640x360 [lowerleft];
            [7:v] setpts=PTS-STARTPTS, scale=640x360 [lowercenter];
            [8:v] setpts=PTS-STARTPTS, scale=640x360 [lowerright];
            [base][upperleft] overlay=shortest=1 [tmp1];
            [tmp1][uppercenter] overlay=shortest=1:x=640 [tmp2];
            [tmp2][upperright] overlay=shortest=1:x=1280 [tmp3];
            [tmp3][centerleft] overlay=shortest=1:y=360 [tmp4];
            [tmp4][centercenter] overlay=shortest=1:x=640:y=360 [tmp5];
            [tmp5][centerright] overlay=shortest=1:x=1280:y=360 [tmp6];
            [tmp6][lowerleft] overlay=shortest=1:y=720 [tmp7];
            [tmp7][lowercenter] overlay=shortest=1:x=640:y=720 [tmp8];
            [tmp8][lowerright] overlay=shortest=1:x=1280:y=720
        "
        -c:v libx264 {outputPath}tiled.mp4'''

        formattedCmd = cmd.replace('\n','').replace('\t',' ')
        subprocess.check_output(formattedCmd,shell=True)

def addLabels():
    renderPath = 'D:/unreal_projects/pythonThesisGround/Renders/NoLabel/'
    outputPath = 'D:/unreal_projects/pythonThesisGround/Renders/Labeled/'
    moviePaths = os.listdir(renderPath)
    for p in moviePaths:
        path = os.path.join(renderPath,p)
        if 'var' in p:
            name = p[:p.index('.')]
        else:
            name = 'orig'
        movie = VideoFileClip(path)
        duration = movie.duration
        text = TextClip(f'{name}',fontsize=100,color='red').set_position(('left','top')).set_duration(duration)
        comp = CompositeVideoClip([movie,text])
        comp.write_videofile(f'{outputPath}{name}.mp4')
        movie.close()
        comp.close()

def displayTile():
    videoDir = 'D:/unreal_projects/pythonThesisGround/Renders/tiled/'
    tileName = os.listdir(videoDir)[0]
    if 'tile' in tileName:
        tileVidPath = os.path.join(videoDir,tileName)
        cap = cv2.VideoCapture(tileVidPath)

        while(True):
            ret,frame=cap.read()
            cv2.imshow('tile-video',frame)
            time.sleep(.03)
            if(cv2.waitKey(1) & 0xFF == ord('q')):
                break

        cap.release()
        cv2.destroyAllWindows()
    
def main():
    funcs=[Render,addLabels,tileVids]
    with unreal.ScopedSlowTask(len(funcs),'converting png seq to mp4') as task:
        task.make_dialog(True)
        for i,x in enumerate(funcs):
            if i==0:
                task.enter_progress_frame(1)
                x()
            if i==1:
                task.enter_progress_frame(1,'adding labels to movie files')
                x()
            if i==2:
                task.enter_progress_frame(1,'creating video grid')
                x()
    displayTile()
            


# def testing():
#     movie = VideoFileClip("D:/unreal_projects/pythonThesisGround/Renders/orig.mp4")
#     duration = movie.duration

#     text = TextClip("Orig",fontsize=100,color="red").set_position(('left','top')).set_duration(duration)
#     comp = CompositeVideoClip([movie,text])
#     comp.write_videofile('out2.mp4')
#     movie.close()
#     comp.close()
