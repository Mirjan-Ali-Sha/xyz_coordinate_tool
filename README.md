# XYZ/MGRS Coordinate Tool for QGIS

![QGIS Plugin](https://img.shields.io/badge/QGIS-Plugin-green.svg)
![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![License](https://img.shields.io/badge/license-MIT-orange.svg)
![Python](https://img.shields.io/badge/python-3.x-blue.svg)

A professional multi-format coordinate capture and visualization tool for QGIS that supports **5 different coordinate systems** with full navigation and plotting capabilities.

## 📋 Table of Contents

- [Features](#features)
- [Supported Formats](#supported-formats)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage Guide](#usage-guide)
- [Use Cases](#use-cases)
- [Technical Details](#technical-details)
- [Screenshots](#screenshots)
- [Contributing](#contributing)
- [Support](#support)
- [License](#license)
- [Author](#author)

## ✨ Features

- **🎯 Multi-Format Support**: Work with XYZ tiles, MGRS, WKT, WKB, and GeoJSON
- **🖱️ Interactive Capture**: Click on map to capture XYZ/MGRS coordinates
- **⌨️ Manual Input**: Paste or type WKT/WKB/GeoJSON geometry strings
- **🗺️ Smart Navigation**: "Go To" button navigates to any coordinate system location
- **🎨 Color-Coded Visualization**: Each format has distinct color for easy identification
- **📐 Geometry Detection**: Automatically detects Point, LineString, Polygon, and Multi* types
- **✏️ Editable Inputs**: All coordinate fields are editable for manual entry
- **🔄 CRS Support**: Automatic coordinate reprojection for different CRS
- **💾 Memory Layers**: Creates temporary layers with proper attribute tables
- **🎛️ Dockable Widget**: Professional interface with system dropdown selector

## 🌍 Supported Formats

| Format | Description | Visualization Color | Use Case |
|--------|-------------|-------------------|----------|
| **XYZ Tiles** | Web mapping tile coordinates with zoom levels (0-22) | 🔴 Red | Web map tiles, OpenStreetMap |
| **MGRS** | Military Grid Reference System (Sentinel-2 compatible) | 🔵 Blue | Satellite imagery, Military mapping |
| **WKT** | Well-Known Text geometry format | 🟢 Green | Geometry exchange, Database export |
| **WKB** | Well-Known Binary as hex string | 🟡 Yellow | Binary geometry storage |
| **GeoJSON** | JSON-based geometry format | 🟣 Purple | Web APIs, Modern GIS apps |

## 🚀 Installation

### Method 1: From QGIS Plugin Repository (Recommended)

1. Open QGIS
2. Go to **Plugins** → **Manage and Install Plugins**
3. Search for "XYZ/MGRS Coordinate Tool"
4. Click **Install Plugin**

### Method 2: Manual Installation

1. Download the latest release from [GitHub Releases](https://github.com/Mirjan-Ali-Sha/xyz-coordinate-tool/releases)
2. Extract the ZIP file to your QGIS plugins directory:
   - **Windows**: `C:\Users\<YourUsername>\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins\`
   - **macOS**: `~/Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins/`
   - **Linux**: `~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/`
3. Restart QGIS
4. Enable the plugin from **Plugins** → **Manage and Install Plugins** → **Installed**

## 🎯 Quick Start

### Basic Workflow

1. **Activate the Tool**
   - Click the XYZ Coordinate Tool icon in the toolbar, or
   - Go to **Raster** → **MAS Raster Processing** → **XYZ Coordinate Tool**

2. **Select Coordinate System**
   - Choose from dropdown: XYZ Tiles, MGRS, WKT, WKB, or GeoJSON/JSON

3. **Input Coordinates**
   - **For XYZ/MGRS**: Click on the map to capture coordinates
   - **For WKT/WKB/GeoJSON**: Paste geometry string into the input field

4. **Navigate or Plot**
   - Click **"Go To"** to zoom to the location
   - Click **"Plot Polygon"** to visualize the geometry on the map

## 📖 Usage Guide

### XYZ Tiles Mode

```
Input: X, Y, Z coordinates
Example: X=133235, Y=86284, Z=18
```

- **X**: Tile column number
- **Y**: Tile row number  
- **Z**: Zoom level (0-22, default: 14)
- All values are editable
- Click on map to auto-capture coordinates at current Z level

### MGRS Mode

```
Input: MGRS grid reference
Examples: 45QWF, 33UUU, 44PLV
```

- **Sentinel-2 Compatible**: Works with Sentinel satellite imagery tiles
- **Format**: Zone (2 digits) + Latitude Band (1 letter) + 100km Square ID (2 letters)
- Fixed latitude band calculation with 2,000,000m cycle handling
- Plots 100km × 100km grid squares

### WKT Mode

```
Examples:
POINT(88.5 22.5)
LINESTRING(-0.1228 51.5414, -0.1229 51.5413, -0.1230 51.5414)
POLYGON((0 0, 1 0, 1 1, 0 1, 0 0))
MULTILINESTRING((-0.12 51.54, -0.13 51.55), (-0.14 51.56, -0.15 51.57))
```

- Supports all OGC geometry types
- Automatic detection of Point, Line, Polygon, and Multi* geometries
- Green visualization with appropriate symbology

### WKB Mode

```
Input: Hexadecimal WKB string
Example: 0101000000000000000000F03F0000000000000040
```

- Well-Known Binary format as hex string
- Paste from database exports or geometry tools
- Automatically converted and visualized
- Yellow color for easy identification

### GeoJSON Mode

```
Examples:
{"type":"Point","coordinates":[88.5,22.5]}
{"type":"LineString","coordinates":[[-0.12,51.54],[-0.13,51.55]]}
{"type":"Polygon","coordinates":[[[0,0],[1,0],[1,1],[0,1],[0,0]]]}
```

- Modern JSON-based geometry format
- Supports all geometry types including Multi*
- Compatible with web mapping APIs
- Purple visualization

## 💼 Use Cases

### 🗺️ Web Mapping
- **XYZ Tiles**: Identify and navigate to specific web map tiles
- **Tile Debugging**: Verify tile coverage and zoom levels
- **Cache Management**: Work with tile cache systems

### 🛰️ Satellite Imagery
- **MGRS Integration**: Work with Sentinel-2 satellite imagery
- **Tile Identification**: Find specific 100km MGRS grid squares
- **Data Download**: Identify tiles for bulk satellite data download

### 🔄 Data Exchange
- **WKT/WKB**: Import/export geometries from databases (PostGIS, Oracle Spatial)
- **GeoJSON**: Work with web APIs and modern GIS applications
- **Format Conversion**: Visualize and validate different geometry formats

### 🧪 Testing & QA
- **Coordinate Validation**: Test coordinate transformations
- **Geometry Debugging**: Visualize complex geometries for quality assurance
- **CRS Testing**: Verify coordinate reference system conversions

### 📚 Education
- **Learning Tool**: Understand different coordinate systems
- **Format Comparison**: Compare how different formats represent the same geometry
- **Visualization**: See the difference between coordinate systems visually

## 🔧 Technical Details

### Requirements
- QGIS 3.0 or higher
- Python 3.x
- PyQt5

### Coordinate Systems
- All geometries are created in **EPSG:4326 (WGS84)**
- Automatic reprojection to map canvas CRS
- Supports any QGIS-compatible CRS

### Geometry Types Supported
- Point / MultiPoint
- LineString / MultiLineString  
- Polygon / MultiPolygon
- GeometryCollection (partial support)

### Memory Layers
- Creates temporary layers with proper attribute tables
- Attributes include: original input, geometry type, system identifier
- Color-coded symbology for each format
- Automatic extent buffering (10%) for "Go To" function

### MGRS Implementation
- Fixed latitude band to northing cycle calculation
- Handles 2,000,000m repeating cycles correctly
- Compatible with Sentinel-2 tiling scheme
- Validates results against expected latitude bands

## 📸 Screenshots

### Main Interface
![Main Interface](screenshots/main_interface.png)

### XYZ Tiles Visualization
![XYZ Tiles](screenshots/xyz_tiles.png)

### MGRS Grid (Sentinel-2 Compatible)
![MGRS Grid](screenshots/mgrs_grid.png)

### Multi-Format Support
![Multi-Format](screenshots/multi_format.png)

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Development Setup

```bash
# Clone the repository
git clone https://github.com/Mirjan-Ali-Sha/xyz-coordinate-tool.git

# Create a symbolic link to your QGIS plugins directory
ln -s $(pwd)/xyz_coordinate_tool ~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/

# Restart QGIS and enable the plugin
```

## 📞 Support

### Bug Reports & Feature Requests
- Open an issue on [GitHub Issues](https://github.com/Mirjan-Ali-Sha/xyz-coordinate-tool/issues)
- Provide detailed information including QGIS version, OS, and steps to reproduce

### Contact
- **Email**: mastools.help@gmail.com
- **Issues**: [GitHub Issues](https://github.com/Mirjan-Ali-Sha/xyz-coordinate-tool/issues)

### FAQ

**Q: Why is my MGRS coordinate showing in the wrong location?**  
A: Ensure you're using the 5-character format (e.g., 45QWF). The plugin includes fixed latitude band calculation for accurate positioning.

**Q: Can I use this plugin offline?**  
A: Yes! All coordinate conversions are done locally. Only the base map requires internet.

**Q: What's the difference between WKT and WKB?**  
A: WKT is human-readable text, WKB is binary (shown as hex). Both represent the same geometry.

**Q: How do I get GeoJSON from a web API?**  
A: Most modern mapping APIs return GeoJSON. Just copy the geometry part and paste into the plugin.

## 📄 License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

```
Copyright (C) 2025 Mirjan Ali Sha

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
```

## 👨‍💻 Author

**Mirjan Ali Sha (MAS)**

- Email: mastools.help@gmail.com
- GitHub: [@Mirjan-Ali-Sha](https://github.com/Mirjan-Ali-Sha)

---

## 🌟 Acknowledgments

- Thanks to the QGIS community for excellent documentation
- Inspired by the need for multi-format coordinate tools in GIS workflows
- Special thanks to all contributors and users who provide feedback

---

## ⭐ Star History

If you find this plugin useful, please consider giving it a star on GitHub! ⭐

[![Star History Chart](https://api.star-history.com/svg?repos=Mirjan-Ali-Sha/xyz-coordinate-tool&type=Date)](https://star-history.com/#Mirjan-Ali-Sha/xyz-coordinate-tool&Date)

---

<div align="center">

**Made with ❤️ for the QGIS community**

[Report Bug](https://github.com/Mirjan-Ali-Sha/xyz-coordinate-tool/issues) · [Request Feature](https://github.com/Mirjan-Ali-Sha/xyz-coordinate-tool/issues) · [Documentation](https://github.com/Mirjan-Ali-Sha/xyz-coordinate-tool/wiki)

</div>
