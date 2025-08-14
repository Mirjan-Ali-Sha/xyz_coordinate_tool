# -*- coding: utf-8 -*-

import os
import math
from PyQt5.QtCore import QSettings, QTranslator, QCoreApplication, Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QAction, QToolBar
from qgis.core import QgsProject, QgsApplication
from qgis.gui import QgsMapToolPan

from .xyz_coordinate_dialog import XYZCoordinateDialog
from .xyz_map_tool import XYZMapTool


class XYZCoordinateTool:
    """QGIS Plugin Implementation for XYZ/MGRS Coordinate Tool."""

    def __init__(self, iface):
        """Constructor."""
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        
        # Initialize plugin directory
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'XYZCoordinateTool_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&MAS Raster Processing')  # Common menu name
        self.toolbar = None
        
        # Initialize plugin components
        self.dock_widget = None
        self.map_tool = None
        self.action_XYZCoordinate = None
        self.is_active = False
        self.previous_map_tool = None

    def tr(self, message):
        """Get the translation for a string using Qt translation API."""
        return QCoreApplication.translate('XYZCoordinateTool', message)

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""
        
        icon_path = os.path.join(self.plugin_dir, 'icon.png')
        
        # Check if the toolbar already exists, if not create it
        self.toolbar = self.iface.mainWindow().findChild(QToolBar, 'MASRasterProcessingToolbar')
        if self.toolbar is None:
            self.toolbar = self.iface.addToolBar(u'MAS Raster Processing')
            self.toolbar.setObjectName('MASRasterProcessingToolbar')
        
        # Create the XYZ Coordinate Tool action
        self.action_XYZCoordinate = QAction(
            QIcon(icon_path), 
            u"XYZ Coordinate Tool", 
            self.iface.mainWindow()
        )
        
        # Set detailed tooltips and status tips
        self.action_XYZCoordinate.setToolTip(
            "XYZ/MGRS Coordinate Tool - Capture tile coordinates and MGRS references from map clicks"
        )
        self.action_XYZCoordinate.setStatusTip(
            "Click to activate coordinate capture tool for XYZ tiles and MGRS grid references"
        )
        self.action_XYZCoordinate.setWhatsThis(
            "This tool allows you to click on the map to capture XYZ tile coordinates "
            "and MGRS grid references. For XYZ tiles, you can navigate to coordinates "
            "and plot tile polygons. Switch between coordinate systems using the dock widget."
        )
        
        # Make it checkable for toggle behavior
        self.action_XYZCoordinate.setCheckable(True)
        
        # Connect the action to the toggle method
        self.action_XYZCoordinate.triggered.connect(self.toggle_tool)
        
        # Add to raster menu under MAS Raster Processing
        self.iface.addPluginToRasterMenu(self.menu, self.action_XYZCoordinate)
        
        # Add to toolbar
        self.toolbar.addAction(self.action_XYZCoordinate)
        
        # Add to actions list for cleanup
        self.actions.append(self.action_XYZCoordinate)
        
        # Create dock widget
        self.dock_widget = XYZCoordinateDialog(self.iface)
        self.dock_widget.setWindowTitle("XYZ/MGRS Coordinate Tool")
        self.iface.addDockWidget(Qt.LeftDockWidgetArea, self.dock_widget)
        self.dock_widget.hide()  # Initially hidden
        
        # Create map tool and pass dock widget reference
        self.map_tool = XYZMapTool(self.iface.mapCanvas(), self.dock_widget)
        
        # Connect signals - coordinate clicked AND XYZ button signals
        self.map_tool.coordinates_clicked.connect(self.on_coordinates_clicked)
        self.dock_widget.go_to_clicked.connect(self.go_to_coordinates)
        self.dock_widget.plot_polygon_clicked.connect(self.plot_polygon)
        
        # Connect to dock widget close event to update tool state
        self.dock_widget.visibilityChanged.connect(self.on_dock_visibility_changed)
        
        # Connect to map tool changes to update button state
        self.iface.mapCanvas().mapToolSet.connect(self.on_map_tool_set)

    def add_action(self, icon_path, text, callback, enabled_flag=True, 
                  add_to_menu=True, add_to_toolbar=True, status_tip=None, 
                  whats_this=None, parent=None):
        """Add a toolbar icon to the toolbar - helper method for consistency."""
        
        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)
        action.setCheckable(True)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar and self.toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToRasterMenu(self.menu, action)

        self.actions.append(action)
        return action

    def on_map_tool_set(self, new_tool):
        """Handle when a different map tool is activated."""
        # Check if the new tool is not our tool
        if new_tool != self.map_tool and self.is_active:
            # Update our button state to unchecked but keep dock widget open
            self.is_active = False
            self.action_XYZCoordinate.setChecked(False)
            print("XYZ/MGRS tool button unchecked (other tool selected)")

    def toggle_tool(self):
        """Toggle the XYZ coordinate tool on/off with improved behavior."""
        current_tool = self.iface.mapCanvas().mapTool()
        
        if not self.is_active or current_tool != self.map_tool:
            # Activate tool (either not active or different tool is active)
            self.activate_tool()
        else:
            # Deactivate tool - but keep dock widget open if user wants it
            self.deactivate_tool_only()

    def activate_tool(self):
        """Activate the XYZ coordinate tool."""
        self.is_active = True
        self.action_XYZCoordinate.setChecked(True)
        
        # Store current map tool to restore later
        self.previous_map_tool = self.iface.mapCanvas().mapTool()
        
        # Set custom map tool
        self.iface.mapCanvas().setMapTool(self.map_tool)
        
        # Show dock widget if it's not visible
        if not self.dock_widget.isVisible():
            self.dock_widget.show()
            self.dock_widget.raise_()
        
        # Update status bar
        self.iface.mainWindow().statusBar().showMessage(
            "XYZ/MGRS Coordinate Tool activated - Click on map to capture coordinates", 5000
        )
        
        print("XYZ/MGRS tool activated")

    def deactivate_tool_only(self):
        """Deactivate the tool but keep dock widget open."""
        self.is_active = False
        self.action_XYZCoordinate.setChecked(False)
        
        # Restore previous map tool or set to pan
        if self.previous_map_tool and self.previous_map_tool != self.map_tool:
            self.iface.mapCanvas().setMapTool(self.previous_map_tool)
        else:
            pan_tool = QgsMapToolPan(self.iface.mapCanvas())
            self.iface.mapCanvas().setMapTool(pan_tool)
        
        # Update status bar
        self.iface.mainWindow().statusBar().showMessage(
            "XYZ/MGRS Coordinate Tool deactivated", 3000
        )
        
        print("XYZ/MGRS tool deactivated (dock widget remains open)")

    def deactivate_tool_and_close_dock(self):
        """Deactivate tool and close dock widget (for cleanup only)."""
        self.is_active = False
        self.action_XYZCoordinate.setChecked(False)
        
        # Restore previous map tool or set to pan
        if self.previous_map_tool:
            self.iface.mapCanvas().setMapTool(self.previous_map_tool)
        else:
            pan_tool = QgsMapToolPan(self.iface.mapCanvas())
            self.iface.mapCanvas().setMapTool(pan_tool)
        
        # Hide dock widget
        if self.dock_widget:
            self.dock_widget.hide()
        
        print("XYZ/MGRS tool fully deactivated")

    def on_dock_visibility_changed(self, visible):
        """Handle dock widget visibility changes."""
        if not visible and self.is_active:
            # If dock is manually closed while tool is active, deactivate the tool
            self.deactivate_tool_only()

    def on_coordinates_clicked(self, system, param1, param2, param3):
        """Handle coordinates clicked from map tool."""
        if system == "XYZ":
            self.dock_widget.set_coordinates(param1, param2, param3)
            self.iface.mainWindow().statusBar().showMessage(
                f"XYZ coordinates captured: {param1}, {param2}, {param3}", 3000
            )
            print(f"XYZ coordinates captured: {param1}, {param2}, {param3}")
        elif system == "MGRS":
            self.dock_widget.set_coordinates(param1)
            self.iface.mainWindow().statusBar().showMessage(
                f"MGRS coordinates captured: {param1}", 3000
            )
            print(f"MGRS coordinates captured: {param1}")

    def go_to_coordinates(self, system, param1, param2, param3):
        """Navigate to coordinates - only for XYZ system."""
        if system == "XYZ":
            self.go_to_xyz_coordinates(param1, param2, param3)

    def plot_polygon(self, system, param1, param2, param3):
        """Plot polygon - only for XYZ system."""
        if system == "XYZ":
            self.plot_xyz_polygon(param1, param2, param3)

    def go_to_xyz_coordinates(self, x, y, z):
        """Navigate to XYZ coordinates."""
        from .xyz_map_tool import tile2deg
        from qgis.core import QgsRectangle, QgsCoordinateReferenceSystem, QgsCoordinateTransform
        
        try:
            # Convert tile coordinates to lat/lon
            lat, lon = tile2deg(x, y, z)
            
            # Create extent for the tile
            lat_next, lon_next = tile2deg(x + 1, y + 1, z)
            
            # Create rectangle in WGS84
            extent_wgs84 = QgsRectangle(min(lon, lon_next), min(lat, lat_next), 
                                       max(lon, lon_next), max(lat, lat_next))
            
            # Transform to map CRS if needed
            map_crs = self.iface.mapCanvas().mapSettings().destinationCrs()
            wgs84_crs = QgsCoordinateReferenceSystem("EPSG:4326")
            
            if map_crs != wgs84_crs:
                transform = QgsCoordinateTransform(wgs84_crs, map_crs, QgsProject.instance())
                extent_map = transform.transformBoundingBox(extent_wgs84)
            else:
                extent_map = extent_wgs84
            
            # Set map extent
            self.iface.mapCanvas().setExtent(extent_map)
            self.iface.mapCanvas().refresh()
            
            # Show success message
            self.iface.messageBar().pushMessage(
                "Navigation", 
                f"Navigated to XYZ tile: {x}, {y}, {z}", 
                level=1, duration=3
            )
            print(f"Navigated to XYZ tile: {x}, {y}, {z}")
            
        except Exception as e:
            self.iface.messageBar().pushMessage(
                "Error", 
                f"Failed to navigate to XYZ coordinates: {str(e)}", 
                level=3, duration=5
            )

    def plot_xyz_polygon(self, x, y, z):
        """Plot a polygon representing the XYZ tile area."""
        from .xyz_map_tool import tile2deg
        from qgis.core import (QgsVectorLayer, QgsFeature, QgsGeometry, 
                              QgsPointXY, QgsProject, QgsSingleSymbolRenderer, QgsFillSymbol)
        
        try:
            # Convert tile coordinates to corner points
            corners = [
                tile2deg(x, y, z),           # Top-left
                tile2deg(x + 1, y, z),       # Top-right  
                tile2deg(x + 1, y + 1, z),   # Bottom-right
                tile2deg(x, y + 1, z)        # Bottom-left
            ]
            
            # Create points
            points = [QgsPointXY(lon, lat) for lat, lon in corners]
            points.append(points[0])  # Close the polygon
            
            # Create memory layer
            layer_name = f"XYZ_Tile_{x}_{y}_{z}"
            
            # Remove any existing layer with the same name
            existing_layers = [layer for layer in QgsProject.instance().mapLayers().values() 
                              if layer.name() == layer_name]
            for layer in existing_layers:
                QgsProject.instance().removeMapLayer(layer)
            
            layer = QgsVectorLayer(
                f"Polygon?crs=EPSG:4326&field=x:integer&field=y:integer&field=z:integer&field=tile_id:string", 
                layer_name, "memory"
            )
            
            if not layer.isValid():
                raise Exception("Failed to create memory layer")
            
            provider = layer.dataProvider()
            
            # Create feature
            feature = QgsFeature()
            feature.setGeometry(QgsGeometry.fromPolygonXY([points]))
            feature.setAttributes([x, y, z, f"{x}_{y}_{z}"])
            
            provider.addFeatures([feature])
            layer.updateExtents()
            
            # Set symbol
            symbol = QgsFillSymbol.createSimple({
                'color': '255,0,0,50',  # Red with transparency
                'outline_color': 'red',
                'outline_width': '2',
                'outline_style': 'solid'
            })
            
            renderer = QgsSingleSymbolRenderer(symbol)
            layer.setRenderer(renderer)
            
            # Add layer to project
            QgsProject.instance().addMapLayer(layer)
            
            # Show success message
            self.iface.messageBar().pushMessage(
                "Success", 
                f"XYZ tile polygon plotted: {x}, {y}, {z}", 
                level=1, duration=3
            )
            print(f"XYZ tile polygon plotted: {x}, {y}, {z}")
            
        except Exception as e:
            self.iface.messageBar().pushMessage(
                "Error", 
                f"Failed to plot XYZ polygon: {str(e)}", 
                level=3, duration=5
            )

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        
        # Deactivate tool if active
        if self.is_active:
            self.deactivate_tool_and_close_dock()
        
        # Disconnect from map tool changes signal
        try:
            self.iface.mapCanvas().mapToolSet.disconnect(self.on_map_tool_set)
        except:
            pass  # Ignore if already disconnected
            
        # Remove dock widget
        if self.dock_widget:
            self.iface.removeDockWidget(self.dock_widget)
            self.dock_widget.deleteLater()
            self.dock_widget = None
        
        # Remove actions from raster menu and toolbar
        for action in self.actions:
            self.iface.removePluginRasterMenu(self.tr(u'&MAS Raster Processing'), action)
            self.iface.removeToolBarIcon(action)
        
        # Note: We don't delete the toolbar as it might be shared with other MAS plugins
        # The toolbar will be cleaned up when the last MAS plugin is unloaded
