import sys

from Controller import Controller
from PySide6.QtWidgets import QApplication
from SignalModel import SignalModel
from SingleSignalModel import SingleSignalModel
from View import View


class App(QApplication):
    def __init__(self, sys_argv):
        super(App, self).__init__(sys_argv)
        self.model = SignalModel()
        self.controller = Controller(self.model)
        self.view = View(self.model, self.controller)
        self.controller.set_view(self.view)
        self.view.show()


if __name__ == "__main__":
    app = App(sys.argv)
    main = View(app.model, app.controller)

    app.exec()
