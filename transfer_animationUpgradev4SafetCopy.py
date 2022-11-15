bl_info = {
    
    'name': 'transfer_animation',
    'blender': (3, 2, 0),
    'category': 'Animation',
    'version': (2, 0, 0),
    'author': 'Emil Johansson',
    'description': 'Animation Retargeting'
}
import bpy
import mathutils as mathutils
import math as math
from bpy.types import Operator, OperatorFileListElement
from bpy.props import CollectionProperty, StringProperty
from decimal import *

getcontext().prec = 6
#globals
scene = bpy.context.scene

sourceSkeletonName = ""
targetSkeletonName = ""

mappedBones = {} #Target bones are keys and mapped Source bones are values

sourceBoneNameList = [] #Names
sourceBindPoses = []    #BindPoses
sourcePoseBoneList = [] #Pose bones
sourceRotationList = [] #Rotationmatrices
sourceRestList = []     #Bindposes
sourceOrientationList = [] #Orientationmatrices
sourceParentList = []      #Parentchain
sourceEditBoneList = [] #Edit bones

sourceKeys = []         #keyframes
targetBoneNameList = [] #Names
targetRestList = []     #Bindposes
targetPoseBoneList = [] #Pose bones
targetOrientationList = [] #Orientationmatrices
targetParentList = []      #Parentchain
targetEditBoneList = [] #Edit bones
targetRotationList = [] #Rotationmatrices

#Bone orientation data
sourceRollMap = {}
sourceAxisMap = {}
sourceHeadMap = {}
sourceTailMap = {}


#Functions

def CalcParentMatrices(currentBoneIndex, usesource):
    
    parent = mathutils.Matrix.Identity(4)
    if usesource:
        if sourcePoseBoneList[currentBoneIndex].parent != None:
            parentIndex = sourceBoneNameList.index(sourcePoseBoneList[currentBoneIndex].parent.name)
            parent = parent @ sourceRotationList[0][parentIndex]#sourceRestList[parentIndex]
            parent = parent @ sourceOrientationList[0][parentIndex]
            parent = parent @ CalcParentMatrices(parentIndex, usesource)
            
        
            
    else:
        if targetPoseBoneList[currentBoneIndex].parent != None:
            parentIndex = targetBoneNameList.index(targetPoseBoneList[currentBoneIndex].parent.name)
            parent = parent @ targetRotationList[parentIndex]#targetRestList[parentIndex]
            parent = parent @ targetOrientationList[parentIndex]
            parent = parent @ CalcParentMatrices(parentIndex, usesource)
          
    
    return parent

def ReadFile(): #To simplify a textfile can be added with the names of the corresponding bones to match
    path = "//skeletonMap.txt"

    try:
        f = open(bpy.path.abspath(path), "r")
        for x in f:
            line = x
            if line[0]=="#":
                continue
            bones = line.split(" ")
            bones[1] = bones[1].strip('\n')
            if bones[0] in mappedBones.keys():
                
                if bones[1] in sourceBoneNameList:
                    mappedBones[bones[0]] = bones[1]
                else:
                    mappedBones[bones[0]] = "none"
        f.close() 
    except:
        return    




def ChangeOrientation():
    
    sourceSkeleton = bpy.data.objects[sourceSkeletonName]
    targetSkeleton = bpy.data.objects[targetSkeletonName]
   
    bpy.ops.object.mode_set(mode='EDIT')    
    
    sourceRollMap.clear()
    sourceHeadMap.clear()
    sourceTailMap.clear()
    sourceAxisMap.clear()    
    for ebone in sourceSkeleton.data.edit_bones:
        length = ebone.vector.magnitude
        dir = (ebone.head - ebone.tail).normalized()
        ebone.use_local_location = True
        mat = ebone.matrix
        bpy.context.object.convert_space( 
                matrix=mat, 
                from_space='LOCAL', 
                to_space='WORLD')
        sourceRollMap[ebone.name] = ebone.roll
        sourceHeadMap[ebone.name] = mat.to_translation()
        sourceTailMap[ebone.name] = sourceHeadMap[ebone.name]-(length*dir)
        sourceAxisMap[ebone.name] = (sourceHeadMap[ebone.name] - sourceTailMap[ebone.name]).normalized()
        
    
    
    
    #Need to go from the root bones first to change the bone orients
    chainLists= []
    for x in range(0, len(targetSkeleton.data.edit_bones)):
        if len(targetSkeleton.data.edit_bones[x].children)==0:
            list = GetParentChains(x, False)
            list.reverse()
            list.append(x)
            chainLists.append(list)
    taken = []
    for chain in chainLists:
        
        for listindex, targetIndex in enumerate(chain):
            if targetIndex in taken:
                
                continue
           
            sourceName = mappedBones[targetBoneNameList[targetIndex]]
            if sourceName in sourceBoneNameList:
                sourceIndex = sourceBoneNameList.index(sourceName)
                
                targetSkeleton.data.edit_bones[targetIndex].roll = sourceRollMap[sourceBoneNameList[sourceIndex]]
                b = sourceAxisMap[sourceBoneNameList[sourceIndex]] #normalized source direction
                a = targetSkeleton.data.edit_bones[targetIndex].head - targetSkeleton.data.edit_bones[targetIndex].tail
                a.normalize() #normalized target direction head minus tail
                axis = b.cross(a)
                axis.normalize()
                if b.dot(a)<-1 or b.dot(a)>1:
                    continue
                angle = math.acos(b.dot(a))
                

                Q = mathutils.Quaternion(axis, angle)
                R = Q.to_matrix()
  
                
                dir = targetSkeleton.data.edit_bones[targetIndex].head - targetSkeleton.data.edit_bones[targetIndex].tail
                
                dir = dir @ R
                targetSkeleton.data.edit_bones[targetIndex].head = dir + targetSkeleton.data.edit_bones[targetIndex].tail
                

            taken.append(targetIndex)
            
    
    bpy.ops.object.mode_set(mode='POSE')




def CalcFinalMatrix(frameIndex, targetBoneIndex):
    
    sourceName = mappedBones[targetBoneNameList[targetBoneIndex]]
    
    sourceIndex = sourceBoneNameList.index(sourceName)
    
    
    sworld = bpy.context.object.convert_space(pose_bone=sourcePoseBoneList[sourceIndex],
    matrix = sourceRotationList[frameIndex][sourceIndex], from_space = 'POSE', to_space='WORLD')
    
  
    
    tpose = bpy.context.object.convert_space(pose_bone=targetPoseBoneList[targetBoneIndex],
    matrix = sworld, from_space = 'WORLD', to_space='POSE')
    
    
 
    
    return tpose
    
    
    
    



def GetParentChains(currentBoneIndex, fromSource): #Go backwards to get a 2D list of parentindices
    chain = []
    
    if fromSource:
        if sourcePoseBoneList[currentBoneIndex].parent != None:
            parentIndex = sourceBoneNameList.index(sourcePoseBoneList[currentBoneIndex].parent.name)
            chain.append(parentIndex)
            for x in GetParentChains(parentIndex,fromSource):
                chain.append(x)
    else:
        if targetPoseBoneList[currentBoneIndex].parent != None:
            parentIndex = targetBoneNameList.index(targetPoseBoneList[currentBoneIndex].parent.name)
            chain.append(parentIndex)
            for x in GetParentChains(parentIndex,fromSource):
                chain.append(x)
    return chain




def CalcRotationandParents(useSource):
    

    if useSource:
    
        bpy.ops.object.mode_set(mode='POSE')
        
           
        for frame in sourceKeys:
            scene.frame_set(frame)
            temp = []     
            for  pbone in sourcePoseBoneList:    
                temp.append(pbone.matrix)
                
            sourceRotationList.append(temp)
        for index, pbone in enumerate(sourcePoseBoneList):
            sourceRestList.append(pbone.bone.matrix_local)
            sourceParentList.append(CalcParentMatrices(index, True)) 
            
    else:
        
        bpy.ops.object.mode_set(mode='POSE')
        scene.frame_set(0)
        for index, pbone in enumerate(targetPoseBoneList):
            targetRestList.append(pbone.bone.matrix_local)
            targetRotationList.append(pbone.matrix)
            targetParentList.append(CalcParentMatrices(index, False))    
        
             
       
                
        


    




def ChooseSource():
    
    sourceSkeleton = [obj for obj in bpy.context.selected_objects if obj.type == 'ARMATURE']
    sourceSkeleton = sourceSkeleton[0]
    global sourceSkeletonName
    sourceSkeletonName = sourceSkeleton.name
    
    action = bpy.data.objects[sourceSkeletonName].animation_data.action
    

    for f in range(scene.frame_start, scene.frame_end+1):
        #frames = []
    #for keyframe in action.fcurves[0].keyframe_points:
            #frames.append(keyframe.co.x)
        sourceKeys.append(f)       
            
   
    bpy.ops.object.mode_set(mode='POSE')
        
   
            
    for index, bone in enumerate(sourceSkeleton.pose.bones):
        sourcePoseBoneList.append(bone)
        sourceBoneNameList.append(bone.name)
        
    
    bpy.ops.object.mode_set(mode='EDIT')    
        
    for ebone in sourceSkeleton.data.edit_bones:
        length = ebone.vector.magnitude
        dir = (ebone.head - ebone.tail).normalized()
        ebone.use_local_location = True
        mat = ebone.matrix
        bpy.context.object.convert_space( 
                matrix=mat, 
                from_space='LOCAL', 
                to_space='WORLD')
        sourceRollMap[ebone.name] = ebone.roll
        sourceHeadMap[ebone.name] = mat.to_translation()
        sourceTailMap[ebone.name] = sourceHeadMap[ebone.name]-(length*dir)
        sourceAxisMap[ebone.name] = (sourceHeadMap[ebone.name] - sourceTailMap[ebone.name]).normalized()
        sourceEditBoneList.append(ebone)
        
   
 
    for frame in sourceKeys:
        scene.frame_set(frame)
        temp = [] 
        for ebone in sourceSkeleton.data.edit_bones:
            
            temp.append(ebone.matrix)
        sourceOrientationList.append(temp)
        
        

    CalcRotationandParents(True)

    


def ChooseTarget(): #Needs to be chosen after source
    
    
    targetSkeleton = [obj for obj in bpy.context.selected_objects if obj.type == 'ARMATURE']
    targetSkeleton = targetSkeleton[0]
    global targetSkeletonName
    targetSkeletonName = targetSkeleton.name

    bpy.ops.object.mode_set(mode='POSE')
    
    for index, bone in enumerate(targetSkeleton.pose.bones):
        targetPoseBoneList.append(bone)
        targetBoneNameList.append(bone.name)
        
        

        mappedBones[bone.name] = "none"
        if index < len(sourcePoseBoneList):
            mappedBones[bone.name] = sourcePoseBoneList[index].name
        

    bpy.ops.object.mode_set(mode='EDIT')    
        
    for ebone in targetSkeleton.data.edit_bones:
        targetOrientationList.append(ebone.matrix)
        
    CalcRotationandParents(False)
   





def transfer():
    targetSkeleton = bpy.data.objects[targetSkeletonName]
    sourceSkeleton = bpy.data.objects[sourceSkeletonName]
    
    
    #CalcRotationandOrientation(True)
    #ChangeOrientation()
    #CalcRotationandOrientation(False)

    bpy.data.objects[targetSkeletonName].location = bpy.data.objects[sourceSkeletonName].location
    bpy.ops.object.mode_set(mode='POSE')

    for i, frame in enumerate(sourceKeys):
        scene.frame_set(frame)
   
        for boneIndex, bone in enumerate(targetSkeleton.pose.bones):
            sourceName = "none"
            sourceName = mappedBones[targetBoneNameList[boneIndex]]
            ChangeOrientation()  
            if sourceName in sourceBoneNameList:
                if boneIndex == 0 and bone.parent == None: #Get the root bone translation data
                    
                    finaMat = CalcFinalMatrix(i, boneIndex)
                    rot = finaMat.to_quaternion()
                    trans = finaMat.to_translation()
                    t = trans
                    s = bone.matrix.to_scale() #I never change the scale
                    bone.matrix = mathutils.Matrix().LocRotScale(t, rot, s)
                    bone.keyframe_insert(data_path="location", frame=frame)
                    bone.keyframe_insert(data_path="rotation_quaternion", frame=frame)
                    bone.keyframe_insert(data_path="scale", frame=frame)
                else:
                        
                    finaMat = CalcFinalMatrix(i, boneIndex)
                    rot = finaMat.to_quaternion()
                    trans = finaMat.to_translation()
                    t = bone.matrix.to_translation() 
                    s = bone.matrix.to_scale() #I never change the scale
                        
                    bone.matrix = mathutils.Matrix().LocRotScale(t, rot, s)
                    bone.keyframe_insert(data_path="location", frame=frame)
                    bone.keyframe_insert(data_path="rotation_quaternion", frame=frame)
                    bone.keyframe_insert(data_path="scale", frame=frame)
                
            
    
    
  
#Classes, operators and properties

bpy.types.Scene.selectionProp = bpy.props.StringProperty(name='BoneID',description='Write the bone to map')
            
class Select(bpy.types.Operator):
    
    bl_idname = 'opr.object_select_operator'
    bl_label = 'Select'
    boneID: bpy.props.IntProperty(default=-1, name = "nr")
    selection: bpy.props.StringProperty(default='none', name = "selection")
    mappedBone: bpy.props.StringProperty(default='none', name = "mapped")
    boneName: bpy.props.StringProperty(default="none", name = "name")
       

    def execute(self, context):
        if self.selection == "none":
            return {'FINISHED'}
        if self.boneName in mappedBones.keys():
            if self.selection in sourceBoneNameList:
                mappedBones[self.boneName] = self.selection
            elif self.selection == "null":
                mappedBones[self.boneName] = "none"
                        
             
             
        return {'FINISHED'}           
            
    

class Source(bpy.types.Operator):
    
    bl_idname = 'opr.object_source_operator'
    bl_label = 'Select Source'
    def execute(self, context):
        ChooseSource()  
        return {'FINISHED'}
    
class Target(bpy.types.Operator):
    
    bl_idname = 'opr.object_target_operator'
    bl_label = 'Select Target'
    def execute(self, context):
        ChooseTarget()
        ReadFile()  #If there is a file this overrides the mapping
        return {'FINISHED'}    
    
class Transfer(bpy.types.Operator):
    
    bl_idname = 'opr.object_transfer_operator'
    bl_label = 'Transfer'
    def execute(self, context):
        transfer()  
        return {'FINISHED'}
    
class panel(bpy.types.Panel):
    
    bl_idname = 'VIEW3D_PT_main_panel'
    bl_label = 'Panel'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    
    def draw(self, context):
        self.layout.label(text='Change the number of frames')
        self.layout.label(text='Select source first then target.')
        self.layout.label(text='Enter the word null to map a bone to nothing.')
        self.layout.operator(Source.bl_idname, text='Select Source')
        self.layout.operator(Target.bl_idname, text='Select Target')
        self.layout.operator(Transfer.bl_idname, text='Transfer')

class panelTargetBones(bpy.types.Panel):
    
    bl_idname = 'VIEW3D_PT_target_panel'
    bl_label = 'TargetBones'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    
    def draw(self, context):
        self.layout.prop(context.scene, "selectionProp")
        for i, bone in enumerate(targetPoseBoneList):
            op = self.layout.operator(Select.bl_idname, text=str(i)+" "+bone.name)
            self.layout.prop(op, 'mappedBone')
            op.mappedBone = mappedBones[bone.name]   
            op.selection = bpy.context.scene.selectionProp 
            op.boneName = bone.name
            op.boneID = i
           
            
CLASSES = [panelTargetBones, panel,Source,Target,Transfer,Select]


def register():
    for klass in CLASSES:
        bpy.utils.register_class(klass)

def unregister():
    for klass in CLASSES:
        bpy.utils.unregister_class(klass)
    
    
if __name__ == '__main__':
    register()



















        
    
    

        
            
    


        

        

            
