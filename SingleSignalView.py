from dataclasses import dataclass

from Controller import Controller
from PySide6.QtGui import QDoubleValidator, QIntValidator
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QPushButton, QVBoxLayout, QWidget
from SingleLineEdit import SingleLineEdit
from SingleSignalModel import SingleSignalModel


@dataclass
class SingleSignalView(QWidget):
    _model: SingleSignalModel
    _controller: Controller
    # trunk-ignore(ruff/F821)
    _parentView: "View"

    @property
    def model(self):
        return self._model

    @property
    def controller(self):
        return self._controller

    @property
    def parentView(self):
        return self._parentView

    def __post_init__(self):
        super().__init__()

        layout = QVBoxLayout()

        self.window_select = QComboBox()
        self.window_select.addItems(
            [wf.capitalize() for wf in self.model.get_windows()]
        )
        self.window_select.setCurrentIndex(
            self.model.get_windows().index(self.model.window)
        )
        self.window_select.setToolTip("Fensterfunktion für Ausgabesignal")

        self.signals_hertz = SingleLineEdit(
            QDoubleValidator(0.5, self.model.fs // 2, 1),
            str(self.model.hertz),
            "Frequenz [Hz]",
            "Signalfrequenz",
        )

        self.signals_sigma = SingleLineEdit(
            QDoubleValidator(0.01, self.model.fs // 2, 3),
            str(self.model.sigma),
            "Sigma",
            "Sigma-Wert _nur_ für das Gauß-Fenster",
        )

        self.signals_duration = SingleLineEdit(
            QIntValidator(1, 10**5),
            str(self.model.duration),
            "Signaldauer [ms]",
            "Dauer eines einzelnen Signals ohne Fenster",
        )

        self.signals_window_open_length = SingleLineEdit(
            QIntValidator(0, 10**5),
            str(self.model.window_open_length),
            "Fenster (Start) [ms]",
            "Breite des Fensters vor dem Signal",
        )

        self.signals_window_close_length = SingleLineEdit(
            QIntValidator(0, 10**5),
            str(self.model.window_close_length),
            "Fenster (Stop) [ms]",
            "Breite des Fensters nach dem Signal",
        )

        self.signals_start_offset = SingleLineEdit(
            QIntValidator(0, 10**5),
            str(self.model.start_offset),
            "Offset (Start) [ms]",
            "Offset vor dem Signal",
        )

        self.signals_stop_offset = SingleLineEdit(
            QIntValidator(0, 10**5),
            str(self.model.stop_offset),
            "Offset (Stop) [ms]",
            "Offset nach dem Signal",
        )

        buttons = QHBoxLayout()
        button_apply = QPushButton("Anwenden")
        button_apply.clicked.connect(self.apply_changes)
        button_delete = QPushButton("Löschen")
        button_delete.clicked.connect(self.remove_instance)
        buttons.addWidget(button_apply)
        buttons.addWidget(button_delete)

        layout.addWidget(self.window_select)
        layout.addLayout(self.signals_hertz)
        layout.addLayout(self.signals_sigma)
        layout.addLayout(self.signals_duration)
        layout.addLayout(self.signals_window_open_length)
        layout.addLayout(self.signals_window_close_length)
        layout.addLayout(self.signals_start_offset)
        layout.addLayout(self.signals_stop_offset)
        layout.addLayout(buttons)

        self.setLayout(layout)

    def apply_changes(self):
        self.model.update(
            {
                "window_function": self.window_select.currentText().lower(),
                "hertz": int(self.signals_hertz.picker.text()),
                "sigma": float(self.signals_sigma.picker.text()),
                "duration": int(self.signals_duration.picker.text()),
                "window_open_length": int(
                    self.signals_window_open_length.picker.text()
                ),
                "window_close_length": int(
                    self.signals_window_close_length.picker.text()
                ),
                "start_offset": int(self.signals_start_offset.picker.text()),
                "stop_offset": int(self.signals_stop_offset.picker.text()),
            }
        )
        self.parentView.update_source_graphs()

    def remove_instance(self):
        self.controller.remove_signal(self.model)
        self.parentView.update_source_graphs()
        self.parentView.signal_container_layout.removeWidget(self)
        self.deleteLater()
        del self
