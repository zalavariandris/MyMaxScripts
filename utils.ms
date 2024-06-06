include "setKeysToStepped.mxs"
include "disableRenderMesh.mxs"
include "selectObjectSet.mxs"
include "setSelectedKeys.mxs"

-- Define the rollout panel
rollout AndrisAnimationRollout "And animation" (
    -- Define the button
    button setSteppedButton "Set Selected Keys to Stepped" width:200

    -- Define the button event handler
    on setSteppedButton pressed do (
        setKeysToStepped selection
    )
	
	-- Define the button
    button disableRenderMeshBtn "disable Viewport Mesh" width:200

    -- Define the button event handler
    on disableRenderMeshBtn pressed do (
        disableRenderMeshForShapes selection
    )
	
	-- Define the button
    button selectObjectsSetBtn "Select object set" width:200

    -- Define the button event handler
    on selectObjectsSetBtn pressed do (
        selectObjectsSet selection
    )
)

-- Create the dialog
createDialog AndrisAnimationRollout