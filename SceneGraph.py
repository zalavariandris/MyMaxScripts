# maxscript
from pymxs import runtime as rt

# Qt
from qtmax import GetQMaxMainWindow
from PySide2 import QtWidgets, QtCore
from PySide2.QtWidgets import *
from PySide2.QtCore import *

# graph editor
import NodeGraphQt
from NodeGraphQt import NodeGraph, BaseNode

# python standard libraries
from typing import List, Any
from collections import deque
from enum import Enum
from dataclasses import dataclass


class COLOR:
    ENTITY = [236/3,236/3,239/3]
    NODE =   [165/3,216/3,255/3]
    OBJECT = [252/3,194/3,215/3]

    CONTROLLER = [255/3,236/3,153/3]
    CHILDREN =   [165/3,216/3,250/3]
    SUBANIM =    [255/3,236/3,153/3]
    PROP =       [238/3,190/3,250/3]
    INTERFACE =  [150/3,242/3,215/3]


class MaxBaseEntity:
    def __init__(self, wrap:"mxs.Entity"):
        self.wrapped = wrap

    def __repr__(self):
        return f"{self.__class__.__name__}({self.wrapped})"

    def color(self):
        return COLOR.ENTITY

    def name(self):
        try:
            return f"{self.wrapped.name}"
        except AttributeError:
            return f"{rt.getClassName(self.wrapped)}"

    @staticmethod
    def create(native_entity):
        if is_node(native_entity):
            return MaxNodeEntity(wrap=native_entity)

        elif is_baseobject(native_entity):
            return MaxBaseObject(native_entity)
        elif is_list_controller(native_entity):
            return MaxListController(wrap=native_entity)
        elif is_controller(native_entity):
            if is_expression_controller(native_entity):
                return MaxIExprController(wrap=native_entity)
            elif is_script_controller(native_entity):
                return MaxScriptController(wrap=native_entity)
            elif is_wire_controller(native_entity):
                return MaxWireController(wrap=native_entity)
            else:
                return MaxController(wrap=native_entity)

        else:
            return MaxBaseEntity(wrap=native_entity)

    @staticmethod
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
            
            for max_port in MaxBaseEntity.create(max_entity).get_ports():
                for source_item in max_port.get_sources():
                    explored.add(source_item)
                    queue.append(source_item)
        
        # Return the set of explored nodes
        return explored

    def get_subanim_controller_ports(self):
        for subanim_idx in range(1, self.wrapped.numsubs+1):
            yield SubanimControllerPort(owner=self.wrapped, subanim_idx=subanim_idx)

    def get_animatable_property_ports(self):
        for prop_name in rt.getPropNames(self.wrapped):
            if rt.isPropertyAnimatable(self.wrapped, prop_name):
                yield PropertyControllerPort(owner=self.wrapped, prop_name=prop_name)

    def get_ports(self):
        if rt.isValidNode(self.wrapped):
            """Yield Children"""
            yield ChildrenPort(owner=self.wrapped)
            yield SubanimControllerPort(owner=self.wrapped, subanim_idx=3)
            yield BaseObjectPort(owner=self.wrapped)
            yield MaterialPort(owner=self.wrapped)

        else:
            """
            Yield Subanims
            """
            for port in self.get_subanim_controller_ports():
                yield port

            """
            Yield animatable Properties
            """
            for prop in self.get_animatable_property_ports():
                yield prop

            """
            Yield Interfaces
            """
            """IExprCtrl"""
            # if rt.classOf(self.wrapped) in [rt.Float_Expression, rt.Point3_Expression, rt.Position_Expression, rt.Scale_Expression]:
            #     for i in range(1, self.wrapped.NumScalars()+1):
            #         if self.wrapped.GetScalarType(i) == rt.Name("scalarTarget"):
            #             yield IExprScalarTargetPort(owner=self.wrapped, idx=i)
            #             # subanim = self.wrapped.GetScalarTarget(i)
            #             # scalar_name = self.wrapped.GetScalarName(i)
            #             # yield MaxPort(name=str(scalar_name), target = self.wrapped, source=subanim.controller)

            #     for i in range(1, self.wrapped.NumVectors()+1):
            #         if self.wrapped.GetVectorType(i) == rt.Name("vectorTarget"):
            #             yield IExprVectorTargetPort(owner=self.wrapped, idx=i)


class MaxNodeEntity(MaxBaseEntity):
    def get_ports(self):
        """Yield Children"""
        yield ChildrenPort(owner=self.wrapped)
        yield SubanimControllerPort(owner=self.wrapped, subanim_idx=3)
        yield BaseObjectPort(owner=self.wrapped)
        yield MaterialPort(owner=self.wrapped)

    def color(self):
        return COLOR.NODE


class MaxMaterial(MaxBaseEntity):
    def get_ports(self):
        for port in super().get_ports():
            yield port


class MaxBaseObject(MaxBaseEntity):
    def get_ports(self):
        for port in self.get_animatable_property_ports():
            yield port

    def color(self):
        return COLOR.OBJECT


class MaxController(MaxBaseEntity):
    def get_ports(self):
        # for port in self.get_animatable_property_ports():
        #     yield port
        for port in self.get_subanim_controller_ports():
            yield port

    def color(self):
        return COLOR.CONTROLLER


class MaxIExprController(MaxController):
    """
    maxscript docs: https://help.autodesk.com/view/MAXDEV/2022/ENU/?guid=GUID-FC68369C-232D-4040-B223-F67978A4A5A1
    """
    def get_ports(self):
        for i in range(1, self.wrapped.NumScalars()+1):
            scalarType = self.wrapped.GetScalarType(i)
            if scalarType in[rt.Name("scalarTarget"), rt.Name("scalarConstant")]:
                yield IExprScalarTargetPort(owner=self.wrapped, idx=i)

        for i in range(1, self.wrapped.NumVectors()+1):
            vectorType = self.wrapped.GetVectorType(i)
            if vectorType in [rt.Name("vectorTarget"), rt.Name("vectorConstant")]:
                yield IExprVectorTargetPort(owner=self.wrapped, idx=i)


class MaxScriptController(MaxController):
    """
    maxscript docs: https://help.autodesk.com/view/MAXDEV/2022/ENU/?guid=GUID-569BE1BC-216E-496F-9EDE-1E8D2DB42194
    """
    def get_ports(self):
        # first 4 variables are builtins: T S F NT
        for i in range(5, self.wrapped.NumVariables()+1):
            variable_type = self.wrapped.GetType(i)

            if variable_type == rt.Name("constant"):
                yield IScriptVariablePort(owner=self.wrapped, idx=i)
            elif variable_type == rt.Name("object"):
                yield IScriptVariablePort(owner=self.wrapped, idx=i)
            elif variable_type == rt.Name("node"):
                yield IScriptVariablePort(owner=self.wrapped, idx=i)
            elif variable_type == rt.Name("target"): #subanim track
                pass 

class MaxListController(MaxController):
    """
    maxscript docs: https://help.autodesk.com/view/MAXDEV/2022/ENU/?guid=GUID-ED23BCBD-2344-4DFB-BA5A-ABAF04951164
    """
    def get_ports(self):
        """list controllers"""
        for i in range(1, self.wrapped.getCount()+1):
            name = self.wrapped.getName(i)
            yield ListItemPort(owner=self.wrapped, subanim_idx=i)

        """list weights"""
        for name in rt.GetPropNames(self.wrapped.weights):
            for i in range(1, self.wrapped.weights.numsubs+1):
                weight_subanim = rt.getSubAnim(self.wrapped.weights, i)
                yield SubanimControllerPort(owner=self.wrapped.weights, subanim_idx=i)

        """yield available port"""
        yield ListAvailablePort(owner=self.wrapped)


class MaxWireController(MaxController):
    """
    maxscript docs: https://help.autodesk.com/view/MAXDEV/2022/ENU/?guid=GUID-4D368C80-2B26-4DE2-8543-DA568879195D
    also:
    https://help.autodesk.com/view/MAXDEV/2022/ENU/?guid=GUID-2F2F1393-AB2C-45B9-B7D0-AB452115EDC9
    """
    def get_ports(self):
        for i in range(1, self.wrapped.numWires+1):
            yield DummyPort(owner=self, name=F"wireParent{i}", sources=self.wrapped.getWireParent(i))
            # yield DummyPort(owner=self, name=F"CoController{i}", sources=self.wrapped.getCoController(i))

        # yield DummyPort(owner=self, name="drivenAnimation", sources=self.wrapped.drivenAnimation)


        # self.wrapped.drivenAnimation
        # numWires -> int
        # isDriver -> bool
        # isDriven -> bool
        # isTwoWay -> bool
        # drivenAnimation ->driven animation controller

        # getCoController i
        # getWireParent i
        # getWireSubnum i
        # return iter([])

def is_wire_controller(native_entity):
    return True if rt.getInterface(native_entity, "wireController") else False

def is_node(native_entity):
    return rt.isValidNode(native_entity)

def is_controller(native_entity):
    return rt.isController(native_entity)

def is_baseobject(native_entity):
    return rt.superclassof(native_entity) in [rt.Shape, rt.GeometryClass, rt.Camera, rt.Light, rt.Helper, rt.SpacewarpObject]

def is_material(native_entity):
    return False

def is_texture(native_entity):
    return False

def is_expression_controller(native_entity):
    return rt.classOf(native_entity) in [rt.Float_Expression, rt.Point3_Expression, rt.Position_Expression, rt.Scale_Expression]

def is_script_controller(native_entity):
    return True if rt.getInterface(native_entity, "IScriptCtrl") else False

def is_list_controller(native_entity):
    return True if rt.getInterface(native_entity, "list") else False

class ChildrenPort:
    def __init__(self, owner:"mxs.Node"):
        self.owner = owner

    def __repr__(self):
        return f"ChildrenPort()"

    @property
    def name(self):
        return "children"
    
    @property
    def multi(self):
        return True

    def get_sources(self)->List["mxs.Node"]:
        children = self.owner.children
        if not children:
            return []
        for child in self.owner.children:
            yield child

    def is_connected(self)->bool:
        return len(self.owner.children)>0

    def connect(self, source):
        try:
            rt.attachObjects(self.owner, source)
        except Exception as err:
            print("cant disconnect baseobject", err)

    def disconnect(self, source):
        try:
            source.parent = None
        except Exception as err:
            print("cant disconnect baseobject", err)

class DummyPort:
    def __init__(self, owner, name, sources=[]):
        self.owner = owner
        self._name = name
        self._sources = sources

    @property
    def name(self):
        return self._name

    @property
    def multi(self):
        return True

    def __repr__(self):
        return f"DummyPort({self.name})"

    def get_sources(self):
        return self._sources

    def is_connected(self)->bool:
        return False

    def connect(self):
        raise NotImplementedError

    def disconnect(self):
        raise NotImplementedError



class SubanimControllerPort:
    def __init__(self, owner:"mxs.Node", subanim_idx):
        self.owner = owner
        self.subanim_idx = subanim_idx

    def __repr__(self):
        return f"SubanimControllerPort({self.name})"

    @property
    def name(self):
        return str(rt.getSubAnim(self.owner, self.subanim_idx).name)
    
    @property
    def multi(self):
        return False

    def get_sources(self)->List["mxs.Node"]:
        controller = rt.getSubAnim(self.owner, self.subanim_idx).controller
        return [controller] if controller else []

    def is_connected(self)->bool:
        return True if rt.getSubAnim(self.owner, self.subanim_idx).controller else False

    def connect(self, source:"mxs.Controller")->None:
        print("connect subanim controller", self, source)
        try:
            subanim = rt.getSubAnim(self.owner, self.subanim_idx)
            subanim.controller = source
        except Exception as err:
            print("cant connect subanim", self, err)

    def disconnect(self, source)->None:
        print("connect subanim controller", self, source)

        try:
            subanim = rt.getSubAnim(self.owner, self.subanim_idx)
            remove_controller_from_subanim(subanim)
            # default_controller = new_default_controller_for_superclass(rt.superclassof(subanim.controller))
            # rt.setProperty(subanim, "controller", default_controller)
        except Exception as err:

            print("cant connect subanim", self, err)


class ListItemPort(SubanimControllerPort):
    pass


class ListAvailablePort:
    """
    maxscript docs: https://help.autodesk.com/view/MAXDEV/2022/ENU/?guid=GUID-ED23BCBD-2344-4DFB-BA5A-ABAF04951164
    """
    def __init__(self, owner):
        self.owner = owner

    def __repr__(self):
        return f"ListAvailablePort()"

    @property
    def name(self):
        return "available"

    def __repr__(self):
        return f"MaterialPort()"

    @property
    def multi(self):
        return False

    def get_sources(self)->List["mxs.Object"]:
        return []

    def is_connected(self)->bool:
        return False

    def connect(self, source:"mxs.Controller")->None:
        print("connect list available controller", self, source)
        try:
            subanim = rt.getSubAnim(self.owner, self.owner.numsubs-1)
            subanim.controller = source
        except Exception as err:
            print("cant connect subanim", self, err)

    def disconnect(self, source)->None:
        raise Exception("ListController's available port should never be disconnected. It's a placeholder to add new items to the list controller.")


class ListWeightPort:
    def __init__(self, owner:"mxs.Node", idx):
        self.owner = owner
        self._idx = idx

    def __repr__(self):
        return f"ListWeightPort({self.name})"

    @property
    def name(self):
        return str(rt.getSubAnim(self.owner.weights, self._idx).name)

    @property
    def multi(self):
        return False

    def get_sources(self):
        controller = rt.getSubAnim(self.owner.weights, self._idx).controller
        return [rt.getSubAnim(self.owner.weights, self._idx)] if controller else []

    def is_connected(self):
        controller = rt.getSubAnim(self.owner.weights, self._idx).controller
        return True if controller else False

    def connect(self, source):
        raise NotImplementedError

    def disconnect(self, source):
        raise NotImplementedError


class PropertyControllerPort:
    def __init__(self, owner:"mxs.Node", prop_name):
        self.owner = owner
        self._prop_name = prop_name

    def __repr__(self):
        return f"PropertyControllerPort({self.name})"

    @property
    def name(self):
        return str(self._prop_name)
    
    @property
    def multi(self):
        return False

    def get_sources(self)->List["mxs.Controller"]:
        controller = rt.getPropertyController(self.owner, self._prop_name)
        return [controller] if controller else []

    def is_connected(self)->bool:
        return True if rt.getPropertyController(self.owner, self._prop_name) else False

    def connect(self, source:"mxs.Controller")->None:
        try:
            rt.setPropertyController(self.owner, self._prop_name, source)
        except Exception as err:
            print("cant connect property", inlet, err)

    def disconnect(self, source)->None:
        print("connect property controller", self, source)
        try:
            subanim = rt.getSubAnim(self.owner, self.subanim_idx)
            remove_controller_from_subanim(subanim)
            # default_controller = new_default_controller_for_superclass(rt.superclassof(subanim.controller))
            # rt.setProperty(subanim, "controller", default_controller)

        except Exception as err:

            print("cant connect subanim", self, err)


def remove_controller_from_subanim(subAnim):
    assert rt.isKindOf(subAnim, rt.SubAnim)
    """
    removing controllers with maxscript:
    https://creativescratchpad.blogspot.com/2019/05/removing-controller-with-maxscript.html
    """
    originalValue = subAnim.value
    REFMSG_CONTROLREF_CHANGE = 0xFA

    if rt.isKindOf(subAnim.parent, rt.ParamBlock2):
        iGlobal = rt.dotNetClass("Autodesk.Max.GlobalInterface").Instance
        pBlockNET = iGlobal.Animatable.GetAnimByHandle(rt.getHandleByAnim(subAnim.parent))
        pValNET = pBlockNET.GetPB2Value(pBlockNET.IndexToId(subAnim.index - 1), 0)

        ANIMATABLE_FLAG = 0x40 
        pValNET.Flags = pValNET.Flags | ANIMATABLE_FLAG # set the flag on the PB2Value which controls if the parameter is animated - this effectively removes the controller
    else:
        ctrl = subAnim.controller
        parent = subAnim.parent
        for i in range(1, refs.getNumRefs(parent)):
            if refs.getReference(parent, i):
                refs.replaceReference(parent, i, None)
                break


    if rt.classOf(subAnim.value) == rt.classOf(originalValue):
        subAnim.value = originalValue
    rt.notifyDependents(subAnim.parent, msg=REFMSG_CONTROLREF_CHANGE)

def new_default_controller_for_superclass(superclass):
        if superclass == rt.Matrix3Controller:
            return rt.NewDefultMatrix3Controller()
        elif superclass == rt.PositionController:
            return rt.NewDefultPositionController()
        elif superclass == rt.RotationController:
            return rt.NewDefultRotationController()
        elif superclass == rt.ScaleController:
            return rt.NewDefultScaleController()
        elif superclass == rt.FloatController:
            return rt.NewDefultFloatController()
        elif superclass == rt.Point2Controller:
            return rt.NewDefultPoint2Controller()
        elif superclass == rt.Point3Controller:
            return rt.NewDefultPoint3Controller()
        elif superclass == rt.Point4Controller:
            return rt.NewDefultPoint4Controller()
        elif superclass == rt.BoolController:
            return rt.NewDefultBoolController()
        elif superclass == rt.ColorController:
            return rt.NewDefultColorController()
        elif superclass == rt.ColorController:
            return rt.NewDefultColorController()
        elif superclass == rt.FRGBAController:
            return rt.NewDefultFRGBAController()
        elif superclass == PointControllerContainer:
            return rt.NewDefaultPointControllerContainer()
        else:
            raise Exception("no default controller for", superclass)


class BaseObjectPort:
    def __init__(self, owner:"mxs.Node"):
        self.owner = owner

    def __repr__(self):
        return f"BaseObjectPort()"

    @property
    def name(self):
        return "baseobject"
    
    @property
    def multi(self):
        return False

    def get_sources(self)->List["mxs.Object"]:
        yield self.owner.baseobject

    def is_connected(self)->bool:
        return True if self.owner.baseobject else False

    def connect(self, source:"mxs.Object")->None:

        try:
            self.owner.baseobject = source
        except Exception as err:
            print("cant connect baseobject", err)

    def disconnect(self, source)->None:
        print("disconnect", self, source)


class MaterialPort:
    def __init__(self, owner:"mxs.Node"):
        self.owner = owner

    def __repr__(self):
        return f"MaterialPort()"

    @property
    def name(self):
        return "material"
    
    @property
    def multi(self):
        return False

    def get_sources(self)->List["mxs.Object"]:
        material = self.owner.material
        return [material] if material else []

    def is_connected(self)->bool:
        return True if self.owner.material else False

    def connect(self, source:"mxs.Object")->None:
        try:
            self.owner.material = source
        except Exception as err:
            print("cant connect baseobject", err)

    def disconnect(self, source)->None:
        print("disconnect", self, source)


class IExprScalarTargetPort:
    """
    https://help.autodesk.com/view/MAXDEV/2024/ENU/?guid=GUID-FC68369C-232D-4040-B223-F67978A4A5A1
    """
    def __init__(self, owner:"mxs.Controller", idx):
        self.owner = owner
        self._idx = idx

    @property
    def name(self):
        return str(self.owner.GetScalarName(self._idx))

    def get_sources(self)->List["mxs.Controller"]:
        if self.owner.GetScalarType(self._idx)==rt.Name("scalarTarget"):
            controller = self.owner.GetScalarTarget(self._idx).controller
            return [controller] if controller else []
        else:
            return []

    @property
    def multi(self):
        return False

    def is_connected(self)->bool:
        return True if self.owner.GetScalarTarget(self._idx).controller else False

    def connect(self, source:"mxs.Controller")->None:
        pass

    def disconnect(self, source)->None:
        pass


class IExprVectorTargetPort:
    """
    https://help.autodesk.com/view/MAXDEV/2024/ENU/?guid=GUID-FC68369C-232D-4040-B223-F67978A4A5A1
    """
    def __init__(self, owner:"mxs.Controller", idx):
        self.owner = owner
        self._idx = idx

    @property
    def name(self):
        return str(self.owner.GetVectorName(self._idx))

    def is_connected(self)->bool:
        return True if self.owner.GetVectorTarget(self._idx).controller else False

    def get_sources(self)->List["mxs.Controller"]:
        if self.owner.GetVectorType(self._idx)==rt.Name("vectorTarget"):
            controller = self.owner.GetVectorTarget(self._idx).controller
            return [controller] if controller else []
        else:
            return []

    @property
    def multi(self):
        return False



    def connect(self, source:"mxs.Controller")->None:
        pass

    def disconnect(self, source)->None:
        pass


class IScriptVariablePort:
    """
    https://help.autodesk.com/view/MAXDEV/2024/ENU/?guid=GUID-FC68369C-232D-4040-B223-F67978A4A5A1
    """
    def __init__(self, owner:"mxs.Controller", idx):
        self.owner = owner
        self._idx = idx

    @property
    def name(self):
        return str(self.owner.GetName(self._idx))

    @property
    def multi(self):
        return False

    def __repr__(self):
        return f"{self.__class__.__name__}('{self.name}')"

    def get_sources(self)->List["mxs.Controller"]:
        variable_type = self.owner.GetType(self._idx)

        if variable_type == rt.Name("constant"):
            return []
        elif variable_type == rt.Name("object"):
            return [self.owner.getObject(self._idx)]
        elif variable_type == rt.Name("node"):
            return [self.owner.getNode(self._idx)]
        elif variable_type == rt.Name("target"):
            return []


    def is_connected(self)->bool:
        return len(self.get_sources())>0

    def connect(self, source:"mxs.Controller")->None:
        if is_node(source):
            self.owner.setNode(source)
        else:
            self.owner.setObject(source)

    def disconnect(self, source)->None:
        pass


# Node Graph Widgets
class SceneNode(BaseNode):
    __identifier__ = 'nodes.max'
    NODE_NAME = 'scene node'

    def __init__(self):
        super(SceneNode, self).__init__()

def all_equal(values):
    return len(set(values))==1

def get_same_value(values, default=None):
    if all_equal(values):
        return values[0]
    else:
        return default

class EntityInspector(QWidget):
    def __init__(self, parent=None):
        super(EntityInspector, self).__init__(parent)

        self.setLayout(QVBoxLayout())

    def clear(self):
        for i in reversed(range(self.layout().count())): 
            child = self.layout().itemAt(i).widget()
            child.setParent(None)


            
    def set_entities(self, native_entities):
        self.clear()
        self.title = QLabel()
        self.layout().addWidget(self.title)

        if len(native_entities) == 0:
            self.title.setText( "<nothing selected>")
        elif len(native_entities) == 1:
            native_entity = native_entities[0]
            entity = MaxBaseEntity.create(native_entity)

            if isinstance(entity, MaxIExprController):
                """expression editor widget"""
                expression_editor = QPlainTextEdit(self)
                expression_editor.setPlainText(native_entity.GetExpression())
                self.layout().addWidget(expression_editor)
                evaluate_btn = QPushButton("Evaluate")
                self.layout().addWidget(evaluate_btn)
                
                @evaluate_btn.clicked.connect
                def update_expression(value):
                    try:
                        native_entity.SetExpression(expression_editor.toPlainText())
                        rt.redrawViews()
                    except RuntimeError as err:
                        # expression_editor.setPlainText(native_entity.GetExpression())
                        print(err)

        else:
            entities = [MaxBaseEntity.create(native_entity) for native_entity in native_entities]
            AllSameClass = all_equal(type(entity) for entity in entities)

            self.title.setText(entities[0].name()+"..." if AllSameClass else "<multiple different types>")
            if AllSameClass:
                entities = [MaxBaseEntity.create(native_entity) for native_entity in native_entities]
                if isinstance(entities[0], MaxIExprController):
                    """expression editor widget"""
                    expression_editor = QPlainTextEdit(self)
                    expression_editor.setPlainText(get_same_value([e.GetExpression() for e in native_entities], "<multiple values>"))
                    self.layout().addWidget(expression_editor)
                    evaluate_btn = QPushButton("Evaluate")
                    self.layout().addWidget(evaluate_btn)
                    
                    @evaluate_btn.clicked.connect
                    def update_expression(value):
                        for native_entity in native_entities:
                            try:
                                native_entity.SetExpression(expression_editor.toPlainText())
                                rt.redrawViews()
                            except RuntimeError as err:
                                # expression_editor.setPlainText(native_entity.GetExpression())
                                print(err)


from collections import Counter

def suffix_duplicates(names):
    counter = Counter()
    result = []

    # append index suffix
    for name in names:
        counter[name] += 1
        result.append(f"{name}({counter[name]})")

    # remove suffix if occures only once
    for i, name in enumerate(names):
        if counter[name]<2:
            result[i] = name
    return result               

class SceneGraphDocker(QDockWidget):
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
        # self.update_graph()

        self.graph.port_connected.connect(self.on_port_connected)
        self.graph.port_disconnected.connect(self.on_port_disconnected)
        self.graph.node_selection_changed.connect(self.on_node_selection_changed)

        # create main window widget to hold the toolbar and the graph
        main_window = QMainWindow()
        main_window.setCentralWidget( self.graph.widget)

        inspector_docker = QDockWidget()
        self.inspector = EntityInspector()
        inspector_docker.setWidget(self.inspector)
        main_window.addDockWidget(QtCore.Qt.LeftDockWidgetArea ,inspector_docker)

        # create the toolbar
        toolBar = main_window.addToolBar("hello")
        add_selected_action = toolBar.addAction("add selected")
        add_selected_action.triggered.connect(self.add_selected_entity)

        add_inputs_action = toolBar.addAction("add inputs")
        add_inputs_action.triggered.connect(self.add_selected_node_inputs)

        remove_action = toolBar.addAction("remove")
        remove_action.triggered.connect(self.remove_selected_nodes)

        remove_action = toolBar.addAction("layout all")
        remove_action.triggered.connect(self.layout_all_nodes)

        remove_action = toolBar.addAction("layout selected")
        remove_action.triggered.connect(self.layout_selected_nodes)


        self.setWidget(main_window)

        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum);
        self.setMinimumSize(512,510)

    def selection(self):
        entities = [node.data for node in scenegraph.graph.selected_nodes()]
        if len(entities)==0:
            return None
        elif len(entities)==1:
            return entities[0]
        else:
            return entities

    @Slot()
    def layout_all_nodes(self):
        self.graph.auto_layout_nodes()

    @Slot()
    def layout_selected_nodes(self):
        self.graph.auto_layout_nodes(self.graph.selected_nodes())

    @Slot()
    def add_selected_entity(self):
        selected_entities = rt.selection
        for entity in selected_entities:
            if rt.GetHandleByAnim(entity) in self.node_from_anim_handle:
                pass
            else:
                node = self.add_entity_to_graph(entity)
    @Slot()
    def add_selected_node_inputs(self):
        selected_nodes = self.graph.selected_nodes()
        handles_in_graph = self.node_from_anim_handle.keys()
        
        # collect entities not in graph
        new_entities = []
        for node in selected_nodes:
            entity = node.data
            for max_port in MaxBaseEntity.create(entity).get_ports():
                for source_entity in max_port.get_sources():
                    if rt.GetHandleByAnim(source_entity) not in handles_in_graph:
                        new_entities.append(source_entity)

                    
        # add nodes to graph
        for entity in new_entities:
            node = self.add_entity_to_graph(entity)

    @Slot()
    def remove_selected_nodes(self):
        for node in self.graph.selected_nodes():
            self.remove_entity_from_graph(node.data)
            
    def fitInView(self, nodes=[]):
        viewer = self.graph.widget.widget(0)
        scene = self.graph.scene()

        viewer.fitInView( scene.sceneRect() )

    def showEvent(self, event):
        self.register_callbacks()

    def closeEvent(self, event):
        self.unregister_callbacks()

    """Node graph events"""
    def on_port_connected(self, inlet, outlet):
        print("ui port connected")
        try:
            port = inlet.data
            source_entity = outlet.node().data
            target_entity = inlet.node().data
            port.connect(source_entity, target_entity)
        except Exception as err:
            print("cant connect port", err)

    def on_port_disconnected(self, inlet, outlet):
        print("ui port disconnected")
        try:
            port = inlet.data
            source_entity = outlet.node().data
            target_entity = inlet.node().data
            port.disconnect(source_entity, target_entity)
        except Exception as err:
            print("cant connect port", err)

    def on_node_selection_changed(self, selected, unselected):
        self.inspector.set_entities([node.data for node in self.graph.selected_nodes()])

    def register_callbacks(self):
        # delete old callbacks
        self.unregister_callbacks()

        """
        node related notifictions
        https://help.autodesk.com/view/MAXDEV/2022/ENU/?guid=GUID-F0CD0BD9-FC77-4881-8021-102B5837F7B2
        """
        rt.callbacks.addScript(rt.Name('postNodeSelectOperation'), self.node_selected_callback, id=rt.Name('MyCallbacks'))
        # rt.callbacks.addScript(rt.Name('nodeCreated'), self.node_created_callback, id=rt.Name('MyCallbacks'))
        rt.callbacks.addScript(rt.Name('nodePostDelete'), self.node_deleted_callback, id=rt.Name('MyCallbacks'))
        
        rt.callbacks.addScript(rt.Name('nodeLinked'), self.node_linked_callback, id=rt.Name('MyCallbacks'))
        rt.callbacks.addScript(rt.Name('nodeUnlinked'), self.node_unlinked_callback, id=rt.Name('MyCallbacks'))

    def unregister_callbacks(self):
        rt.callbacks.removeScripts(id=rt.name('MyCallbacks'))

    # Max Callbacks
    def node_created_callback(self):
        notification = rt.callbacks.notificationParam()
        # print("node created callback", notification)

    def node_deleted_callback(self):
        notification = rt.callbacks.notificationParam()
        # print("node delete callback", notification)

        for node in self.graph.all_nodes():
            native_entity = node.data
            if rt.isDeleted(native_entity):
                self.remove_entity_from_graph(native_entity)
                continue

            if not rt.isValidObj(native_entity):
                self.remove_entity_from_graph(native_entity)
                continue

            if len(rt.refs.dependentNodes(native_entity))==0 and not rt.isValidNode(native_entity):
                self.remove_entity_from_graph(native_entity)
                continue

    def node_selected_callback(self):
        notification = rt.callbacks.notificationParam()
        # print("node selected callback", notification)
        # self.update_graph()

    def node_linked_callback(self):
        notification = rt.callbacks.notificationParam()
        # print("node linked callback", notification)
        # self.update_graph()

    def node_unlinked_callback(self):
        notification = rt.callbacks.notificationParam()
        # print("node unlinked callback", notification)
        # self.update_graph()

    def add_entity_to_graph(self, native_entity):
        if rt.GetHandleByAnim(native_entity) in self.node_from_anim_handle.keys():
            return
        # create the node from max object
        node = BaseNode() #self.graph.create_node('nodes.max.SceneNode', native_entity.name, selected=False, push_undo=False)
        node.data = native_entity
        self.node_from_anim_handle[rt.GetHandleByAnim(native_entity)] = node

        # create input ports
        ports = [port for port in MaxBaseEntity.create(native_entity).get_ports()]
        port_names_with_indices = suffix_duplicates([port.name for port in ports])
        for max_port, suffixed_port_name in zip(ports, port_names_with_indices):
            input_port = node.add_input(suffixed_port_name, multi_input=max_port.multi)
            input_port.data=max_port
            self.port_from_handle_name[(rt.GetHandleByAnim(native_entity), suffixed_port_name)] = input_port

        # create output ports
        output_port = node.add_output('self')

        # add graph to node
        self.graph.add_node(node)


        """customize node"""
        max_entity = MaxBaseEntity.create(native_entity)
        node.set_name(max_entity.name())
        node.set_color(*max_entity.color())

        # connect node to graph
        for node in self.graph.all_nodes():
            native_entity = node.data
            ports = [port for port in MaxBaseEntity.create(native_entity).get_ports()]
            # add indices to duplicate named ports
            port_names_with_indices = suffix_duplicates([port.name for port in ports])
            for max_port, port_name in zip(ports, port_names_with_indices):
                sources = list(max_port.get_sources())
                for source in sources:
                    input_port = node.get_input(port_name)
                    source_node = self.node_from_anim_handle.get(rt.GetHandleByAnim(source), None)
                    
                    if source_node is None or source_node.get_output(0) in input_port.connected_ports():
                        pass
                    else:
                        source_node.get_output(0).connect_to(input_port, emit_signal=False)

        # return
        return node

    def remove_entity_from_graph(self, native_entity):
        node = self.node_from_anim_handle[rt.GetHandleByAnim(native_entity)]
        del self.node_from_anim_handle[rt.GetHandleByAnim(native_entity)]
        """remove connections silently"""
        for port in node.input_ports()+node.output_ports():
            port.clear_connections(push_undo=False, emit_signal=False)
        self.graph.remove_node(node)

def opengraph():
    global scenegraph
    max_window = GetQMaxMainWindow()
    scenegraph = max_window.findChild(QDockWidget, "TheSceneGraph")
    if scenegraph:
        scenegraph.deleteLater()

    scenegraph = SceneGraphDocker(max_window)
    scenegraph.setObjectName("TheSceneGraph")
    max_window.addDockWidget(QtCore.Qt.LeftDockWidgetArea, scenegraph)
    scenegraph.move(100,0)
    scenegraph.setFloating(False)
    scenegraph.show()



"""
TEST NODES PORTS existance, connecting and disconnecting
"""
import unittest
from pymxs import runtime as rt
class TestNodePorts(unittest.TestCase):
    def test_duplicated_ports(self):
        pass

    def test_children_port(self):
        # setup max scene
        teapot = rt.Teapot()

        # test ports
        node_ports = [port.name for port  in MaxBaseEntity.create(teapot).get_ports()]
        self.assertIn('children', node_ports)

    def test_children_source(self):
        # setup max scene
        teapot = rt.Teapot()
        cylinder = rt.Cylinder()
        cylinder.parent = teapot

        # test ports
        children = [child for child in ChildrenPort(owner=teapot).get_sources()]
        self.assertIn(cylinder, children)

    def test_parenting(self):
        # setup max scene
        teapot = rt.Teapot()
        cylinder = rt.Cylinder()

        # test ports
        children_port = ChildrenPort(owner=teapot)
        children_port.connect(cylinder)
        self.assertIn(cylinder, teapot.children)

    def test_unparenting(self):
        # setup max scene
        teapot = rt.Teapot()
        cylinder = rt.Cylinder()
        cylinder.parent = teapot

        # test ports
        children_port = ChildrenPort(owner=teapot)
        children_port.disconnect(cylinder)
        self.assertNotIn(cylinder, teapot.children)

    def test_baseobject_port(self):
        # setup max scene
        teapot = rt.Teapot()

        # test ports
        node_ports = [port.name for port  in MaxBaseEntity.create(teapot).get_ports()]
        self.assertIn('baseobject', node_ports)

    def test_baseobject_source(self):
        # setup max scene
        teapot = rt.Teapot()

        # test ports
        sources = [source for source in BaseObjectPort(owner=teapot).get_sources()]
        self.assertIn(teapot.baseobject, sources)

    def test_baseobject_connect(self):
        # setup max scene
        teapot = rt.Teapot()
        cylinder = rt.Cylinder()

        # test ports
        port = BaseObjectPort(owner=teapot)
        port.connect(cylinder.baseobject)
        self.assertEqual(cylinder.baseobject, teapot.baseobject)

    def test_baseobject_discconnect(self):
        pass

    def test_transform_port(self):
        # setup max scene
        teapot = rt.Teapot()

        # test ports
        node_ports = [port.name for port  in MaxBaseEntity.create(teapot).get_ports()]
        self.assertIn('Transform', node_ports)

    def test_connecting_transform(self):
        pass

    def test_disconnecting_transform(self):
        pass

    def test_material_port(self):
        pass

    def test_connecting_material(self):
        pass

    def test_disconnecting_material(self):
        pass


class TestFloatExpression(unittest.TestCase):
    def test_duplicated_ports(self):
        pass

    def test_scalar_and_vector_constants(self):
        expression_controller = rt.Float_Expression()
        expression_controller.AddScalarConstant("my_scalar_constant", 0.0)
        expression_controller.AddVectorConstant("my_vector_constant", rt.Point3(0,0,0))

        teapot = rt.Teapot()
        teapot[2][0][0].controller = expression_controller

        self.assertIn("my_scalar_constant", [port.name for port in MaxBaseEntity.create(expression_controller).get_ports()])
        self.assertIn("my_vector_constant", [port.name for port in MaxBaseEntity.create(expression_controller).get_ports()])

    def test_scalar_and_vector_targets(self):
        teapot = rt.Teapot()
        sphere = rt.Sphere()

        transform_subanim = rt.getSubanim(teapot, 3)
        position_subanim = rt.getSubanim(transform_subanim, 1)
        x_subanim = rt.getSubanim(position_subanim, 1)

        expression_controller = rt.Float_Expression()
        x_subanim.controller = expression_controller

        expression_controller.AddScalarTarget("sphere_z_pos", sphere[2][0][2].controller)
        expression_controller.SetExpression("sphere_z_pos")

        expression_entity = MaxBaseEntity.create(x_subanim.controller)
        self.assertIn("sphere_z_pos", [port.name for port in expression_entity.get_ports()])

    def test_connecting(self):
        pass

    def test_disconnecting(self):
        pass


class TestScriptController(unittest.TestCase):
    def test_duplicated_ports(self):
        pass

    def test_ports(self):
        # create control objects
        dummy1 = rt.Point()
        dummy2 = rt.Dummy()

        script_controller = rt.position_script()
        script_controller.addConstant("myconstant", 0.0)
        # script_controller.addTarget
        script_controller.addObject("myobject", dummy1[2][0][0].controller)
        script_controller.addNode("mynode", dummy2)

        script_controller.setExpression("[myconstant, myobject.value, mynode.pos.z]")



        teapot = rt.Teapot()
        teapot[2][0].controller = script_controller

    def test_connecting(self):
        pass

    def test_disconnecting(self):
        pass


class TestListController(unittest.TestCase):
    def test_suplicate_suffix(self):
        position_list = rt.position_list()
        

        teapot = rt.Teapot()
        teapot[2][0].controller = position_list
        available_subanim = rt.getSubAnim(position_list, position_list.numsubs-1)
        available_subanim.controller = rt.position_xyz()
        available_subanim.controller = rt.position_xyz()

        # assert is_list_controller(position_list)
        port_names = [port.name for port in MaxBaseEntity.create(position_list).get_ports()]

        self.assertNotEqual(len(port_names), len(set(port_names)))
        suffixed = suffix_duplicates(port_names)
        self.assertEqual(len(port_names), len(set(suffixed)))

    def test_ports(self):
        position_list = rt.position_list()
        

        teapot = rt.Teapot()
        teapot[2][0].controller = position_list
        available_subanim = rt.getSubAnim(position_list, position_list.numsubs-1)
        available_subanim.controller = rt.position_xyz()
        available_subanim.controller = rt.position_xyz()

        # assert is_list_controller(position_list)
        port_names = [port.name for port in MaxBaseEntity.create(position_list).get_ports()]
        
        self.assertEqual(port_names, ['Position XYZ', 'Position XYZ', 'Weight: Position XYZ', 'Weight: Position XYZ', "available"])


class TestWireController(unittest.TestCase):
    def test_wire_ports(self):
        teapot = rt.Teapot()
        box = rt.Box()


class TestReactController(unittest.TestCase):
    pass

"""
TEST BEHAVIOUR
"""
class TestControllerInstancing(unittest.TestCase):
    def test_positionXYZController(self):
        # setup max scene
        teapot = rt.Teapot()

        transform_controller = rt.getSubanim(teapot, 3)
        position_controller = rt.getSubanim(transform_controller, 1)
        x_controller = rt.getSubanim(position_controller, 1)
        y_controller = rt.getSubanim(position_controller, 2)
        z_controller = rt.getSubanim(position_controller, 3)

        # test connectiing
        ports = list( MaxBaseEntity.create(position_controller).get_ports() )
        ports[0].connect(z_controller)
        ports[1].connect(z_controller)
        ports[2].connect(z_controller)
        self.assertEqual(rt.getSubanim(position_controller, 1), rt.getSubanim(position_controller, 2))
        self.assertEqual(rt.getSubanim(position_controller, 1), rt.getSubanim(position_controller, 3))



if __name__ == "__main__":
    """reset max file """
    # rt.resetMaxFile(rt.Name("noPrompt"))

    """individual testcases"""
    # unittest.main(TestChildrenPort())
    # unittest.main(TestBaseObjectPort())
    # unittest.main(TestControllerInstancing())
    # unittest.main(TestFloatExpression())
    # unittest.main(TestScriptController())
    # unittest.main(TestListController())

    unittest.main(TestWireController())

    """run all tests"""
    # unittest.main()

    """open graph docker"""
    # opengraph()

    
