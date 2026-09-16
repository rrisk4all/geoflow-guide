import os

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import QAction, QInputDialog, QMessageBox
from qgis.core import (
    QgsApplication,
    QgsContrastEnhancement,
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsMapLayer,
    QgsProject,
    QgsRasterLayer,
    QgsVectorLayer,
    QgsUnitTypes,
    QgsWkbTypes,
)

from .dock import GeoFlowDock
from .tasks import COMMON_TASKS, LINE_TASKS, POINT_TASKS, POLYGON_TASKS, RASTER_TASKS


class GeoFlowGuidePlugin:
    """Layer-aware guide that delegates analysis to native QGIS capabilities."""

    def __init__(self, iface):
        self.iface = iface
        self.action = None
        self.dock = None
        self.result_layer_ids = []
        self.layer_change_handler = None

    def initGui(self):
        self.action = QAction("GeoFlow Guide", self.iface.mainWindow())
        self.action.triggered.connect(self.show_dock)
        self.iface.addPluginToVectorMenu("GeoFlow Guide", self.action)
        self.iface.addToolBarIcon(self.action)

    def show_dock(self):
        if not self.dock:
            self.dock = GeoFlowDock(self.iface.mainWindow())
            self.dock.refresh_requested.connect(self.refresh)
            self.dock.run_requested.connect(self.run_task)
            self.dock.remove_result_requested.connect(self.remove_result)
            self.dock.load_sample_requested.connect(self.load_sample)
            self.dock.help_requested.connect(self.show_help)
            self.dock.self_check_requested.connect(self.run_self_check)
            self.iface.addDockWidget(
                Qt.DockWidgetArea.RightDockWidgetArea, self.dock
            )
            self.layer_change_handler = lambda _: self.refresh()
            self.iface.currentLayerChanged.connect(self.layer_change_handler)
        self.dock.show()
        self.refresh()

    def active_layer(self):
        return self.iface.activeLayer()

    def refresh(self):
        layer = self.active_layer()
        if not layer:
            self.dock.clear_layer()
            self.dock.log("Open or select a layer to receive recommendations.")
            return
        if layer.type() == QgsMapLayer.VectorLayer:
            geometry = QgsWkbTypes.geometryType(layer.wkbType())
            type_names = {
                QgsWkbTypes.PointGeometry: "point",
                QgsWkbTypes.LineGeometry: "line",
                QgsWkbTypes.PolygonGeometry: "polygon",
            }
            type_name = type_names.get(geometry, "vector")
            specific = {
                QgsWkbTypes.PointGeometry: POINT_TASKS,
                QgsWkbTypes.LineGeometry: LINE_TASKS,
                QgsWkbTypes.PolygonGeometry: POLYGON_TASKS,
            }.get(geometry, [])
            summary = "%d features • %d fields • %s layer • CRS %s" % (
                layer.featureCount(),
                len(layer.fields()),
                type_name,
                layer.crs().authid() or "not set",
            )
            self.dock.set_layer(layer.name(), summary, COMMON_TASKS + specific)
        elif layer.type() == QgsMapLayer.RasterLayer:
            summary = "%d × %d pixels • %d band(s) • CRS %s" % (
                layer.width(),
                layer.height(),
                layer.bandCount(),
                layer.crs().authid() or "not set",
            )
            self.dock.set_layer(layer.name(), summary, RASTER_TASKS)
        else:
            self.dock.set_layer(
                layer.name(),
                "This layer type currently supports map zoom only.",
                [COMMON_TASKS[0]],
            )

    def run_task(self, task_id):
        layer = self.active_layer()
        if not layer:
            self.dock.log("Select a layer first.")
            return
        try:
            if task_id == "zoom":
                self.iface.setActiveLayer(layer)
                self.iface.zoomToActiveLayer()
                self.dock.log("Map zoomed to %s." % layer.name())
            elif task_id == "attributes":
                self.iface.showAttributeTable(layer)
                self.dock.log("Opened the attribute table.")
            elif task_id == "summary":
                self.show_summary(layer)
            elif task_id == "select_all":
                layer.selectAll()
                self.dock.log("Selected %d feature(s)." % layer.selectedFeatureCount())
                self.refresh()
            elif task_id == "clear_selection":
                layer.removeSelection()
                self.dock.log("Selection cleared.")
                self.refresh()
            elif task_id == "stretch":
                self.stretch_raster(layer)
            else:
                self.run_processing_task(layer, task_id)
        except Exception as exc:
            self.dock.log("Task could not run: %s" % exc)
            QMessageBox.warning(
                self.iface.mainWindow(), "GeoFlow Guide", str(exc)
            )

    def run_processing_task(self, layer, task_id):
        import processing

        algorithms = {
            "centroids": ("native:centroids", {"INPUT": layer, "ALL_PARTS": False}),
            "fix_geometries": ("native:fixgeometries", {"INPUT": layer}),
            "extract_vertices": ("native:extractvertices", {"INPUT": layer}),
            "geometry_columns": ("native:exportaddgeometrycolumns", {"INPUT": layer, "CALC_METHOD": 0}),
        }
        if task_id == "buffer":
            distance, ok = QInputDialog.getDouble(
                self.iface.mainWindow(),
                "Buffer distance",
                "Distance:",
                1.0,
                -1000000000.0,
                1000000000.0,
                3,
            )
            if not ok:
                self.dock.log("Buffer cancelled.")
                return
            unit, ok = QInputDialog.getItem(
                self.iface.mainWindow(),
                "Buffer unit",
                "Unit:",
                ["metres", "kilometres"],
                0,
                False,
            )
            if not ok:
                self.dock.log("Buffer cancelled.")
                return
            distance_metres = distance * (1000.0 if unit == "kilometres" else 1.0)
            source_layer = layer
            original_crs = layer.crs()
            reproject_back = False
            if not original_crs.isValid():
                raise ValueError(
                    "The layer has no valid CRS. Assign a CRS before creating an accurate buffer."
                )
            if (
                original_crs.isGeographic()
                or original_crs.mapUnits() != QgsUnitTypes.DistanceMeters
            ):
                metric_crs = self.local_metric_crs(layer)
                source_layer = processing.run(
                    "native:reprojectlayer",
                    {
                        "INPUT": layer,
                        "TARGET_CRS": metric_crs,
                        "OUTPUT": "TEMPORARY_OUTPUT",
                    },
                )["OUTPUT"]
                reproject_back = True
                self.dock.log(
                    "GeoFlow temporarily reprojected the layer to %s for a metre-based buffer."
                    % metric_crs.authid()
                )
            algorithm = "native:buffer"
            parameters = {
                "INPUT": source_layer,
                "DISTANCE": distance_metres,
                "SEGMENTS": 8,
                "END_CAP_STYLE": 0,
                "JOIN_STYLE": 0,
                "MITER_LIMIT": 2,
                "DISSOLVE": False,
            }
        else:
            algorithm, parameters = algorithms[task_id]
        parameters["OUTPUT"] = "TEMPORARY_OUTPUT"
        result = processing.run(algorithm, parameters)
        output = result.get("OUTPUT")
        if task_id == "buffer" and output and reproject_back:
            output = processing.run(
                "native:reprojectlayer",
                {
                    "INPUT": output,
                    "TARGET_CRS": original_crs,
                    "OUTPUT": "TEMPORARY_OUTPUT",
                },
            )["OUTPUT"]
        if output:
            output.setName("GeoFlow — %s" % self.task_label(task_id))
            QgsProject.instance().addMapLayer(output)
            self.result_layer_ids.append(output.id())
            self.dock.add_result(output.id(), output.name())
            self.iface.setActiveLayer(output)
            self.iface.zoomToActiveLayer()
            self.dock.log(
                "Success — created temporary result: %s. Original data was not changed."
                % output.name()
            )

    def local_metric_crs(self, layer):
        """Return the local WGS 84 UTM CRS for the layer extent centre."""
        centre = layer.extent().center()
        wgs84 = QgsCoordinateReferenceSystem("EPSG:4326")
        transform = QgsCoordinateTransform(layer.crs(), wgs84, QgsProject.instance())
        centre_wgs84 = transform.transform(centre)
        longitude = max(-180.0, min(180.0, centre_wgs84.x()))
        latitude = centre_wgs84.y()
        zone = max(1, min(60, int((longitude + 180.0) / 6.0) + 1))
        epsg = (32600 if latitude >= 0 else 32700) + zone
        return QgsCoordinateReferenceSystem("EPSG:%d" % epsg)

    def task_label(self, task_id):
        labels = {
            "buffer": "Buffer",
            "centroids": "Centroids",
            "fix_geometries": "Fixed geometries",
            "extract_vertices": "Vertices",
            "geometry_columns": "Geometry information",
        }
        return labels.get(task_id, "Result")

    def show_summary(self, layer):
        source = layer.source() or "Temporary/in-memory source"
        if layer.type() == QgsMapLayer.VectorLayer:
            details = (
                "Name: %s\nType: Vector\nFeatures: %d\nFields: %d\n"
                "Geometry: %s\nCRS: %s\nSource: %s"
                % (
                    layer.name(),
                    layer.featureCount(),
                    len(layer.fields()),
                    QgsWkbTypes.displayString(layer.wkbType()),
                    layer.crs().authid() or "Not set",
                    source,
                )
            )
        else:
            details = (
                "Name: %s\nType: Raster\nSize: %d × %d\nBands: %d\n"
                "CRS: %s\nSource: %s"
                % (
                    layer.name(),
                    layer.width(),
                    layer.height(),
                    layer.bandCount(),
                    layer.crs().authid() or "Not set",
                    source,
                )
            )
        QMessageBox.information(self.iface.mainWindow(), "Layer explanation", details)
        self.dock.log("Displayed a plain-language layer summary.")

    def stretch_raster(self, layer):
        renderer = layer.renderer()
        provider = layer.dataProvider()
        for band in range(1, layer.bandCount() + 1):
            stats = provider.bandStatistics(band)
            enhancement = QgsContrastEnhancement(provider.dataType(band))
            enhancement.setContrastEnhancementAlgorithm(
                QgsContrastEnhancement.StretchToMinimumMaximum
            )
            enhancement.setMinimumValue(stats.minimumValue)
            enhancement.setMaximumValue(stats.maximumValue)
            if hasattr(renderer, "setContrastEnhancement"):
                renderer.setContrastEnhancement(enhancement)
        layer.triggerRepaint()
        self.dock.log("Applied a min-max contrast stretch.")

    def remove_result(self, layer_id):
        if not layer_id:
            self.dock.log("Select a generated result to remove.")
            return
        if QgsProject.instance().mapLayer(layer_id):
            QgsProject.instance().removeMapLayer(layer_id)
        if layer_id in self.result_layer_ids:
            self.result_layer_ids.remove(layer_id)
        self.dock.remove_result(layer_id)
        self.dock.log("Removed the selected generated result.")

    def load_sample(self, sample_type):
        samples = {
            "point": ("sample_points.geojson", "GeoFlow sample points"),
            "line": ("sample_lines.geojson", "GeoFlow sample lines"),
            "polygon": ("sample_polygons.geojson", "GeoFlow sample polygons"),
        }
        filename, name = samples.get(sample_type, samples["point"])
        path = os.path.join(os.path.dirname(__file__), "test_data", filename)
        layer = QgsVectorLayer(path, name, "ogr")
        if not layer.isValid():
            self.dock.log("The bundled sample could not be loaded.")
            return
        QgsProject.instance().addMapLayer(layer)
        self.iface.setActiveLayer(layer)
        self.iface.zoomToActiveLayer()
        self.dock.log("Loaded the bundled sample layer.")
        self.refresh()

    def show_help(self):
        text = (
            "1. Open a layer or choose a bundled sample.\n"
            "2. GeoFlow detects whether it is a point, line, polygon or raster.\n"
            "3. Choose a recommended task and read its explanation.\n"
            "4. Click Run Task. Processing outputs are temporary.\n"
            "5. Select any generated result in the list to remove it.\n\n"
            "Buffer distances are entered in metres or kilometres. GeoFlow "
            "temporarily uses a local metric CRS when required."
        )
        QMessageBox.information(self.iface.mainWindow(), "GeoFlow Guide — Help", text)
        self.dock.log("Opened built-in help.")

    def run_self_check(self):
        required = [
            "native:buffer",
            "native:reprojectlayer",
            "native:centroids",
            "native:fixgeometries",
            "native:extractvertices",
            "native:exportaddgeometrycolumns",
        ]
        registry = QgsApplication.processingRegistry()
        missing = [item for item in required if not registry.algorithmById(item)]
        sample_dir = os.path.join(os.path.dirname(__file__), "test_data")
        sample_files = [
            "sample_points.geojson",
            "sample_lines.geojson",
            "sample_polygons.geojson",
        ]
        missing_samples = [
            item for item in sample_files if not os.path.isfile(os.path.join(sample_dir, item))
        ]
        if not missing and not missing_samples:
            message = "PASS — QGIS processing tools and bundled samples are available."
            QMessageBox.information(self.iface.mainWindow(), "GeoFlow self-check", message)
        else:
            message = "FAILED — Missing: %s" % ", ".join(missing + missing_samples)
            QMessageBox.warning(self.iface.mainWindow(), "GeoFlow self-check", message)
        self.dock.log(message)

    def unload(self):
        if self.dock:
            try:
                if self.layer_change_handler:
                    self.iface.currentLayerChanged.disconnect(
                        self.layer_change_handler
                    )
            except (TypeError, RuntimeError) as exc:
                self.dock.log(
                    "Could not disconnect the layer-change handler: %s" % exc
                )
            self.iface.removeDockWidget(self.dock)
            self.dock.deleteLater()
        if self.action:
            self.iface.removePluginVectorMenu("GeoFlow Guide", self.action)
            self.iface.removeToolBarIcon(self.action)
