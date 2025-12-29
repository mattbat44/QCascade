"""
@brief Animation controls tab component for D-CASCADE results viewer
@author D-CASCADE Team
"""

from qgis.PyQt.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QPushButton, QComboBox, QDoubleSpinBox, QSpinBox,
    QLabel, QSlider
)
from qgis.PyQt.QtCore import Qt


class AnimationTab(QWidget):
    """Animation tab to control map symbology and playback."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        # Variable and color ramp selection
        form = QFormLayout()
        self.dyn_variable_combo = QComboBox()
        self.dyn_variable_combo.addItems([
            'Volume out [m^3]',
            'Volume in [m^3]',
            'Transport capacity [m^3]',
            'Sediment budget [m^3]',
            'D50 active layer [m]',
            'D50 volume out [m]'
        ])
        form.addRow("Variable:", self.dyn_variable_combo)

        self.dyn_color_combo = QComboBox()
        self.dyn_color_combo.addItems([
            'Spectral', 'Viridis', 'Plasma', 'Magma', 'Inferno',
            'Blues', 'Greens', 'Reds', 'BuGn', 'YlOrRd'
        ])
        form.addRow("Color ramp:", self.dyn_color_combo)

        self.dyn_width_spin = QDoubleSpinBox()
        self.dyn_width_spin.setRange(0.1, 10.0)
        self.dyn_width_spin.setSingleStep(0.1)
        self.dyn_width_spin.setValue(1.2)
        form.addRow("Line width:", self.dyn_width_spin)

        layout.addLayout(form)

        # Time slider
        slider_layout = QHBoxLayout()
        slider_layout.addWidget(QLabel("Time Step:"))
        self.time_slider = QSlider(Qt.Horizontal)
        self.time_slider.setMinimum(0)
        self.time_slider.setMaximum(100)
        self.time_slider.setValue(0)
        self.time_slider.setEnabled(False)
        slider_layout.addWidget(self.time_slider, 1)
        self.time_label = QLabel("0 / 0")
        slider_layout.addWidget(self.time_label)
        layout.addLayout(slider_layout)

        # Play button
        play_layout = QHBoxLayout()
        self.play_btn = QPushButton("▶ Play")
        self.play_btn.setEnabled(False)
        play_layout.addWidget(self.play_btn)
        play_layout.addStretch()
        layout.addLayout(play_layout)

        # Animation frame duration
        duration_control_layout = QHBoxLayout()
        duration_control_layout.addWidget(QLabel("Frame Duration (ms):"))
        self.frame_duration_spin = QSpinBox()
        self.frame_duration_spin.setRange(50, 5000)
        self.frame_duration_spin.setValue(200)
        duration_control_layout.addWidget(self.frame_duration_spin)
        layout.addLayout(duration_control_layout)

        layout.addStretch()
