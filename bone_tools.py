# maxscript
from pymxs import runtime as rt

# Qt
from qtmax import GetQMaxMainWindow
from PySide2 import QtWidgets, QtCore

def get_x_axis(obj):
	tm = obj.transform
	x_axis_vector = rt.point3(tm[0][0], tm[1][0], tm[2][0])
	return rt.normalize(x_axis_vector)

def divide_bone(bone, num_segments):   
	# Get the direction vector of the bone
	x_axis = get_x_axis(bone)
	start_pos = bone.position
	end_pos = start_pos+x_axis * bone.length
	child_bone = bone.children
	
	# Create new bones
	new_bones = []
	current_start = start_pos
	segment_length = bone.length/(num_segments)


	bone.length = segment_length
	current_bone = bone
	for i in range(1, num_segments):
		current_start = start_pos + x_axis * segment_length*(i)
		current_end =   start_pos + x_axis * segment_length*(i+1)
		z_axis=rt.point3(0,0,1)
		new_bone = rt.BoneSys.createBone(current_start, current_end, z_axis)
		new_bone.parent=current_bone
		current_bone = new_bone
		current_start = current_end

	# reconnect children bones
	for child in bone.children:
		child.parent = current_bone



if __name__ == "__main__":
	divide_bone(rt.selection[0],6)