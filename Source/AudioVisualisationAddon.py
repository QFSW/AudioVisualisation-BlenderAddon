import bpy, time, sys
from bpy import context

#Info
bl_info = {
    "name": "Audio Visualiser",
    "description": "Generates an array of objects and bakes sound curves them to visualise an audio file",
    "author":"Yusuf Ismail",
    "version":(0,1),
    "blender":(2,76,0),
    "category": "Audio"
}

#Audio panel to input settings
class AudioPanel(bpy.types.Panel):
    bl_label = "Audio Visualisation"
    bl_idname = "Audio_Visualise"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "scene"
 
    def draw(self, context):
        #Displays all the settings and buttons
        layout = self.layout
        Scene = context.scene
        
        layout.label("Import Options")
        row = layout.row()
        row.prop(Scene, "FileString")
        
        layout.label("")
        layout.label("Scene Options")
        row = layout.row()
        row.prop(Scene, "FRange")
        row.enabled=Scene.VSE
        
        layout.label("")
        layout.label("Audio Options")
        row = layout.row()
        row.prop(Scene, "SFrame")
        row.prop(Scene, "VSE")
        
        row = layout.row()
        row.prop(Scene, "AObj")
        row.enabled=False
        
        layout.label("")
        layout.label("Generation Options")
        row = layout.row()
        row.prop(Scene, "Count")
        row.label("")
        
        row = layout.row()
        row.prop(Scene, "StepSize")
        row.prop(Scene, "StartF")
        
        
        row = layout.row()
        row.prop(Scene,"SPos")
        
        row = layout.row()
        row.prop(Scene,"DPos")
        
        layout.label("")
        layout.label("Mesh Options")
        row = layout.row()
        row.prop(Scene, "Name")
        row.prop(Scene, "Index")
        row = layout.row()
        row.prop(Scene,"Scale")
        row = layout.row()
        row.prop(Scene, "Origin")
        row = layout.row()
        row.prop(Scene, "ScaleLock")
        row = layout.row()
        row.prop(Scene, "Material")
        row = layout.row()
        row.prop_search(Scene, "MaterialName", bpy.data, "materials")
        row.enabled = Scene.Material
        
        layout.label("")
        layout.operator("audio.visualise")

#Generates the visualisation
class GenerateVisualisation(bpy.types.Operator):
    bl_idname = "audio.visualise"
    bl_label = "Generate Visualisation"

    def execute(self, context):
        #Caches information
        Scene = context.scene
        CurrentArea= bpy.context.area.type
        Scene.frame_current=Scene.SFrame
        Time=0
        AverageTime=0
        
        #Adds the sound strip
        try:
            if Scene.VSE:
                bpy.context.area.type = "SEQUENCE_EDITOR"
                bpy.ops.sequencer.sound_strip_add(filepath=Scene.FileString,frame_start=Scene.SFrame)
                
                if Scene.FRange:
                    Scene.frame_end=Scene.SFrame+Scene.sequence_editor.sequences_all[-1].frame_final_duration
                    
                bpy.context.area.type = CurrentArea
            
        except:
            print("Error: Failed to add sound strip")
                
        XP=Scene.SPos[0]
        YP=Scene.SPos[1]
        ZP=Scene.SPos[2]
        try:
            print("\n\n")
            for i in range(Scene.Count):
                if i>0:
                    AverageTime=(AverageTime*i+time.time()-Time)/(i+1)
                UpdateProgress("Audio Visualisation in Progress",i/Scene.Count,AverageTime*(Scene.Count-i))
                Time = time.time()
                if i==0:
                    
                    #Creates Cube
                    bpy.ops.mesh.primitive_cube_add()
                    Cube=bpy.context.scene.objects.active
                    
                    if Scene.Material:
                        try:
                            #Retrieves material
                            Material = bpy.data.materials.get(Scene.MaterialName)
                            if Material is None:
                                #Create material if not found
                                Material = bpy.data.materials.new(name="Material")
                                
                            # Assign it to object
                            if Cube.data.materials:
                                #Assign to 1st material slot
                                Cube.data.materials[0] = Material
                            else:
                                #No slots
                                Cube.data.materials.append(Material)
                        except:
                            print("Error: Assigning material failed")
                    
                    #Translates Vertices
                    Vertices=Cube.data.vertices
                    for Vertex in Vertices:
                        Vertex.co.x+=Scene.Origin[0]
                        Vertex.co.y+=Scene.Origin[1]
                        Vertex.co.z+=Scene.Origin[2]
                           
                    #Scales Cube
                    Cube.scale=Scene.Scale
                    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
                    Cube.scale=(1,1,0)
                    
                    #Sets up animation curves
                    bpy.ops.anim.keyframe_insert_menu(type = "Scaling")
                    Cube.animation_data.action.fcurves[0].lock = not Scene.ScaleLock[0];
                    Cube.animation_data.action.fcurves[1].lock = not Scene.ScaleLock[1];
                    Cube.animation_data.action.fcurves[2].lock = not Scene.ScaleLock[2];
    
                else:
                    #Duplicates Mesh
                    bpy.ops.object.duplicate()
                    Cube=bpy.context.scene.objects.active
                
                #Sets Object Properties
                Cube.location=(XP,YP,ZP)
                Cube.pass_index=Scene.Index+i
                Cube.name=Scene.Name+str(i+1)
                
                try:
                    bpy.context.area.type = "GRAPH_EDITOR";
                    bpy.ops.graph.sound_bake(filepath=Scene.FileString, low=Scene.StartF+(Scene.StepSize*i), high=Scene.StartF+(Scene.StepSize*(i+1)));
                    bpy.context.area.type = CurrentArea
                except:
                    print("Error: Unable to bake sound to curve\n\n")
                
                XP+=Scene.DPos[0]
                YP+=Scene.DPos[1]
                ZP+=Scene.DPos[2]
            UpdateProgress("Audio Visualisation in Progress",1)
        except:
            raise
        return {'FINISHED'}

def register():
    #Registers properties to scene
    bpy.types.Scene.ScaleLock = bpy.props.BoolVectorProperty \
      (
        name = "Animated Scale",
        description = "Which axis to scale during visualisation",
        default = (False,False,True),
        subtype="XYZ"
      )
    bpy.types.Scene.VSE = bpy.props.BoolProperty \
      (
        name = "Add Audio to VSE",
        description = "Adds the audio to the VSE on visualisation",
        default = True
      )
    bpy.types.Scene.FRange = bpy.props.BoolProperty \
      (
        name = "Adjust Frame Range",
        description = "Adjusts frame range of scene so that audio visualisation fits",
        default = True
      )
    bpy.types.Scene.AObj = bpy.props.BoolProperty \
      (
        name = "Add Audio as Sound Object",
        description = "Adds the audio to the scene as a sound object on visualisation",
        default = False
      )
    bpy.types.Scene.FileString = bpy.props.StringProperty \
      (
        name = "Sound File Name",
        description = "Name and path of desired sound file",
        default = "",
        subtype='FILE_PATH'
      )
    bpy.types.Scene.StepSize = bpy.props.IntProperty \
      (
        name = "Step Size",
        description = "Range of frequencies for each cube in Hz",
        default = 250,
        min=1
      )
    bpy.types.Scene.StartF = bpy.props.IntProperty \
      (
        name = "Start Frequency",
        description = "Frequency at which to start baking at in Hz",
        default = 0,
        min=0
      )
    bpy.types.Scene.Count = bpy.props.IntProperty \
      (
        name = "Total Intervals",
        description = "Number of cubes to split sound baking into",
        default = 10,
        min=1
      )
    
    bpy.types.Scene.SFrame = bpy.props.IntProperty \
      (
        name = "Start Frame",
        description = "Frame to start audio visualisation at",
        default = 1,
        min=1
      )
    
    bpy.types.Scene.SPos = bpy.props.FloatVectorProperty \
      (
        name = "Start Position",
        description = "Position to start generating visualisation",
        default = (0,0,0)
      )
    bpy.types.Scene.DPos = bpy.props.FloatVectorProperty \
      (
        name = "Offset",
        description = "Distance to move after generating each subsequent cube",
        default = (1,0,0)
      )
    bpy.types.Scene.Scale = bpy.props.FloatVectorProperty \
      (
        name = "Size",
        description = "Size of each cube",
        default = (1,1,1)
      )
    bpy.types.Scene.Origin = bpy.props.FloatVectorProperty \
      (
        name = "Origin Offset",
        description = "Vector to translate all the vertices by",
        default = (0,0,1)
      )
    bpy.types.Scene.Name = bpy.props.StringProperty \
      (
        name = "Name",
        description = "Name for generated meshes",
        default = "Cube"
      )
    bpy.types.Scene.Index = bpy.props.IntProperty \
      (
        name = "Index",
        description = "Object Index to start at",
        default = 1,
        min = 1
      )
    bpy.types.Scene.Material = bpy.props.BoolProperty \
      (
        name = "Assign Material",
        description = "Assign a material to the generated meshes",
        default = False
      )
    bpy.types.Scene.MaterialName = bpy.props.StringProperty \
      (
        name = "Material",
        description = "The material to assign to the generated meshes",
        default = ""
      )
    bpy.utils.register_module(__name__)        

def unregister():
    #Unregisters properties
    del bpy.types.Scene.FileString
    del bpy.types.Scene.StepSize
    del bpy.types.Scene.Count
    del bpy.types.Scene.SPos
    del bpy.types.Scene.DPos
    del bpy.types.Scene.Scale
    del bpy.types.Scene.Name
    del bpy.types.Scene.Index
    del bpy.types.Scene.Origin
    del bpy.types.Scene.VSE
    del bpy.types.Scene.AObj
    del bpy.types.Scene.SFrame
    del bpy.types.Scene.ScaleLock
    del bpy.types.Scene.FRange
    del bpy.types.Scene.Material
    del bpy.types.Scene.MaterialName
    bpy.utils.unregister_module(__name__)
    
#Updates progress to console
def UpdateProgress(JobTitle, Progress, TimeLeft=0):
    Length = 50
    Block = int(round(Length*Progress))
    Msg = "\r{0}: [{1}] {2}% ".format(JobTitle, "#"*Block + "-"*(Length-Block), round(Progress*100, 2))
    if Progress >= 1: Msg += " COMPLETE              \r\n"
    elif TimeLeft>0:
        Minutes, Seconds = divmod(TimeLeft, 60)
        Hours, Minutes = divmod(Minutes, 60)
        Msg+= " %d:%02d:%02d" % (Hours, Minutes, Seconds)+" Remaining        "
    sys.stdout.write(Msg)
    sys.stdout.flush()
    
if __name__ == "__main__":
    register()