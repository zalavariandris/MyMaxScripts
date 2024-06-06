import pymxs
rt = pymxs.runtime

def get_selection_sets_for_objects(objs):
	# -- Iterate through all selection sets
	for selectionSet in rt.selectionSets:
		# -- Check if the object is in the current selection set
		for obj in objs:
			if obj in selectionSet:
				yield selectionSet


def select_object_set(objs):
	objectsToSelect = []
	for selectionSet in get_selection_sets_for_objects(objs):
		objectsToSelect += [obj for obj in selectionSet]
	rt.select(objectsToSelect)