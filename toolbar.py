from PySide2 import QtWidgets
from qtmax import GetQMaxMainWindow
from pymxs import runtime as rt

from pymxs import runtime as mxs
from typing import List

def get_selection_sets_for_objects(objs):
	# -- Iterate through all selection sets
	for selectionSet in mxs.selectionSets:
		# -- Check if the object is in the current selection set
		for obj in objs:
			if obj in selectionSet:
				yield selectionSet


def select_object_set(objs):
	objectsToSelect = []
	for selectionSet in get_selection_sets_for_objects(objs):
		objectsToSelect += [obj for obj in selectionSet]
	mxs.select(objectsToSelect)


def get_subanims(obj, recursive=True)->List:
	subanims = []
	if not obj:
		return []
	for i in range(1, obj.numsubs+1):
		subanim = mxs.getSubAnim(obj, i)
		if subanim:
			subanims.append(subanim)

			if recursive:
				subanims+=get_subanims(subanim)
		
	return subanims

def get_keys(subanims):
	allKeys = []
	for sa in subanims:
		IsBezierFloat = mxs.classOf(sa.controller) == mxs.Bezier_Float
		HasKeys = sa.keys != None
		if HasKeys:
			allKeys+=sa.keys
	return allKeys

def set_selected_keys(kind=mxs.Name("step")):
	subanims = []
	for obj in mxs.selection:
		subanims+=get_subanims(obj, recursive=True)

	bezier_controllers = [sa.controller for sa in subanims if mxs.classOf(sa.controller) == mxs.Bezier_Float]
	selectedKeys = []
	for controller in bezier_controllers:
		for key in controller.keys:
			if key.selected:
				selectedKeys.append(key)

	for key in selectedKeys:
		key.inTangentType = mxs.Name(kind)
		key.outTangentType = mxs.Name(kind)

#
# CREATE TOOLBAR
#

# update toolbar in 3dsmax
main_window = GetQMaxMainWindow()
toolbar = main_window.findChild(QtWidgets.QToolBar, "AndrisTB")
if toolbar:
	toolbar.deleteLater()

toolbar = QtWidgets.QToolBar("Andris tools", main_window)
toolbar.setObjectName("AndrisTB")

# create actions
select_object_set_action = QtWidgets.QAction("Select Object Set", toolbar)
select_object_set_action.triggered.connect(lambda val: select_object_set(rt.selection))
toolbar.addAction(select_object_set_action)

set_step_keys_action = QtWidgets.QAction("Step keys", toolbar)
set_step_keys_action.triggered.connect(lambda val: set_selected_keys(mxs.Name("step")))
toolbar.addAction(set_step_keys_action)

set_auto_keys_action = QtWidgets.QAction("Auto keys", toolbar)
set_auto_keys_action.triggered.connect(lambda val: set_selected_keys(mxs.Name("auto")))
toolbar.addAction(set_auto_keys_action)

# add toolbar
main_window.addToolBar(toolbar)
toolbar.show()