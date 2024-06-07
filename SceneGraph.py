
from PySide2 import QtWidgets, QtCore
from NodeGraphQt import NodeGraph, BaseNode
from qtmax import GetQMaxMainWindow
from pymxs import runtime as rt
from typing import List
from collections import deque
from enum import Enum
from dataclasses import dataclass

class COLOR:
    ENTITY = [50,50,50]
    NODE = [50,50,200]
    OBJECT = [200,50,50]
    CONTROLLER = [200,200,50]
    CHILDREN = [50,50,200]
    SUBANIM = [200,200,50]
    PROP = [50,200,200]


class MaxPort:
    def __init__(self, name, target, source=None, multi=False):
        self.name = name
        self.target = target
        self.source = source
        self.multi = multi

    def connect(self, source, target):
        raise NotImplementedError

    def disconnect(self, source, target):
        raise NotImplementedError

    def __repr__(self):
        return f"MaxPort('{self.name}')"

class UniversalPort(MaxPort):
    def __init__(self, name, target, connector, disconnector, source=None, multi=False):
        super().__init__(name, target, source, multi)
        self.connector = connector
        self.disconnector = disconnector

    def connect(self, source, target):
        self.connector(self, source, target)

    def disconnect(self, source, target):
        self.disconnector(self, source, target)

class MaxChildrenPort(MaxPort):
    def connect(self, source, target):
        raise NotImplementedError

    def disconnect(self, source, target):
        raise NotImplementedError


class MaxPropPort(MaxPort):
    def connect(self, source, target):
        raise NotImplementedError

    def disconnect(self, source, target):
        raise NotImplementedError


class MaxSubanimPort(MaxPort):
    def connect(self, source, target):
        raise NotImplementedError

    def disconnect(self, source, target):
        raise NotImplementedError

def connect_baseobject(max_port:"MaxPort", source:"mxs.Object", target:"mxs.node"):
    try:
        target.baseobject = source
    except Exception as err:
        print("cant connect baseobject", err)

def disconnect_baseobject(max_port:"MaxPort", source:"mxs.Object", target:"mxs.Node"):
    print("disconnect", source, "from", max_port)


def connect_child(max_port:"MaxPort", source:"mxs.Node", target:"mxs.Node"):
    try:
        rt.attachObjects(target, source)
    except Exception as err:
        print("cant disconnect baseobject", err)

def disconnect_child(max_port:"MaxPort", source:"mxs.Node", target:"mxs.Node"):
    try:
        source.parent = None
    except Exception as err:
        print("cant disconnect child", err)

def connect_property(max_port:"MaxPort", source:"mxs.Controller", target:"mxs.Entity"):
    try:
        rt.setPropertyController(target, max_port.name, source)
    except Exception as err:
        print("cant connect property", inlet, err)

def disconnect_property(max_port, source, target):
    pass

def connect_subanim_controller(max_port, source, target):
    print("connect subanim controller", max_port, source, target)
    try:
        subanim = rt.getSubAnim(target, max_port.subanim_idx)
        subanim.controller = source
    except Exception as err:
        print("cant connect subanim", inlet, err)

def disconnect_subanim_controller(max_port, source, target):
    pass

def connect_subanim_object(max_port, source, target):
    print("connect subanim object", max_port, source, target)
    try:
        subanim = rt.getSubAnim(target, max_port.subanim_idx)
        print("current object", subanim.object)
        target.setmxsprop(max_port.name, source)
        # subanim.object = source
    except Exception as err:
        print("cant connect subanim", inlet, err)

def disconnect_subanim_object(max_port, source, target):
    pass

def connect_material(max_port, source, target):
    pass

def disconnect_material(max_port, source, target):
    pass


def get_ports(max_entity):
    # print()
    # print("get subanim", max_entity)
    if rt.isValidNode(max_entity):
        # yield children 
        # yield UniversalPort(name="children", target=max_entity, source=[child for child in max_entity.children], multi=True, connector=connect_child, disconnector=disconnect_child)

        # yield tranform
        subanim = rt.getSubAnim(max_entity, 3)
        transform_port = UniversalPort(name=subanim.name, target=max_entity, source=subanim.controller, connector=connect_subanim_controller, disconnector=disconnect_subanim_controller)
        transform_port.subanim_idx = 3
        yield transform_port

        # yield UniversalPort(name="baseobject", target=max_entity, source=max_entity.baseobject, connector=connect_baseobject, disconnector=disconnect_baseobject)
        
        # yield UniversalPort(name="material", target=max_entity, source=max_entity.material, connector=connect_material, disconnector=disconnect_material)


    else:
        # for i in range(1, max_entity.numsubs+1):
        #     subanim = rt.getSubanim(max_entity, i)

            
        #     # skip subanims when a parent is a paramblock. these subanims will be included with parameters
        #     if subanim.parent != max_entity: 
        #         continue

        #     # if subanim.name in ("Transform", "Visibility"):
        #     subanim_name = rt.getSubAnimName(max_entity, i, asString=True)
        #     name_without_value = subanim_name.split(":")[0]
        #     if name_without_value:
        #         if subanim.object:
        #             port = UniversalPort(name=name_without_value, target=max_entity, source=subanim.controller, connector=connect_subanim_controller, disconnector=disconnect_subanim_controller)
        #             port.subanim_idx = i
        #             yield port


        # yield animatable properties
        for prop_name in rt.getPropNames(max_entity):
            if rt.isPropertyAnimatable(max_entity, prop_name):
                prop_controller = rt.getPropertyController(max_entity, prop_name)
                yield UniversalPort(name=str(prop_name), target=max_entity, source=prop_controller, connector=connect_property, disconnector=disconnect_property)

        # yield constraint interface
        print("interfaces for ", max_entity)
        for interface in rt.getInterfaces(max_entity):
            print(interface)


        
def bfs(roots):
    queue = deque()
    explored = set()

    # Initialize the queue with all root nodes
    for root in roots:
        if root not in explored:
            explored.add(root)
            queue.append(root)
    
    # While queue is not empty
    while queue:
        max_entity = queue.popleft()
        
        for max_port in get_ports(max_entity):
            if max_port.source is None:
                pass
            elif max_port.multi:
                for source_item in max_port.source:
                    explored.add(source_item)
                    queue.append(source_item)
            elif max_port.source not in explored:
                    explored.add(max_port.source)
                    queue.append(max_port.source)
    
    # Return the set of explored nodes
    return explored



# Node Graph Widgets
class SceneNode(BaseNode):
    __identifier__ = 'nodes.max'
    NODE_NAME = 'scene node'

    def __init__(self):
        super(SceneNode, self).__init__()





class SceneGraphDocker(QtWidgets.QDockWidget):
    def __init__(self, parent=None):
        self.node_from_anim_handle = dict() # map nodes to max entityes {anim_handle: node}
        self.port_from_handle_name = dict() # map ports to max properties... {(anim_handle, name): port}
        # qtmax.DisableMaxAcceleratorsOnFocus(self, True)

        super(SceneGraphDocker, self).__init__(parent)

        # set this widget 
        self.setAllowedAreas(QtCore.Qt.AllDockWidgetAreas)
        self.setWindowTitle("Scene Graph")
        self.setWindowFlags(QtCore.Qt.Tool)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        

        # create graph controller
        self.graph = NodeGraph()
        self.graph.register_node(SceneNode)
        self.update_graph()

        self.graph.port_connected.connect(self.on_port_connected)
        self.graph.port_disconnected.connect(self.on_port_disconnected)

        # create main window widget to hold the toolbar and the graph
        main_window = QMainWindow()
        main_window.setCentralWidget( self.graph.widget)

        # create the toolbar
        toolBar = main_window.addToolBar("hello")
        action = toolBar.addAction("->")
        self.setWidget(main_window)

        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum);
        self.setMinimumSize(512,510);

    def fitInView(self, nodes=[]):
        viewer = self.graph.widget.widget(0)
        scene = self.graph.scene()

        viewer.fitInView( scene.sceneRect() )

    def showEvent(self, event):
        self.register_callbacks()

    def closeEvent(self, event):
        self.unregister_callbacks()

    def on_port_connected(self, inlet, outlet):
        # if isinstance(inlet.data, MaxChildrenPort):
        #     try:
        #         # get target_port
        #         source_entity = outlet.node().data

        #         target_entity = inlet.node().data
        #         target_max_port = inlet.data

        #         rt.attachObjects(target_entity, source_entity)
        #         # source_entity.parent = target_entity
        #     except Exception as err:
        #         print("cant connect port", err)
        #         outlet.disconnect_from(inlet)

        if isinstance(inlet.data, MaxPropPort):
            try:
                source_entity = outlet.node().data
                target_entity = inlet.node().data
                target_port = inlet.data

                rt.setPropertyController(target_entity, target_port.name, source_entity)
            except Exception as err:

                print("cant connect port", inlet, err)
                outlet.disconnect_from(inlet)

        elif isinstance(inlet.data, MaxSubanimPort):
            try:
                raise NotImplementedError
            except Exception as err:
                print("cant connect port", err)
                outlet.disconnect_from(inlet)

        elif isinstance(inlet.data, UniversalPort):
            try:
                port = inlet.data
                source_entity = outlet.node().data
                target_entity = inlet.node().data
                port.connect(source_entity, target_entity)
            except Exception as err:
                print("cant connect port", err)


    def on_port_disconnected(self, inlet, outlet):
        if isinstance(inlet.data, MaxChildrenPort):
            try:
                # get target_port
                source_entity = outlet.node().data

                target_max_port = inlet.data
                target_entity = inlet.node().data
                

                print("disconnect", source_entity, "to", target_entity, target_max_port)
                source_entity.parent = None
            except Exception as err:
                print("cant disconnect port", err)
                # TODO handle port that cannot be disconnected?

        if isinstance(inlet.data, UniversalPort):
            try:
                port = inlet.data
                source_entity = outlet.node().data
                target_entity = inlet.node().data
                port.disconnect(source_entity, target_entity)
            except Exception as err:
                print("cant connect port", err)

    def register_callbacks(self):
        # delete old callbacks
        self.unregister_callbacks()

        rt.callbacks.addScript(rt.Name('postNodeSelectOperation'), self.node_selected_callback, id=rt.Name('MySelectionCallbacks'))
        # rt.callbacks.addScript(rt.Name('nodeCreated'), self.node_created_callback, id=rt.Name('MyCreatedCallbacks'))
        
        rt.callbacks.addScript(rt.Name('nodeLinked'), self.node_linked_callback, id=rt.Name('MyCallbacks'))
        rt.callbacks.addScript(rt.Name('nodeUnlinked'), self.node_unlinked_callback, id=rt.Name('MyCallbacks'))

    def unregister_callbacks(self):
        rt.callbacks.removeScripts(id=rt.name('MyCreatedCallbacks'))
        rt.callbacks.removeScripts(id=rt.name('MySelectionCallbacks'))
        rt.callbacks.removeScripts(id=rt.name('MyCallbacks'))

    # Max Callbacks
    def node_created_callback(self):
        notification = rt.callbacks.notificationParam()

    def node_selected_callback(self):
        notification = rt.callbacks.notificationParam()
        self.update_graph()

    def node_linked_callback(self):
        notification = rt.callbacks.notificationParam()
        self.update_graph()

    def node_unlinked_callback(self):
        notification = rt.callbacks.notificationParam()
        self.update_graph()

    def create_node_from_entity(self, max_entity):
        # create the node from max object
        node = BaseNode()#self.graph.create_node('nodes.max.SceneNode', max_entity.name, selected=False, push_undo=False)
        node.data = max_entity
        self.node_from_anim_handle[rt.GetHandleByAnim(max_entity)] = node

        # create input ports
        for max_port in get_ports(max_entity):
            input_port = node.add_input(max_port.name, multi_input=max_port.multi)
            input_port.data=max_port
            self.port_from_handle_name[(rt.GetHandleByAnim(max_entity), max_port.name)] = input_port

        # create output ports
        output_port = node.add_output('self')


        # add graph to node
        self.graph.add_node(node)
        try:
            node.set_name(name=f"{max_entity.name}")
        except AttributeError:
            node.set_name(name=f"{rt.getClassName(max_entity)}")

        # return
        return node

    def update_graph(self):
        for node in self.graph.all_nodes():
            for inlet in node.input_ports():
                inlet.clear_connections(emit_signal=False)
            for outlet in node.output_ports():
                outlet.clear_connections(emit_signal=False)
            self.graph.remove_node(node)

        self.node_from_anim_handle = dict()

        # create nodes
        selection = [obj for obj in rt.selection]
        scene_objects = bfs(selection)
        
        # add nodes
        for max_entity in scene_objects:
            node = self.create_node_from_entity(max_entity)

        # create connections
        for max_entity in scene_objects:
            target_node = self.node_from_anim_handle[rt.GetHandleByAnim(max_entity)]

            for max_port in get_ports(max_entity):
                target_port = target_node.get_input(max_port.name)
                if max_port.source is None:
                    pass
                elif max_port.multi:
                    for source_entity in max_port.source:
                        source_node = self.node_from_anim_handle[rt.GetHandleByAnim(source_entity)]
                        source_port = source_node.get_output(0)
                        source_port.connect_to(target_port, push_undo=False, emit_signal=False)
                else:
                    source_entity = max_port.source
                    source_node = self.node_from_anim_handle[rt.GetHandleByAnim(source_entity)]
                    source_port = source_node.get_output(0)
                    source_port.connect_to(target_port, push_undo=False, emit_signal=False)

        self.graph.auto_layout_nodes()
        # self.fitInView()
        # self.graph.center_on()


if __name__ == "__main__":
    from PySide2.QtWidgets import *

    max_window = GetQMaxMainWindow()
    w = max_window.findChild(QDockWidget, "TheSceneGraph")
    if w:
        w.deleteLater()

    w = SceneGraphDocker(max_window)
    w.setObjectName("TheSceneGraph")
    max_window.addDockWidget(QtCore.Qt.LeftDockWidgetArea,w)
    w.move(100,0)
    w.setFloating(False)
    w.show()