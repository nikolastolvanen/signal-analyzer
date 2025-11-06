from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QCheckBox, QMenuBar, QMenu
)
from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT as NavigationToolbar
)
from matplotlib.figure import Figure
from qtpy.QtCore import Qt
from superqt import QRangeSlider


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Signal analyzer")
        self.resize(1000, 600)

        self.menu_bar = QMenuBar(self)
        self.setMenuBar(self.menu_bar)

        self.file_menu = QMenu("File", self)
        self.menu_bar.addMenu(self.file_menu)

        self.open_action = self.file_menu.addAction("Open file")
        self.convert_action = self.file_menu.addAction("Convert a file to .bin format")
        self.exit_action = self.file_menu.addAction("Exit")

        main_layout = QHBoxLayout()
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        left_panel = QVBoxLayout()
        main_layout.addLayout(left_panel, 1)

        self.file_label = QLabel("Selected file: None")
        left_panel.addWidget(self.file_label)

        self.file_size_label = QLabel("File size: --")
        left_panel.addWidget(self.file_size_label)

        self.data_points_label = QLabel("Data points: --")
        left_panel.addWidget(self.data_points_label)

        self.signal_time_label = QLabel("Signal duration: --")
        left_panel.addWidget(self.signal_time_label)

        self.plot_button = QPushButton("Plot")
        left_panel.addWidget(self.plot_button)

        self.peaks_checkbox = QCheckBox("Show peaks")
        self.peaks_checkbox.setChecked(False)
        left_panel.addWidget(self.peaks_checkbox)

        self.baseline_checkbox = QCheckBox("Show baseline")
        self.baseline_checkbox.setChecked(False)
        left_panel.addWidget(self.baseline_checkbox)

        left_panel.addStretch()

        right_panel = QVBoxLayout()
        main_layout.addLayout(right_panel, 4)

        self.figure = Figure(figsize=(8, 6))
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)
        right_panel.addWidget(self.toolbar)
        right_panel.addWidget(self.canvas)

        self.range_slider = QRangeSlider(Qt.Horizontal)
        self.range_slider.setRange(0, 100)
        self.range_slider.setValue((0, 100))
        right_panel.addWidget(self.range_slider)

        self.slider_label = QLabel("Range: 0% – 100%")
        right_panel.addWidget(self.slider_label)

        self.range_button = QPushButton("Reset range")
        self.range_button.setFixedSize(100, 30)
        right_panel.addWidget(self.range_button)
