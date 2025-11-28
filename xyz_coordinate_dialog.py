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
        self.system_combo.addItems(["XYZ Tiles", "MGRS", "WKT", "WKB", "GeoJSON/JSON"])
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
        # self.x_input.setReadOnly(True)  # Make read-only since it's captured from clicks
        x_layout.addWidget(self.x_input)
        self.input_layout.addLayout(x_layout)
        
        # Y coordinate input  
        y_layout = QHBoxLayout()
        y_layout.addWidget(QLabel("Y:"))
        self.y_input = QSpinBox()
        self.y_input.setRange(0, 999999999)
        self.y_input.setValue(0)
        # self.y_input.setReadOnly(True)  # Make read-only since it's captured from clicks
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
        # self.mgrs_input.setReadOnly(True)  # Make read-only since it's captured from clicks
        mgrs_layout.addWidget(self.mgrs_input)
        self.input_layout.addLayout(mgrs_layout)

    def setup_wkt_inputs(self):
        """Setup WKT coordinate input field."""
        self.clear_inputs()
        
        # WKT coordinate input
        wkt_layout = QVBoxLayout()
        wkt_layout.addWidget(QLabel("WKT:"))
        self.wkt_input = QLineEdit()
        self.wkt_input.setPlaceholderText("e.g., POINT(88.5 22.5) or POLYGON(...)")
        self.wkt_input.setToolTip("Well-Known Text geometry representation")
        wkt_layout.addWidget(self.wkt_input)
        self.input_layout.addLayout(wkt_layout)

    def setup_wkb_inputs(self):
        """Setup WKB coordinate input field."""
        self.clear_inputs()
        
        # WKB coordinate input
        wkb_layout = QVBoxLayout()
        wkb_layout.addWidget(QLabel("WKB (Hex):"))
        self.wkb_input = QLineEdit()
        self.wkb_input.setPlaceholderText("e.g., 0101000000...")
        self.wkb_input.setToolTip("Well-Known Binary geometry as hex string")
        wkb_layout.addWidget(self.wkb_input)
        self.input_layout.addLayout(wkb_layout)

    def setup_geojson_inputs(self):
        """Setup GeoJSON coordinate input field."""
        self.clear_inputs()
        
        # GeoJSON coordinate input
        geojson_layout = QVBoxLayout()
        geojson_layout.addWidget(QLabel("GeoJSON:"))
        self.geojson_input = QLineEdit()
        self.geojson_input.setPlaceholderText('e.g., {"type":"Point","coordinates":[88.5,22.5]}')
        self.geojson_input.setToolTip("GeoJSON geometry representation")
        geojson_layout.addWidget(self.geojson_input)
        self.input_layout.addLayout(geojson_layout)


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
        
        # Show buttons for ALL systems
        self.button_container.show()
        
        if current_system == "XYZ Tiles":
            self.info_label.setText("Click on the map to capture XYZ coordinates")
            self.go_to_button.setToolTip("Navigate to the XYZ tile location")
            self.plot_polygon_button.setToolTip("Draw polygon representing the XYZ tile area")
        elif current_system == "MGRS":
            self.info_label.setText("Click on the map to capture MGRS coordinates")
            self.go_to_button.setToolTip("Navigate to the MGRS tile location (Sentinel-2 compatible)")
            self.plot_polygon_button.setToolTip("Draw polygon representing the MGRS 100km tile area")
        elif current_system == "WKT":
            self.info_label.setText("Enter or paste WKT geometry")
            self.go_to_button.setToolTip("Navigate to the WKT geometry extent")
            self.plot_polygon_button.setToolTip("Plot the WKT geometry on map")
        elif current_system == "WKB":
            self.info_label.setText("Enter or paste WKB hex string")
            self.go_to_button.setToolTip("Navigate to the WKB geometry extent")
            self.plot_polygon_button.setToolTip("Plot the WKB geometry on map")
        elif current_system == "GeoJSON/JSON":
            self.info_label.setText("Enter or paste GeoJSON geometry")
            self.go_to_button.setToolTip("Navigate to the GeoJSON geometry extent")
            self.plot_polygon_button.setToolTip("Plot the GeoJSON geometry on map")

    def on_system_changed(self, system_name):
        """Handle coordinate system change."""
        if system_name == "XYZ Tiles":
            self.setup_xyz_inputs()
        elif system_name == "MGRS":
            self.setup_mgrs_inputs()
        elif system_name == "WKT":
            self.setup_wkt_inputs()
        elif system_name == "WKB":
            self.setup_wkb_inputs()
        elif system_name == "GeoJSON/JSON":
            self.setup_geojson_inputs()
        
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
        elif current_system == "MGRS" and len(args) >= 1:
            mgrs_ref = args[0]
            if hasattr(self, 'mgrs_input'):
                self.mgrs_input.setText(str(mgrs_ref))
        elif current_system == "WKT" and len(args) >= 1:
            wkt_str = args[0]
            if hasattr(self, 'wkt_input'):
                self.wkt_input.setText(str(wkt_str))
        elif current_system == "WKB" and len(args) >= 1:
            wkb_str = args[0]
            if hasattr(self, 'wkb_input'):
                self.wkb_input.setText(str(wkb_str))
        elif current_system == "GeoJSON/JSON" and len(args) >= 1:
            geojson_str = args[0]
            if hasattr(self, 'geojson_input'):
                self.geojson_input.setText(str(geojson_str))

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
        elif current_system == "WKT":
            if hasattr(self, 'wkt_input'):
                return (self.wkt_input.text().strip(),)
            return ("",)
        elif current_system == "WKB":
            if hasattr(self, 'wkb_input'):
                return (self.wkb_input.text().strip(),)
            return ("",)
        elif current_system == "GeoJSON/JSON":
            if hasattr(self, 'geojson_input'):
                return (self.geojson_input.text().strip(),)
            return ("",)


    def on_go_to_clicked(self):
        """Handle Go To button click - for all systems."""
        current_system = self.get_current_system()
        coords = self.get_coordinates()
        
        if current_system == "XYZ Tiles":
            x, y, z = coords
            self.go_to_clicked.emit("XYZ", x, y, z)
        elif current_system == "MGRS":
            mgrs_ref = coords[0]
            if mgrs_ref:
                self.go_to_clicked.emit("MGRS", mgrs_ref, None, None)
        elif current_system == "WKT":
            wkt_str = coords[0]
            if wkt_str:
                self.go_to_clicked.emit("WKT", wkt_str, None, None)
        elif current_system == "WKB":
            wkb_str = coords[0]
            if wkb_str:
                self.go_to_clicked.emit("WKB", wkb_str, None, None)
        elif current_system == "GeoJSON/JSON":
            geojson_str = coords[0]
            if geojson_str:
                self.go_to_clicked.emit("GeoJSON", geojson_str, None, None)

    def on_plot_polygon_clicked(self):
        """Handle Plot Polygon button click - for all systems."""
        current_system = self.get_current_system()
        coords = self.get_coordinates()
        
        if current_system == "XYZ Tiles":
            x, y, z = coords
            self.plot_polygon_clicked.emit("XYZ", x, y, z)
        elif current_system == "MGRS":
            mgrs_ref = coords[0]
            if mgrs_ref:
                self.plot_polygon_clicked.emit("MGRS", mgrs_ref, None, None)
        elif current_system == "WKT":
            wkt_str = coords[0]
            if wkt_str:
                self.plot_polygon_clicked.emit("WKT", wkt_str, None, None)
        elif current_system == "WKB":
            wkb_str = coords[0]
            if wkb_str:
                self.plot_polygon_clicked.emit("WKB", wkb_str, None, None)
        elif current_system == "GeoJSON/JSON":
            geojson_str = coords[0]
            if geojson_str:
                self.plot_polygon_clicked.emit("GeoJSON", geojson_str, None, None)

    # def on_plot_polygon_clicked(self):
    #     """Handle Plot Polygon button click - for both XYZ and MGRS."""
    #     current_system = self.get_current_system()
        
    #     if current_system == "XYZ Tiles":
    #         coords = self.get_coordinates()
    #         x, y, z = coords
    #         self.plot_polygon_clicked.emit("XYZ", x, y, z)
    #     elif current_system == "MGRS":
    #         coords = self.get_coordinates()
    #         mgrs_ref = coords[0]
    #         if mgrs_ref:
    #             self.plot_polygon_clicked.emit("MGRS", mgrs_ref, None, None)
