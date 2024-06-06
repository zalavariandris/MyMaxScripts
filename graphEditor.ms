rollout NodeGraphEditor "Node Graph Editor"
(
    button btnAddNode "Add Node" width:100
    button btnClear "Clear" width:100
    dotNetControl graph "System.Windows.Forms.Panel" width:600 height:400

    struct Node (
        id,
        name,
        position,
        size,
        inputs,
        outputs
    )
	
	struct Connection (
		startNodeID,
		endNodeID
	)
	
	fn addConnection startNodeID endNodeID =
	(
		local newConnection = Connection startNodeID endNodeID
		append connections newConnection
		NodeGraphEditor.graph.Invalidate()
	)

    global nodes = #()
    global connections = #()
    global selectedNode = undefined
    global offset = [0,0]

	fn drawGraph g =
	(
		g.Clear (dotNetClass "System.Drawing.Color").White

		-- Draw connections
		local pen = dotNetObject "System.Drawing.Pen" (dotNetClass "System.Drawing.Color").Black
		for conn in connections do
		(
			local startNode = nodes[conn.startNodeID]
			local endNode = nodes[conn.endNodeID]
			local startPoint = [startNode.position[1] + startNode.size[1], startNode.position[2] + startNode.size[2] / 2]
			local endPoint = [endNode.position[1], endNode.position[2] + endNode.size[2] / 2]
			g.DrawLine pen (dotNetObject "System.Drawing.Point" startPoint[1] startPoint[2]) (dotNetObject "System.Drawing.Point" endPoint[1] endPoint[2])
		)

		-- Draw nodes
		for node in nodes do
		(
			local rect = dotNetObject "System.Drawing.Rectangle" node.position[1] node.position[2] node.size[1] node.size[2]
			g.FillRectangle ((dotNetClass "System.Drawing.Brushes").LightBlue) rect
			g.DrawRectangle pen rect
			--g.DrawString node.name (dotNetObject "System.Drawing.Font" "Arial" 10) ((dotNetClass "System.Drawing.Brushes").Black) rect
		)
	)

    fn addNode name position =
    (
		local nodeID = nodes.count+1
        local newNode = Node id:nodeID name:name position:position size:[100, 50] inputs:#() outputs:#()
        append nodes newNode
        NodeGraphEditor.graph.Invalidate()
		return nodeID
    )

    fn onMouseDown sender args =
    (
        local mousePos = [args.X, args.Y]
        for node in nodes do
        (
            local nodeRect = [node.position[1], node.position[2], node.size[1], node.size[2]]
            if (mousePos[1] >= nodeRect[1] and mousePos[1] <= nodeRect[1] + nodeRect[3] and mousePos[2] >= nodeRect[2] and mousePos[2] <= nodeRect[2] + nodeRect[4]) then
            (
                selectedNode = node
                offset = mousePos - node.position
                exit
            )
        )
    )

    fn onMouseMove sender args =
    (
        if selectedNode != undefined do
        (
            selectedNode.position = [args.X, args.Y] - offset
            NodeGraphEditor.graph.Invalidate()
        )
    )

    fn onMouseUp sender args =
    (
        selectedNode = undefined
    )

    on btnAddNode pressed do
    (
        addNode "Node" [50, 50]  -- Add a node at position (50, 50)
    )

    on btnClear pressed do
    (
        nodes = #()
        connections = #()
        NodeGraphEditor.graph.Invalidate()
    )

    on graph paint sender args do
    (
        drawGraph args.Graphics
    )
	
	on graph MouseDown sender args do 
	(
		onMouseDown sender args
	)
	
	on graph MouseMove sender args do 
	(
		onMouseMove sender args
	)
	
	on graph MouseUp sender args do 
	(
		onMouseUp sender args
	)
	
    fn enableDoubleBuffering control =
    (
        local type = control.GetType()
		local binding_flags = dotnetclass "System.Reflection.BindingFlags"
		local flags = dotnet.combineenums binding_flags.Instance binding_flags.NonPublic
        local prop = type.GetProperty "DoubleBuffered" flags
        prop.SetValue control true (dotNetObject "System.Object[]" 0)
    )

    on NodeGraphEditor open do
    (
		enableDoubleBuffering graph
        local n1 = addNode "Node1" [50, 50]
		local n2 = addNode "Node2" [200, 50]
		addConnection n1 n2
		
    )
)

createdialog NodeGraphEditor width:650 height:650
