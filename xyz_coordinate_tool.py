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
        """Navigate to coordinates - for all systems."""
        if system == "XYZ":
            self.go_to_xyz_coordinates(param1, param2, param3)
        elif system == "MGRS":
            self.go_to_mgrs_coordinates(param1)
        elif system == "WKT":
            self.go_to_wkt_coordinates(param1)
        elif system == "WKB":
            self.go_to_wkb_coordinates(param1)
        elif system == "GeoJSON":
            self.go_to_geojson_coordinates(param1)

    def plot_polygon(self, system, param1, param2, param3):
        """Plot polygon - for all systems."""
        if system == "XYZ":
            self.plot_xyz_polygon(param1, param2, param3)
        elif system == "MGRS":
            self.plot_mgrs_polygon(param1)
        elif system == "WKT":
            self.plot_wkt_geometry(param1)
        elif system == "WKB":
            self.plot_wkb_geometry(param1)
        elif system == "GeoJSON":
            self.plot_geojson_geometry(param1)


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

    def go_to_mgrs_coordinates(self, mgrs_ref):
        """Navigate to MGRS tile coordinates (Sentinel-2 compatible)."""
        from .xyz_map_tool import get_mgrs_grid_bounds_enhanced
        from qgis.core import QgsRectangle, QgsCoordinateReferenceSystem, QgsCoordinateTransform
        
        try:
            # Get bounds of the MGRS tile
            bounds = get_mgrs_grid_bounds_enhanced(mgrs_ref)
            if bounds is None:
                self.iface.messageBar().pushMessage(
                    "Error", 
                    f"Failed to calculate bounds for MGRS tile: {mgrs_ref}", 
                    level=3, 
                    duration=5
                )
                return
            
            min_lat, min_lon, max_lat, max_lon = bounds
            
            # Create extent in WGS84
            extent_wgs84 = QgsRectangle(min_lon, min_lat, max_lon, max_lat)
            
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
                f"Navigated to MGRS tile: {mgrs_ref} (Sentinel-2 compatible)", 
                level=1, 
                duration=3
            )
            print(f"Navigated to MGRS tile: {mgrs_ref}")
            
        except Exception as e:
            self.iface.messageBar().pushMessage(
                "Error", 
                f"Failed to navigate to MGRS coordinates: {str(e)}", 
                level=3, 
                duration=5
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

    def plot_mgrs_polygon(self, mgrs_ref):
        """Plot a polygon representing the MGRS 100km tile area (Sentinel-2 compatible)."""
        from .xyz_map_tool import get_mgrs_grid_bounds_enhanced
        from qgis.core import (QgsVectorLayer, QgsFeature, QgsGeometry, 
                            QgsPointXY, QgsProject, QgsSingleSymbolRenderer, 
                            QgsFillSymbol)
        
        try:
            # Get bounds of the MGRS tile
            bounds = get_mgrs_grid_bounds_enhanced(mgrs_ref)
            if bounds is None:
                self.iface.messageBar().pushMessage(
                    "Error", 
                    f"Failed to calculate bounds for MGRS tile: {mgrs_ref}", 
                    level=3, 
                    duration=5
                )
                return
            
            min_lat, min_lon, max_lat, max_lon = bounds
            
            # Create corner points (in WGS84)
            corners = [
                (min_lat, min_lon),  # Bottom-left
                (max_lat, min_lon),  # Top-left
                (max_lat, max_lon),  # Top-right
                (min_lat, max_lon),  # Bottom-right
            ]
            
            # Create points
            points = [QgsPointXY(lon, lat) for lat, lon in corners]
            points.append(points[0])  # Close the polygon
            
            # Create memory layer
            layer_name = f"MGRS_Tile_{mgrs_ref}"
            
            # Remove any existing layer with the same name
            existing_layers = [layer for layer in QgsProject.instance().mapLayers().values() 
                            if layer.name() == layer_name]
            for layer in existing_layers:
                QgsProject.instance().removeMapLayer(layer)
            
            # Create new layer with MGRS-specific fields
            layer = QgsVectorLayer(
                f"Polygon?crs=EPSG:4326&field=mgrs:string&field=zone:integer&field=band:string&field=square:string&field=type:string",
                layer_name,
                "memory"
            )
            
            if not layer.isValid():
                raise Exception("Failed to create memory layer")
            
            provider = layer.dataProvider()
            
            # Create feature with MGRS tile info
            feature = QgsFeature()
            feature.setGeometry(QgsGeometry.fromPolygonXY([points]))
            
            # Parse MGRS reference
            zone = int(mgrs_ref[:2])
            band = mgrs_ref[2]
            square = mgrs_ref[3:5] if len(mgrs_ref) >= 5 else ""
            
            feature.setAttributes([mgrs_ref, zone, band, square, "Sentinel-2 Compatible"])
            provider.addFeatures([feature])
            layer.updateExtents()
            
            # Set blue symbol for MGRS (different from red XYZ)
            symbol = QgsFillSymbol.createSimple({
                'color': '0,0,255,50',  # Blue with transparency
                'outline_color': 'blue',
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
                f"MGRS tile polygon plotted: {mgrs_ref} (~100×100 km Sentinel-2 tile)", 
                level=1, 
                duration=3
            )
            print(f"MGRS tile polygon plotted: {mgrs_ref}")
            
        except Exception as e:
            self.iface.messageBar().pushMessage(
                "Error", 
                f"Failed to plot MGRS polygon: {str(e)}", 
                level=3, 
                duration=5
            )

    def go_to_wkt_coordinates(self, wkt_str):
        """Navigate to WKT geometry extent."""
        from qgis.core import QgsGeometry, QgsCoordinateReferenceSystem, QgsCoordinateTransform
        
        try:
            # Parse WKT geometry
            geometry = QgsGeometry.fromWkt(wkt_str)
            
            if geometry.isNull() or geometry.isEmpty():
                self.iface.messageBar().pushMessage(
                    "Error", 
                    "Invalid WKT geometry", 
                    level=3, 
                    duration=5
                )
                return
            
            # Get bounding box
            bbox = geometry.boundingBox()
            
            # Transform to map CRS if needed
            map_crs = self.iface.mapCanvas().mapSettings().destinationCrs()
            wgs84_crs = QgsCoordinateReferenceSystem("EPSG:4326")
            
            if map_crs != wgs84_crs:
                transform = QgsCoordinateTransform(wgs84_crs, map_crs, QgsProject.instance())
                bbox = transform.transformBoundingBox(bbox)
            
            # Set map extent with buffer
            bbox.scale(1.1)  # Add 10% buffer
            self.iface.mapCanvas().setExtent(bbox)
            self.iface.mapCanvas().refresh()
            
            self.iface.messageBar().pushMessage(
                "Navigation", 
                f"Navigated to WKT geometry extent", 
                level=1, 
                duration=3
            )
            
        except Exception as e:
            self.iface.messageBar().pushMessage(
                "Error", 
                f"Failed to navigate to WKT coordinates: {str(e)}", 
                level=3, 
                duration=5
            )

    def go_to_wkb_coordinates(self, wkb_hex):
        """Navigate to WKB geometry extent."""
        from qgis.core import QgsGeometry, QgsCoordinateReferenceSystem, QgsCoordinateTransform
        
        try:
            # Convert hex string to bytes
            wkb_bytes = bytes.fromhex(wkb_hex)
            
            # Parse WKB geometry
            geometry = QgsGeometry()
            geometry.fromWkb(wkb_bytes)
            
            if geometry.isNull() or geometry.isEmpty():
                self.iface.messageBar().pushMessage(
                    "Error", 
                    "Invalid WKB geometry", 
                    level=3, 
                    duration=5
                )
                return
            
            # Get bounding box
            bbox = geometry.boundingBox()
            
            # Transform to map CRS if needed
            map_crs = self.iface.mapCanvas().mapSettings().destinationCrs()
            wgs84_crs = QgsCoordinateReferenceSystem("EPSG:4326")
            
            if map_crs != wgs84_crs:
                transform = QgsCoordinateTransform(wgs84_crs, map_crs, QgsProject.instance())
                bbox = transform.transformBoundingBox(bbox)
            
            # Set map extent with buffer
            bbox.scale(1.1)
            self.iface.mapCanvas().setExtent(bbox)
            self.iface.mapCanvas().refresh()
            
            self.iface.messageBar().pushMessage(
                "Navigation", 
                f"Navigated to WKB geometry extent", 
                level=1, 
                duration=3
            )
            
        except Exception as e:
            self.iface.messageBar().pushMessage(
                "Error", 
                f"Failed to navigate to WKB coordinates: {str(e)}", 
                level=3, 
                duration=5
            )

    def go_to_geojson_coordinates(self, geojson_str):
        """Navigate to GeoJSON geometry extent."""
        from qgis.core import QgsGeometry, QgsCoordinateReferenceSystem, QgsCoordinateTransform
        import json
        
        try:
            # Parse GeoJSON
            geojson_dict = json.loads(geojson_str)
            
            # Convert to QgsGeometry
            geometry = QgsGeometry.fromWkt(self._geojson_to_wkt(geojson_dict))
            
            if geometry.isNull() or geometry.isEmpty():
                self.iface.messageBar().pushMessage(
                    "Error", 
                    "Invalid GeoJSON geometry", 
                    level=3, 
                    duration=5
                )
                return
            
            # Get bounding box
            bbox = geometry.boundingBox()
            
            # Transform to map CRS if needed
            map_crs = self.iface.mapCanvas().mapSettings().destinationCrs()
            wgs84_crs = QgsCoordinateReferenceSystem("EPSG:4326")
            
            if map_crs != wgs84_crs:
                transform = QgsCoordinateTransform(wgs84_crs, map_crs, QgsProject.instance())
                bbox = transform.transformBoundingBox(bbox)
            
            # Set map extent with buffer
            bbox.scale(1.1)
            self.iface.mapCanvas().setExtent(bbox)
            self.iface.mapCanvas().refresh()
            
            self.iface.messageBar().pushMessage(
                "Navigation", 
                f"Navigated to GeoJSON geometry extent", 
                level=1, 
                duration=3
            )
            
        except Exception as e:
            self.iface.messageBar().pushMessage(
                "Error", 
                f"Failed to navigate to GeoJSON coordinates: {str(e)}", 
                level=3, 
                duration=5
            )

    def plot_wkt_geometry(self, wkt_str):
        """Plot WKT geometry on map with correct geometry type."""
        from qgis.core import (QgsVectorLayer, QgsFeature, QgsGeometry, 
                            QgsProject, QgsSingleSymbolRenderer, 
                            QgsFillSymbol, QgsLineSymbol, QgsMarkerSymbol, QgsWkbTypes)
        
        try:
            # Parse WKT geometry
            geometry = QgsGeometry.fromWkt(wkt_str)
            
            if geometry.isNull() or geometry.isEmpty():
                self.iface.messageBar().pushMessage(
                    "Error", 
                    "Invalid WKT geometry", 
                    level=3, 
                    duration=5
                )
                return
            
            # Get actual WKT geometry type name
            wkt_type = geometry.wkbType()
            geom_type_name = QgsWkbTypes.displayString(wkt_type)
            
            # Determine layer type for QGIS (Point, LineString, or Polygon)
            if geometry.type() == 0:  # Point
                layer_type = "Point"
            elif geometry.type() == 1:  # Line
                layer_type = "LineString"
            elif geometry.type() == 2:  # Polygon
                layer_type = "Polygon"
            else:
                layer_type = "Geometry"
            
            # Create memory layer with appropriate geometry type
            layer_name = f"WKT_{geom_type_name}"
            
            # Remove existing layer with same name
            existing_layers = [layer for layer in QgsProject.instance().mapLayers().values() 
                            if layer.name() == layer_name]
            for layer in existing_layers:
                QgsProject.instance().removeMapLayer(layer)
            
            # Create new layer
            layer = QgsVectorLayer(
                f"{layer_type}?crs=EPSG:4326&field=wkt:string&field=geom_type:string",
                layer_name,
                "memory"
            )
            
            if not layer.isValid():
                raise Exception("Failed to create memory layer")
            
            provider = layer.dataProvider()
            
            # Create feature
            feature = QgsFeature()
            feature.setGeometry(geometry)
            feature.setAttributes([wkt_str[:200], geom_type_name])
            provider.addFeatures([feature])
            layer.updateExtents()
            
            # Set appropriate symbol based on geometry type
            if geometry.type() == 0:  # Point
                symbol = QgsMarkerSymbol.createSimple({
                    'name': 'circle',
                    'color': '0,255,0',
                    'size': '4',
                    'outline_color': 'darkgreen',
                    'outline_width': '0.5'
                })
            elif geometry.type() == 1:  # Line
                symbol = QgsLineSymbol.createSimple({
                    'color': '0,255,0',
                    'width': '2',
                    'line_style': 'solid'
                })
            elif geometry.type() == 2:  # Polygon
                symbol = QgsFillSymbol.createSimple({
                    'color': '0,255,0,50',
                    'outline_color': 'green',
                    'outline_width': '2',
                    'outline_style': 'solid'
                })
            
            renderer = QgsSingleSymbolRenderer(symbol)
            layer.setRenderer(renderer)
            
            # Add to project
            QgsProject.instance().addMapLayer(layer)
            
            self.iface.messageBar().pushMessage(
                "Success", 
                f"WKT geometry plotted: {geom_type_name}", 
                level=1, 
                duration=3
            )
            
        except Exception as e:
            self.iface.messageBar().pushMessage(
                "Error", 
                f"Failed to plot WKT geometry: {str(e)}", 
                level=3, 
                duration=5
            )

    def plot_wkb_geometry(self, wkb_hex):
        """Plot WKB geometry on map with correct geometry type."""
        from qgis.core import (QgsVectorLayer, QgsFeature, QgsGeometry, 
                            QgsProject, QgsSingleSymbolRenderer, 
                            QgsFillSymbol, QgsLineSymbol, QgsMarkerSymbol, QgsWkbTypes)
        
        try:
            # Convert hex to bytes
            wkb_bytes = bytes.fromhex(wkb_hex)
            
            # Parse WKB geometry
            geometry = QgsGeometry()
            geometry.fromWkb(wkb_bytes)
            
            if geometry.isNull() or geometry.isEmpty():
                self.iface.messageBar().pushMessage(
                    "Error", 
                    "Invalid WKB geometry", 
                    level=3, 
                    duration=5
                )
                return
            
            # Get actual WKB geometry type name
            wkb_type = geometry.wkbType()
            geom_type_name = QgsWkbTypes.displayString(wkb_type)
            
            # Determine layer type for QGIS
            if geometry.type() == 0:  # Point
                layer_type = "Point"
            elif geometry.type() == 1:  # Line
                layer_type = "LineString"
            elif geometry.type() == 2:  # Polygon
                layer_type = "Polygon"
            else:
                layer_type = "Geometry"
            
            # Create memory layer
            layer_name = f"WKB_{geom_type_name}"
            
            # Remove existing layer
            existing_layers = [layer for layer in QgsProject.instance().mapLayers().values() 
                            if layer.name() == layer_name]
            for layer in existing_layers:
                QgsProject.instance().removeMapLayer(layer)
            
            # Create new layer
            layer = QgsVectorLayer(
                f"{layer_type}?crs=EPSG:4326&field=wkb:string&field=geom_type:string",
                layer_name,
                "memory"
            )
            
            if not layer.isValid():
                raise Exception("Failed to create memory layer")
            
            provider = layer.dataProvider()
            
            # Create feature
            feature = QgsFeature()
            feature.setGeometry(geometry)
            feature.setAttributes([wkb_hex[:200], geom_type_name])
            provider.addFeatures([feature])
            layer.updateExtents()
            
            # Set appropriate symbol based on geometry type
            if geometry.type() == 0:  # Point
                symbol = QgsMarkerSymbol.createSimple({
                    'name': 'circle',
                    'color': '255,255,0',
                    'size': '4',
                    'outline_color': 'darkyellow',
                    'outline_width': '0.5'
                })
            elif geometry.type() == 1:  # Line
                symbol = QgsLineSymbol.createSimple({
                    'color': '255,255,0',
                    'width': '2',
                    'line_style': 'solid'
                })
            elif geometry.type() == 2:  # Polygon
                symbol = QgsFillSymbol.createSimple({
                    'color': '255,255,0,50',
                    'outline_color': 'yellow',
                    'outline_width': '2',
                    'outline_style': 'solid'
                })
            
            renderer = QgsSingleSymbolRenderer(symbol)
            layer.setRenderer(renderer)
            
            # Add to project
            QgsProject.instance().addMapLayer(layer)
            
            self.iface.messageBar().pushMessage(
                "Success", 
                f"WKB geometry plotted: {geom_type_name}", 
                level=1, 
                duration=3
            )
            
        except Exception as e:
            self.iface.messageBar().pushMessage(
                "Error", 
                f"Failed to plot WKB geometry: {str(e)}", 
                level=3, 
                duration=5
            )

    def plot_geojson_geometry(self, geojson_str):
        """Plot GeoJSON geometry on map with correct geometry type."""
        from qgis.core import (QgsVectorLayer, QgsFeature, QgsGeometry, 
                            QgsProject, QgsSingleSymbolRenderer, 
                            QgsFillSymbol, QgsLineSymbol, QgsMarkerSymbol, QgsWkbTypes)
        import json
        
        try:
            # Parse GeoJSON
            geojson_dict = json.loads(geojson_str)
            
            # Convert to WKT then QgsGeometry
            geometry = QgsGeometry.fromWkt(self._geojson_to_wkt(geojson_dict))
            
            if geometry.isNull() or geometry.isEmpty():
                self.iface.messageBar().pushMessage(
                    "Error", 
                    "Invalid GeoJSON geometry", 
                    level=3, 
                    duration=5
                )
                return
            
            # Get geometry type name
            wkb_type = geometry.wkbType()
            geom_type_name = QgsWkbTypes.displayString(wkb_type)
            
            # Determine layer type for QGIS
            if geometry.type() == 0:  # Point
                layer_type = "Point"
            elif geometry.type() == 1:  # Line
                layer_type = "LineString"
            elif geometry.type() == 2:  # Polygon
                layer_type = "Polygon"
            else:
                layer_type = "Geometry"
            
            # Create memory layer
            layer_name = f"GeoJSON_{geom_type_name}"
            
            # Remove existing layer
            existing_layers = [layer for layer in QgsProject.instance().mapLayers().values() 
                            if layer.name() == layer_name]
            for layer in existing_layers:
                QgsProject.instance().removeMapLayer(layer)
            
            # Create new layer
            layer = QgsVectorLayer(
                f"{layer_type}?crs=EPSG:4326&field=geojson:string&field=geom_type:string",
                layer_name,
                "memory"
            )
            
            if not layer.isValid():
                raise Exception("Failed to create memory layer")
            
            provider = layer.dataProvider()
            
            # Create feature
            feature = QgsFeature()
            feature.setGeometry(geometry)
            feature.setAttributes([geojson_str[:200], geom_type_name])
            provider.addFeatures([feature])
            layer.updateExtents()
            
            # Set appropriate symbol based on geometry type
            if geometry.type() == 0:  # Point
                symbol = QgsMarkerSymbol.createSimple({
                    'name': 'circle',
                    'color': '255,0,255',
                    'size': '4',
                    'outline_color': 'purple',
                    'outline_width': '0.5'
                })
            elif geometry.type() == 1:  # Line
                symbol = QgsLineSymbol.createSimple({
                    'color': '255,0,255',
                    'width': '2',
                    'line_style': 'solid'
                })
            elif geometry.type() == 2:  # Polygon
                symbol = QgsFillSymbol.createSimple({
                    'color': '255,0,255,50',
                    'outline_color': 'purple',
                    'outline_width': '2',
                    'outline_style': 'solid'
                })
            
            renderer = QgsSingleSymbolRenderer(symbol)
            layer.setRenderer(renderer)
            
            # Add to project
            QgsProject.instance().addMapLayer(layer)
            
            self.iface.messageBar().pushMessage(
                "Success", 
                f"GeoJSON geometry plotted: {geom_type_name}", 
                level=1, 
                duration=3
            )
            
        except Exception as e:
            self.iface.messageBar().pushMessage(
                "Error", 
                f"Failed to plot GeoJSON geometry: {str(e)}", 
                level=3, 
                duration=5
            )

    def _geojson_to_wkt(self, geojson_dict):
        """Convert GeoJSON dictionary to WKT string - handles all geometry types."""
        geom_type = geojson_dict.get('type', '').upper()
        coords = geojson_dict.get('coordinates', [])
        
        if geom_type == 'POINT':
            return f"POINT({coords[0]} {coords[1]})"
        
        elif geom_type == 'MULTIPOINT':
            points_str = ', '.join([f"({c[0]} {c[1]})" for c in coords])
            return f"MULTIPOINT({points_str})"
        
        elif geom_type == 'LINESTRING':
            coords_str = ', '.join([f"{c[0]} {c[1]}" for c in coords])
            return f"LINESTRING({coords_str})"
        
        elif geom_type == 'MULTILINESTRING':
            lines = []
            for line in coords:
                line_str = ', '.join([f"{c[0]} {c[1]}" for c in line])
                lines.append(f"({line_str})")
            return f"MULTILINESTRING({', '.join(lines)})"
        
        elif geom_type == 'POLYGON':
            rings = []
            for ring in coords:
                ring_str = ', '.join([f"{c[0]} {c[1]}" for c in ring])
                rings.append(f"({ring_str})")
            return f"POLYGON({', '.join(rings)})"
        
        elif geom_type == 'MULTIPOLYGON':
            polygons = []
            for polygon in coords:
                rings = []
                for ring in polygon:
                    ring_str = ', '.join([f"{c[0]} {c[1]}" for c in ring])
                    rings.append(f"({ring_str})")
                polygons.append(f"({', '.join(rings)})")
            return f"MULTIPOLYGON({', '.join(polygons)})"
        
        else:
            raise ValueError(f"Unsupported geometry type: {geom_type}")

    def _geojson_to_wkt(self, geojson_dict):
        """Convert GeoJSON dictionary to WKT string."""
        geom_type = geojson_dict.get('type', '').upper()
        coords = geojson_dict.get('coordinates', [])
        
        if geom_type == 'POINT':
            return f"POINT({coords[0]} {coords[1]})"
        elif geom_type == 'LINESTRING':
            coords_str = ', '.join([f"{c[0]} {c[1]}" for c in coords])
            return f"LINESTRING({coords_str})"
        elif geom_type == 'POLYGON':
            rings = []
            for ring in coords:
                ring_str = ', '.join([f"{c[0]} {c[1]}" for c in ring])
                rings.append(f"({ring_str})")
            return f"POLYGON({', '.join(rings)})"
        else:
            raise ValueError(f"Unsupported geometry type: {geom_type}")


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
