import unreal
import os

executor = None

def OnMoviePipelineExecutorFinished(exec,succ):
    pass

def getSeqVars():
    assetHelpers = unreal.AssetRegistryHelpers().get_asset_registry()
    Sequences =assetHelpers.get_assets_by_path('/Game/chatgptSeqs/dupes/toRender/')
    sequencesToRender=[]
    sequencesToRender.append(unreal.SoftObjectPath(unreal.EditorAssetLibrary().load_asset('/Game/chatgptSeqs/ActionShot2').get_path_name()))
    for s in Sequences:
        loadedAsset = unreal.EditorAssetLibrary().load_asset(f'{s.package_name}')
        assetPathName = loadedAsset.get_path_name()
        softObjWrap = unreal.SoftObjectPath(assetPathName)
        sequencesToRender.append(softObjWrap)
    return sequencesToRender

def makeRenderQueue(sequeces):
    global executor
    movieQueueSubSys = unreal.get_editor_subsystem(unreal.MoviePipelineQueueSubsystem)
    queue = movieQueueSubSys.get_queue()
    outputDir = os.path.abspath(os.path.join(unreal.Paths().project_dir(),'versions'))
    if(len(queue.get_jobs())>0):
        for job in queue.get_jobs():
            queue.delete_job(job)

    world = unreal.UnrealEditorSubsystem().get_editor_world().get_name()
    for i, x in enumerate(sequeces):
        job = queue.allocate_new_job()
        job.set_editor_property('map', unreal.SoftObjectPath('/Game/'+world))
        job.set_editor_property('sequence', x)

        jobConfig = job.get_configuration()
        jobConfig.find_or_add_setting_by_class(unreal.MoviePipelineDeferredPassBase)
        output_setting = jobConfig.find_or_add_setting_by_class(unreal.MoviePipelineOutputSetting)
        RenderDir = os.path.join(outputDir,f'{i}')
        output_setting.output_directory = unreal.DirectoryPath(RenderDir)
        output_setting.output_resolution = (720,480)
        jobConfig.find_or_add_setting_by_class(unreal.MoviePipelineImageSequenceOutput_PNG)

    executor = unreal.MoviePipelinePIEExecutor()
    ecallback = unreal.OnMoviePipelineExecutorFinished()
    ecallback.add_callable(OnMoviePipelineExecutorFinished)
    executor.set_editor_property('on_executor_finished_delegate',ecallback)
    movieQueueSubSys.render_queue_with_executor_instance(executor)

def render():
    sequences = getSeqVars()
    makeRenderQueue(sequences)