# maxscript
from pymxs import runtime as rt

# Qt
from qtmax import GetQMaxMainWindow
from qtmax import GetQMaxMainWindow
from PySide2.QtWidgets import *
from PySide2.QtCore import *

class TransformPanel(QDockWidget):
	def __init__(self, parent=None):
		super(TransformPanel, self).__init__(parent)
		self.setWindowFlags(QtCore.Qt.Tool)
		self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
		self.widget = QWidget()
		self.widget.setLayout(QVBoxLayout())
		self.setWidget(self.widget)

		self.initUI()

	def set_x_rotation(self, value):
		# print("set_x_rotation", value)
		for obj in rt.selection:
			rotation_controller = obj[2][1][0].controller
			rotation_controller.value = value
		

	def set_y_rotation(self, value):
		# print("set_y_rotation", self, args)
		for obj in rt.selection:
			rotation_controller = obj[2][1][1].controller
			rotation_controller.value = value

	def set_z_rotation(self, value):
		# print("set_z_rotation", self, args)
		for obj in rt.selection:
			rotation_controller = obj[2][1][2].controller
			rotation_controller.value = value

	def initUI(self):
		# Position
		

		# Rotation
		axis_order = QComboBox()
		axis_order.addItems(["XYZ", "XZY", "YZX", "YXZ", "ZXY", "ZYX", "XYX", "YZY", "ZXZ"])
		self.widget.layout().addWidget(axis_order)

		x_spinner = QSlider(orientation=Qt.Horizontal)
		y_spinner = QSlider(orientation=Qt.Horizontal)
		z_spinner = QSlider(orientation=Qt.Horizontal)
		self.widget.layout().addWidget(x_spinner)
		self.widget.layout().addWidget(y_spinner)
		self.widget.layout().addWidget(z_spinner)

		x_spinner.valueChanged.connect(self.set_x_rotation)
		y_spinner.valueChanged.connect(self.set_y_rotation)
		z_spinner.valueChanged.connect(self.set_z_rotation)
	

	def showEvent(self, event):
		self.register_callbacks()

	def closeEvent(self, event):
		self.unregister_callbacks()

	def register_callbacks(self):
		# delete old callbacks
		self.unregister_callbacks()

		rt.callbacks.addScript(rt.Name('postNodeSelectOperation'), self.node_selected_callback, id=rt.Name('TransformPanel-SelectionCallbacks'))

	def unregister_callbacks(self):
		rt.callbacks.removeScripts(id=rt.name('TransformPanel-SelectionCallbacks'))

	def node_selected_callback(self):
		notification = rt.callbacks.notificationParam()
		print("node selected", notification)

		# collect parameters for all selected objects

		# update ui
		selection = rt.selection



if __name__ == "__main__":
	max_window = GetQMaxMainWindow()
	w = max_window.findChild(QDockWidget, "TransformPanel")
	if w:
		w.deleteLater()

	w = TransformPanel(max_window)

	w.setObjectName("TransformPanel")
	w.setFloating(True)
	w.show()