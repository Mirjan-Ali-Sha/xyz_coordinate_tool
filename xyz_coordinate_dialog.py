# -*- coding: utf-8 -*-

from PyQt5.QtCore import QObject, pyqtSignal, Qt
from PyQt5.QtWidgets import (QDockWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QLineEdit, QPushButton, QWidget, QSpinBox, QComboBox)


class XYZCoordinateDialog(QDockWidget):
    """Dock widget for XYZ/MGRS coordinate input and controls."""
    
    # Signals - only for XYZ tiles
    go_to_clicked = pyqtSignal(str, object, object, object)  # system, param1, param2, param3
    plot_polygon_clicked = pyqtSignal(str, object, object, object)  # system, param1, param2, param3
    coordinate_system_changed = pyqtSignal(str)  # system name

    def __init__(self, iface, parent=None):
        super(XYZCoordinateDialog, self).__init__("XYZ/MGRS Coordinate Tool", parent)
        self.iface = iface
        self.setObjectName("XYZCoordinateDialog")
        self.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        
        # Create main widget and layout
        main_widget = QWidget()
        self.setWidget(main_widget)
        
        layout = QVBoxLayout(main_widget)
        
        # Coordinate system dropdown
        system_layout = QHBoxLayout()
        system_layout.addWidget(QLabel("System:"))
        self.system_combo = QComboBox()
        self.system_combo.addItems(["XYZ Tiles", "MGRS"])
        self.system_combo.currentTextChanged.connect(self.on_system_changed)
        system_layout.addWidget(self.system_combo)
        layout.addLayout(system_layout)
        
        # Container for coordinate inputs
        self.input_container = QWidget()
        self.input_layout = QVBoxLayout(self.input_container)
        layout.addWidget(self.input_container)
        
        # Initialize with XYZ system
        self.setup_xyz_inputs()
        
        # Buttons container (for showing/hiding)
        self.button_container = QWidget()
        self.button_layout = QVBoxLayout(self.button_container)
        
        self.go_to_button = QPushButton("Go To")
        self.go_to_button.setToolTip("Navigate to the XYZ tile location")
        self.go_to_button.clicked.connect(self.on_go_to_clicked)
        self.button_layout.addWidget(self.go_to_button)
        
        self.plot_polygon_button = QPushButton("Plot Polygon")
        self.plot_polygon_button.setToolTip("Draw polygon representing the XYZ tile area")
        self.plot_polygon_button.clicked.connect(self.on_plot_polygon_clicked)
        self.button_layout.addWidget(self.plot_polygon_button)
        
        layout.addWidget(self.button_container)
        
        # Info label to explain functionality
        info_layout = QVBoxLayout()
        self.info_label = QLabel("Click on the map to capture coordinates")
        self.info_label.setStyleSheet("color: #666; font-style: italic; margin-top: 10px;")
        self.info_label.setWordWrap(True)
        info_layout.addWidget(self.info_label)
        layout.addLayout(info_layout)
        
        # Add stretch to push everything to top
        layout.addStretch()
        
        # Initially show buttons since XYZ is default
        self.update_button_visibility()

    def setup_xyz_inputs(self):
        """Setup XYZ coordinate input fields."""
        self.clear_inputs()
        
        # X coordinate input
        x_layout = QHBoxLayout()
        x_layout.addWidget(QLabel("X:"))
        self.x_input = QSpinBox()
        self.x_input.setRange(0, 999999999)
        self.x_input.setValue(0)
        self.x_input.setReadOnly(True)  # Make read-only since it's captured from clicks
        x_layout.addWidget(self.x_input)
        self.input_layout.addLayout(x_layout)
        
        # Y coordinate input  
        y_layout = QHBoxLayout()
        y_layout.addWidget(QLabel("Y:"))
        self.y_input = QSpinBox()
        self.y_input.setRange(0, 999999999)
        self.y_input.setValue(0)
        self.y_input.setReadOnly(True)  # Make read-only since it's captured from clicks
        y_layout.addWidget(self.y_input)
        self.input_layout.addLayout(y_layout)
        
        # Z coordinate input (zoom level) - keep editable for user preference
        z_layout = QHBoxLayout()
        z_layout.addWidget(QLabel("Z:"))
        self.z_input = QSpinBox()
        self.z_input.setRange(0, 22)  # Typical zoom range
        self.z_input.setValue(14)  # Default zoom level
        self.z_input.setToolTip("Zoom level for XYZ tiles (editable)")
        z_layout.addWidget(self.z_input)
        self.input_layout.addLayout(z_layout)

    def setup_mgrs_inputs(self):
        """Setup MGRS coordinate input field."""
        self.clear_inputs()
        
        # MGRS coordinate input
        mgrs_layout = QHBoxLayout()
        mgrs_layout.addWidget(QLabel("MGRS:"))
        self.mgrs_input = QLineEdit()
        self.mgrs_input.setPlaceholderText("e.g., 44PLV, 43PES, 44PKC")
        self.mgrs_input.setToolTip("MGRS grid reference captured from map clicks")
        self.mgrs_input.setReadOnly(True)  # Make read-only since it's captured from clicks
        mgrs_layout.addWidget(self.mgrs_input)
        self.input_layout.addLayout(mgrs_layout)

    def clear_inputs(self):
        """Clear all input widgets from the container."""
        while self.input_layout.count():
            child = self.input_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
            elif child.layout():
                self.clear_layout(child.layout())

    def clear_layout(self, layout):
        """Recursively clear a layout."""
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
            elif child.layout():
                self.clear_layout(child.layout())

    def update_button_visibility(self):
        """Update button visibility based on coordinate system."""
        current_system = self.get_current_system()
        
        if current_system == "XYZ Tiles":
            # Show buttons for XYZ
            self.button_container.show()
            self.info_label.setText("Click on the map to capture XYZ coordinates")
        elif current_system == "MGRS":
            # Hide buttons for MGRS
            self.button_container.hide()
            self.info_label.setText("Click on the map to capture MGRS coordinates")

    def on_system_changed(self, system_name):
        """Handle coordinate system change."""
        if system_name == "XYZ Tiles":
            self.setup_xyz_inputs()
        elif system_name == "MGRS":
            self.setup_mgrs_inputs()
        
        # Update button visibility
        self.update_button_visibility()
        
        # Emit signal for other components
        self.coordinate_system_changed.emit(system_name)

    def get_current_system(self):
        """Get the currently selected coordinate system."""
        return self.system_combo.currentText()

    def set_coordinates(self, *args):
        """Set coordinate values based on current system."""
        current_system = self.get_current_system()
        
        if current_system == "XYZ Tiles" and len(args) >= 3:
            x, y, z = args[0], args[1], args[2]
            if hasattr(self, 'x_input'):
                self.x_input.setValue(int(x))
                self.y_input.setValue(int(y))
                # Don't override Z value - let user keep their preference
        elif current_system == "MGRS" and len(args) >= 1:
            mgrs_ref = args[0]
            if hasattr(self, 'mgrs_input'):
                self.mgrs_input.setText(str(mgrs_ref))

    def get_coordinates(self):
        """Get the current coordinate values based on system."""
        current_system = self.get_current_system()
        
        if current_system == "XYZ Tiles":
            if hasattr(self, 'x_input'):
                return (self.x_input.value(), self.y_input.value(), self.z_input.value())
            return (0, 0, 14)
        elif current_system == "MGRS":
            if hasattr(self, 'mgrs_input'):
                return (self.mgrs_input.text().strip(),)
            return ("",)

    def on_go_to_clicked(self):
        """Handle Go To button click - only for XYZ."""
        current_system = self.get_current_system()
        
        if current_system == "XYZ Tiles":
            coords = self.get_coordinates()
            x, y, z = coords
            self.go_to_clicked.emit("XYZ", x, y, z)
        # No action for MGRS since buttons are hidden

    def on_plot_polygon_clicked(self):
        """Handle Plot Polygon button click - only for XYZ."""
        current_system = self.get_current_system()
        
        if current_system == "XYZ Tiles":
            coords = self.get_coordinates()
            x, y, z = coords
            self.plot_polygon_clicked.emit("XYZ", x, y, z)
        # No action for MGRS since buttons are hidden
