from PySide6.QtCore import Qt
from PySide6.QtGui import QValidator
from PySide6.QtWidgets import QHBoxLayout, QLineEdit, QLabel
from typing import Callable


class SingleLineEdit(QHBoxLayout):
    def __init__(self,
                 validator: QValidator,
                 text: str,
                 label: str,
                 tooltip: str,
                 on_change: Callable | None = None):
        super().__init__()

        self._on_change = on_change

        self._picker = QLineEdit()
        self._picker.setValidator = validator
        self._picker.setText(text)
        self._picker.setToolTip(tooltip)
        self._picker.editingFinished.connect(self.editingFinished)

        self._label = QLabel(label)
        self._label.setToolTip(tooltip)
        self._label.setBuddy(self._picker)

        self.addWidget(self._picker)
        self.addWidget(self._label)

    def editingFinished(self):
        if self._on_change is None:
            return

        self._on_change(self._picker.text())

    @property
    def picker(self) -> QLineEdit:
        return self._picker

    @property
    def label(self) -> QLabel:
        return self._label
