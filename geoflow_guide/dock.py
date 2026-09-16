from qgis.PyQt.QtCore import Qt, pyqtSignal
from qgis.PyQt.QtWidgets import (
    QComboBox,
    QDockWidget,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class GeoFlowDock(QDockWidget):
    refresh_requested = pyqtSignal()
    run_requested = pyqtSignal(str)
    remove_result_requested = pyqtSignal(str)
    load_sample_requested = pyqtSignal(str)
    help_requested = pyqtSignal()
    self_check_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__("GeoFlow Guide", parent)
        self.setAllowedAreas(
            Qt.DockWidgetArea.LeftDockWidgetArea
            | Qt.DockWidgetArea.RightDockWidgetArea
        )
        root = QWidget(self)
        layout = QVBoxLayout(root)

        title = QLabel("What would you like to do?")
        title.setStyleSheet("font-size:16px;font-weight:700;padding:6px 0")
        layout.addWidget(title)

        self.layer_label = QLabel("Active layer: none")
        self.layer_label.setStyleSheet("font-weight:700")
        self.layer_summary = QLabel(
            "Open or select a layer. GeoFlow will suggest suitable tasks."
        )
        self.layer_summary.setWordWrap(True)
        layout.addWidget(self.layer_label)
        layout.addWidget(self.layer_summary)

        top_buttons = QHBoxLayout()
        refresh = QPushButton("Refresh Layer")
        refresh.clicked.connect(self.refresh_requested)
        self.sample_type = QComboBox()
        self.sample_type.addItem("Point sample", "point")
        self.sample_type.addItem("Line sample", "line")
        self.sample_type.addItem("Polygon sample", "polygon")
        sample = QPushButton("Load Sample")
        sample.clicked.connect(
            lambda: self.load_sample_requested.emit(self.sample_type.currentData())
        )
        top_buttons.addWidget(refresh)
        top_buttons.addWidget(self.sample_type)
        top_buttons.addWidget(sample)
        layout.addLayout(top_buttons)

        layout.addWidget(QLabel("Recommended task"))
        self.tasks = QComboBox()
        self.tasks.currentIndexChanged.connect(self._show_description)
        layout.addWidget(self.tasks)

        self.description = QLabel("Select a layer to begin.")
        self.description.setWordWrap(True)
        self.description.setStyleSheet(
            "background:#f4f6f8;border:1px solid #d9dee5;padding:8px"
        )
        layout.addWidget(self.description)

        self.run_button = QPushButton("Run Task")
        self.run_button.setEnabled(False)
        self.run_button.clicked.connect(
            lambda: self.run_requested.emit(self.tasks.currentData() or "")
        )
        layout.addWidget(self.run_button)

        layout.addWidget(QLabel("Generated results"))
        self.results = QListWidget()
        self.results.setMaximumHeight(90)
        layout.addWidget(self.results)

        self.remove_button = QPushButton("Remove Selected Result")
        self.remove_button.setEnabled(False)
        self.remove_button.clicked.connect(
            lambda: self.remove_result_requested.emit(
                self.results.currentItem().data(Qt.ItemDataRole.UserRole)
                if self.results.currentItem()
                else ""
            )
        )
        layout.addWidget(self.remove_button)

        utility_buttons = QHBoxLayout()
        help_button = QPushButton("Help")
        help_button.clicked.connect(self.help_requested)
        check_button = QPushButton("Self-check")
        check_button.clicked.connect(self.self_check_requested)
        utility_buttons.addWidget(help_button)
        utility_buttons.addWidget(check_button)
        layout.addLayout(utility_buttons)

        layout.addWidget(QLabel("Activity"))
        self.log_box = QPlainTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setMaximumBlockCount(250)
        layout.addWidget(self.log_box, 1)
        self.setWidget(root)

    def set_layer(self, name, summary, tasks):
        self.layer_label.setText("Active layer: %s" % name)
        self.layer_summary.setText(summary)
        self.tasks.clear()
        for task in tasks:
            self.tasks.addItem(task["label"], task["id"])
            index = self.tasks.count() - 1
            self.tasks.setItemData(
                index, task["description"], Qt.ItemDataRole.ToolTipRole
            )
        self.run_button.setEnabled(bool(tasks))
        self._show_description()

    def clear_layer(self):
        self.layer_label.setText("Active layer: none")
        self.layer_summary.setText(
            "Open or select a layer. GeoFlow will suggest suitable tasks."
        )
        self.tasks.clear()
        self.description.setText("Select a layer to begin.")
        self.run_button.setEnabled(False)

    def _show_description(self):
        index = self.tasks.currentIndex()
        text = (
            self.tasks.itemData(index, Qt.ItemDataRole.ToolTipRole)
            if index >= 0
            else None
        )
        self.description.setText(text or "Select a task.")

    def add_result(self, layer_id, name):
        self.results.addItem(name)
        item = self.results.item(self.results.count() - 1)
        item.setData(Qt.ItemDataRole.UserRole, layer_id)
        self.results.setCurrentItem(item)
        self.remove_button.setEnabled(True)

    def remove_result(self, layer_id):
        for row in range(self.results.count()):
            if (
                self.results.item(row).data(Qt.ItemDataRole.UserRole)
                == layer_id
            ):
                self.results.takeItem(row)
                break
        self.remove_button.setEnabled(self.results.count() > 0)

    def log(self, text):
        self.log_box.appendPlainText(text)
