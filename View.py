import numpy as np
import pyqtgraph as pg
from Controller import Controller
from PySide6.QtCore import QCoreApplication, QLocale, Qt
from PySide6.QtGui import (
    QAction,
    QDoubleValidator,
    QIntValidator,
    QKeySequence,
    QPalette,
)
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtMultimedia import QAudioFormat
from scipy.fft import fft
from scipy.signal.windows import hann
from SignalModel import SignalModel
from SingleLineEdit import SingleLineEdit
from SingleSignalModel import SingleSignalModel
from SingleSignalView import SingleSignalView


class View(QMainWindow):
    def __init__(self, model: SignalModel, controller: Controller):
        super().__init__()

        # Be able to parse input fields correctly by float() itself.
        _locale = QLocale(QLocale.English, QLocale.UnitedStates)

        self._model = model
        self._controller = controller

        _ = Qt.AlignmentFlag.AlignTop

        # column1 | column2 | column3
        # ---------------------------
        #  graph  | graph3  | -Tabs-
        # ------------------| inputs
        #  graph2 | graph4  | inputs

        self.window = QWidget()
        self.setWindowTitle("Stepped Frequency Analyser")
        menu = self.menuBar()
        self.layout = QHBoxLayout()
        self.first_column = QVBoxLayout()  # Player Section.
        self.second_column = QVBoxLayout()  # Recording Section.
        self.third_column = QTabWidget()  # Signals, Analysis and Calibration.
        self.layout.addLayout(self.first_column)
        self.layout.addLayout(self.second_column)
        self.layout.addWidget(self.third_column)
        self.window.setLayout(self.layout)
        self.window.setWindowFlags(Qt.WindowTitleHint)

        # Menu.
        menu_open_action = QAction("&Open", self)
        menu_open_action.setShortcut(QKeySequence("Ctrl+O"))
        menu_open_action.triggered.connect(self.menu_file_open_dialog)
        menu_save_action = QAction("&Save", self)
        menu_save_action.setShortcut(QKeySequence("Ctrl+S"))
        menu_save_action.triggered.connect(self.menu_file_save_dialog)
        menu_save_as_action = QAction("&Save As", self)
        menu_save_as_action.setShortcut(QKeySequence("Ctrl+Shift+S"))
        menu_save_as_action.triggered.connect(self.menu_file_save_as_dialog)
        menu_export_action = QAction("&Export Audio File", self)
        menu_export_action.setShortcut(QKeySequence("Ctrl+Shift+E"))
        menu_export_action.triggered.connect(self.menu_file_export_dialog)
        menu_quit_action = QAction("&Quit", self)
        menu_quit_action.setShortcut(QKeySequence("Ctrl+Q"))
        menu_quit_action.triggered.connect(QCoreApplication.quit)
        menu_refresh_action = QAction("&Refresh", self)
        menu_refresh_action.setShortcut(QKeySequence("Ctrl+R"))
        menu_refresh_action.triggered.connect(self.update_sink_graphs)

        file_menu = menu.addMenu("&File")

        file_menu.addAction(menu_open_action)
        file_menu.addAction(menu_save_action)
        file_menu.addAction(menu_save_as_action)
        file_menu.addAction(menu_export_action)
        file_menu.addAction(menu_quit_action)
        file_menu.addAction(menu_refresh_action)

        # Input / Output section.
        input_select_layout = QHBoxLayout()
        input_select_label = QLabel("Eingabegerät: ")
        input_select_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        input_select = QComboBox()
        for device_info in self.controller.get_audio_inputs():
            input_select.addItem(device_info.description(), device_info)
        input_select.currentIndexChanged.connect(self.controller.set_input_device)
        input_select.setToolTip("Eingabegerät zur Aufnahme")
        input_select_label.setToolTip("Eingabegerät zur Aufnahme")
        input_select_label.setBuddy(input_select)
        input_select_layout.addWidget(input_select_label)
        input_select_layout.addWidget(input_select, stretch=1)

        input_fs_select_layout = QHBoxLayout()
        input_fs_select_label = QLabel("Sample-Rate:  ")
        input_fs_select_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        input_fs_select = QComboBox()
        for fs in self.controller.supported_audio_formats(self.controller.input_device):
            input_fs_select.addItem(f"{fs.sampleRate()} Hz", fs)
        input_fs_select.currentIndexChanged.connect(self.controller.set_input_format)
        # TODO: setCurrentIndex needs to be in the preferred format, but only with 1 channel.
        input_fs_select.setCurrentIndex(1)
        input_fs_select.setToolTip("Sample-Rate für Aufnahme")
        input_fs_select_label.setToolTip("Sample-Rate für Aufnahme")
        input_fs_select_label.setBuddy(input_fs_select)
        input_fs_select_layout.addWidget(input_fs_select_label)
        input_fs_select_layout.addWidget(input_fs_select, stretch=1)

        output_select_layout = QHBoxLayout()
        output_select_label = QLabel("Ausgabegerät: ")
        output_select_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        output_select = QComboBox()
        for device_info in self.controller.get_audio_outputs():
            output_select.addItem(device_info.description(), device_info)
        output_select.currentIndexChanged.connect(self.controller.set_output_device)
        output_select.setToolTip("Ausgabegerät zur Wiedergabe")
        output_select_label.setToolTip("Ausgabegerät zur Wiedergabe")
        output_select_label.setBuddy(output_select)
        output_select_layout.addWidget(output_select_label)
        output_select_layout.addWidget(output_select, stretch=1)

        output_fs_select_layout = QHBoxLayout()
        output_fs_select_label = QLabel("Sample-Rate:   ")
        output_fs_select_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        output_fs_select = QComboBox()
        for fs in self.controller.supported_audio_formats(self.controller.output_device):
            output_fs_select.addItem(f"{fs.sampleRate()} Hz", fs)
        output_fs_select.currentIndexChanged.connect(self.controller.set_output_format)
        # TODO: setCurrentIndex needs to be in the preferred format, but only with 1 channel.
        output_fs_select.setCurrentIndex(1)
        output_fs_select.setToolTip("Sample-Rate für Wiedergabe")
        output_fs_select_label.setToolTip("Sample-Rate für Wiedergabe")
        output_fs_select_label.setBuddy(output_fs_select)
        output_fs_select_layout.addWidget(output_fs_select_label)
        output_fs_select_layout.addWidget(output_fs_select, stretch=1)
        # graph  |  graph3
        # =output|  =input
        # ----------------
        # graph2 |  graph4
        # =fft(o)|  =fft(i)
        self.graph = pg.GraphicsLayoutWidget(title="Signal Analyzer")
        self.graph.setWindowTitle("Signal Analyzer")
        self.graphWidget = pg.PlotWidget(background="w")
        self.graphWidget.showGrid(x=True, y=True)
        self.graphWidget.getAxis("left").setLabel("Amplitude")
        self.graphWidget.getAxis("bottom").setLabel("Zeit", "s")
        self.graphWidgetPlot = self.graphWidget.plot(pen="r")
        graphHeadline = QLabel("Abfragesignal")
        graphHeadline.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        self.graph2 = pg.GraphicsLayoutWidget()
        self.graph2Widget = pg.PlotWidget(background="w")
        self.graph2Widget.showGrid(x=True, y=True)
        self.graph2Widget.setLogMode(y=True)
        self.graph2Widget.getAxis("left").setLabel("Amplitude")
        self.graph2Widget.getAxis("bottom").setLabel("Frequenz", "Hz")
        self.graph2WidgetPlot = self.graph2Widget.plot(pen="r")
        graph2Headline = QLabel("Spektrum des Abfragesignals")
        graph2Headline.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        self.graph3 = pg.GraphicsLayoutWidget()
        self.graph3Widget = pg.PlotWidget(background="w")
        self.graph3Widget.showGrid(x=True, y=True)
        self.graph3Widget.getAxis("bottom").setLabel("Zeit", "s")
        self.graph3WidgetPlot = self.graph3Widget.plot(pen="r")
        graph3Headline = QLabel("Antwortsignal")
        graph3Headline.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        self.graph4 = pg.GraphicsLayoutWidget()
        self.graph4Widget = pg.PlotWidget(background="w")
        self.graph4Widget.showGrid(x=True, y=True)
        self.graph4Widget.setLogMode(y=True)
        self.graph4Widget.getAxis("bottom").setLabel("Frequenz", "Hz")
        self.graph4WidgetPlot = self.graph4Widget.plot(pen="r")
        graph4Headline = QLabel("Spektrum des Antwortsignals")
        graph4Headline.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        # [Signals | Analysis | Calibration] tabs.
        self.tab_signal = QWidget()
        self.tab_analysis = QWidget()
        self.tab_calibration = QWidget()

        self.signal_layout = QVBoxLayout()
        self.signal_container = QWidget()
        self.signal_container_layout = QVBoxLayout()
        self.signal_container_layout.setAlignment(Qt.AlignmentFlag.AlignBottom)
        self.signal_container.setLayout(self.signal_container_layout)
        self.signal_scroll = QScrollArea()
        self.signal_scroll.setWidget(self.signal_container)
        self.signal_scroll.setWidgetResizable(True)
        self.signal_container_layout.insertStretch(0)

        self.analysis_layout = QVBoxLayout()
        self.calibration_layout = QVBoxLayout()

        self.tab_signal.setLayout(self.signal_layout)
        self.tab_analysis.setLayout(self.analysis_layout)
        self.tab_calibration.setLayout(self.calibration_layout)

        # Signals.
        # Window function selector for output signal.
        window_select = QComboBox()
        window_select.addItems([wf.capitalize() for wf in self.model.get_windows()])
        window_select.setCurrentIndex(self.model.get_windows().index(self.model.window))
        window_select.setToolTip("Fensterfunktion für Ausgabesignal")
        window_select.currentTextChanged.connect(self.controller.set_window)

        signals_hertz = SingleLineEdit(
            QDoubleValidator(0.5, self.model.fs // 2, 1),
            str(self.model.hertz),
            "Frequenz [Hz]",
            "Signalfrequenz",
            self.controller.set_hertz,
        )

        signals_sigma = SingleLineEdit(
            QDoubleValidator(0.01, self.model.fs // 2, 3),
            str(self.model.sigma),
            "Sigma",
            "Sigma-Wert _nur_ für das Gauß-Fenster",
            self.controller.set_sigma,
        )

        signals_duration = SingleLineEdit(
            QIntValidator(1, 10**5),
            str(self.model.duration),
            "Signaldauer [ms]",
            "Dauer eines einzelnen Signals ohne Fenster",
            self.controller.set_duration,
        )

        signals_window_open_length = SingleLineEdit(
            QIntValidator(0, 10**5),
            str(self.model._default_window_open_length),
            "Fenster (Start) [ms]",
            "Breite des Fensters vor dem Signal",
            self.controller.set_window_open_length,
        )

        signals_window_close_length = SingleLineEdit(
            QIntValidator(0, 10**5),
            str(self.model._default_window_close_length),
            "Fenster (Stop) [ms]",
            "Breite des Fensters nach dem Signal",
            self.controller.set_window_close_length,
        )

        signals_start_offset = SingleLineEdit(
            QIntValidator(0, 10**5),
            str(self.model.start_offset),
            "Offset (Start) [ms]",
            "Offset vor dem Signal",
            self.controller.set_start_offset,
        )

        signals_stop_offset = SingleLineEdit(
            QIntValidator(0, 10**5),
            str(self.model.stop_offset),
            "Offset (Stop) [ms]",
            "Offset nach dem Signal",
            self.controller.set_stop_offset,
        )

        button_add = QPushButton("Signal hinzufügen")
        button_add.clicked.connect(self.add_signal)

        button_remove_signals = QPushButton("Alle Signale entfernen")
        button_remove_signals.clicked.connect(self.remove_all_signals)

        # Analysis.
        analyse_start_row = QHBoxLayout()
        analyse_start_picker = QLineEdit()
        analyse_start_picker.setValidator(QIntValidator(0, 100000))  # time:ms.
        analyse_start_picker.setText("0")
        analyse_start_picker.setToolTip("Beginn des Analyseabschnitts")
        analyse_start_label = QLabel("Analyser Start [ms]")
        analyse_start_label.setToolTip(analyse_start_picker.toolTip())
        analyse_start_label.setBuddy(analyse_start_picker)
        analyse_start_row.addWidget(analyse_start_picker)
        analyse_start_row.addWidget(analyse_start_label)

        analyse_stop_row = QHBoxLayout()
        analyse_stop_picker = QLineEdit()
        analyse_stop_picker.setValidator(QIntValidator(-1, 100000))  # time:ms.
        analyse_stop_picker.setText("-1")
        analyse_stop_picker.setToolTip("Ende des Analyseabschnitts; Ende: -1")
        analyse_stop_label = QLabel("Analyser Stop [ms]")
        analyse_stop_label.setToolTip(analyse_stop_picker.toolTip())
        analyse_stop_label.setBuddy(analyse_stop_picker)
        analyse_stop_row.addWidget(analyse_stop_picker)
        analyse_stop_row.addWidget(analyse_stop_label)

        button_set_analyse_interval = QPushButton("Anwenden")
        button_set_analyse_interval.clicked.connect(
            lambda: self.set_analyser_interval(
                analyse_start_picker.text(), analyse_stop_picker.text()
            )
        )

        button_reset_analyse_interval = QPushButton("Zurücksetzen")
        button_reset_analyse_interval.clicked.connect(
            lambda: self.set_analyser_interval(0, -1)
        )

        region = pg.LinearRegionItem()
        region.sigRegionChangeFinished.connect(
            lambda x: self.set_analyser_interval(
                *(int(xy * 1000) for xy in x.getRegion())
            )
        )
        region.sigRegionChanged.connect(
            lambda x: self.set_analyser_text_wrapper(
                analyse_start_picker, analyse_stop_picker, x.getRegion()
            )
        )

        check_region = QCheckBox("Auswahlfenster (experimentell)")
        check_region.setChecked(False)
        check_region.clicked.connect(lambda b: self.graph3Widget.addItem(region) if b else self.graph3Widget.removeItem(region))
        # self.graph3Widget.addItem(region)

        # Calibration
        calibration_sweep_select = QComboBox()
        calibration_sweep_select.addItems(
            [s.capitalize() for s in self.model.get_sweeps()]
        )
        calibration_sweep_select.setToolTip("Art des Frequenzdurchlaufs")
        calibration_sweep_select.currentTextChanged.connect(
            self.controller.set_calibration_sweep
        )

        calibration_duration = SingleLineEdit(
            QIntValidator(1, 10**5),
            str(self.model.calibration_duration),
            "Sweep-Dauer [ms]",
            "Dauer des gesamten Sweeps in Millisekunden",
            self.controller.set_calibration_duration,
        )
        calibration_freq_start = SingleLineEdit(
            QDoubleValidator(0.5, self.model.fs // 2, 1),
            str(self.model.calibration_freq_start),
            "Startfrequenz [Hz]",
            "Untere Frequenz des Sweeps",
            self.controller.set_calibration_freq_start,
        )
        calibration_freq_stop = SingleLineEdit(
            QDoubleValidator(0.5, self.model.fs // 2, 1),
            str(self.model.calibration_freq_stop),
            "Stopfrequenz [Hz]",
            "Obere Frequenz des Sweeps",
        )

        button_change_calibration = QPushButton("Änderungen anwenden")
        button_change_calibration.clicked.connect(
            lambda: self.controller.set_calibration(
                calibration_sweep_select.currentText(),
                int(calibration_duration.picker.text()),
                float(calibration_freq_start.picker.text()),
                float(calibration_freq_stop.picker.text()),
            )
        )
        button_set_calibration = QPushButton("Sweep Wiedergabe / Aufnahme")
        button_set_calibration.clicked.connect(
            lambda: self.controller.play_record(self.model.generate_sweep())
        )

        # Putting everything together.
        self.signal_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.signal_layout.addWidget(self.signal_scroll)
        self.signal_layout.addWidget(window_select)
        self.signal_layout.addLayout(signals_sigma)
        self.signal_layout.addLayout(signals_hertz)
        self.signal_layout.addLayout(signals_duration)
        self.signal_layout.addLayout(signals_window_open_length)
        self.signal_layout.addLayout(signals_window_close_length)
        self.signal_layout.addLayout(signals_start_offset)
        self.signal_layout.addLayout(signals_stop_offset)
        self.signal_layout.addWidget(button_add)
        self.signal_layout.addWidget(button_remove_signals)

        self.analysis_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.analysis_layout.addLayout(analyse_start_row)
        self.analysis_layout.addLayout(analyse_stop_row)
        self.analysis_layout.addWidget(button_set_analyse_interval)
        self.analysis_layout.addWidget(button_reset_analyse_interval)
        self.analysis_layout.addWidget(check_region)

        self.calibration_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.calibration_layout.addWidget(calibration_sweep_select)
        self.calibration_layout.addLayout(calibration_duration)
        self.calibration_layout.addLayout(calibration_freq_start)
        self.calibration_layout.addLayout(calibration_freq_stop)
        self.calibration_layout.addWidget(button_change_calibration)
        self.calibration_layout.addWidget(button_set_calibration)

        self.first_column.addLayout(output_select_layout)
        self.first_column.addLayout(output_fs_select_layout)
        self.first_column.addWidget(graphHeadline)
        self.first_column.addWidget(self.graphWidget)
        self.first_column.addWidget(graph2Headline)
        self.first_column.addWidget(self.graph2Widget)
        self.second_column.addLayout(input_select_layout)
        self.second_column.addLayout(input_fs_select_layout)
        self.second_column.addWidget(graph3Headline)
        self.second_column.addWidget(self.graph3Widget)
        self.second_column.addWidget(graph4Headline)
        self.second_column.addWidget(self.graph4Widget)
        # third_column.addWidget(type_select)
        self.third_column.addTab(self.tab_signal, "Signals")
        self.third_column.addTab(self.tab_analysis, "Analysis")
        self.third_column.addTab(self.tab_calibration, "Calibration")
        # third_column.addLayout(normalize_row)

        # Buttons for Play / Record, Reset, Export.
        # buttons = QVBoxLayout()
        play_button = QPushButton("Wiedergabe / Aufnahme")
        play_button.clicked.connect(self.controller.play_record)
        reset_button = QPushButton("Audio zurücksetzen")
        reset_button.clicked.connect(self.controller.reset_player)
        export_button = QPushButton("Audio exportieren")
        export_button.clicked.connect(self.menu_file_export_dialog)
        self.signal_layout.addWidget(
            play_button, alignment=Qt.AlignmentFlag.AlignBottom
        )
        self.signal_layout.addWidget(
            reset_button, alignment=Qt.AlignmentFlag.AlignBottom
        )
        self.signal_layout.addWidget(
            export_button, alignment=Qt.AlignmentFlag.AlignBottom
        )
        # self.signal_layout.addLayout(buttons, )

        self.setCentralWidget(self.window)

    @property
    def model(self) -> SignalModel:
        return self._model

    @property
    def controller(self) -> Controller:
        return self._controller

    def remove_all_signals(self):
        for i in range(self.signal_container_layout.count(), 0, -1):
            # Catch the NoneType items.
            try:
                self.signal_container_layout.itemAt(i).widget().remove_instance()
            except AttributeError:
                continue

    def menu_file_open_dialog(self, s):
        filename = QFileDialog.getOpenFileName(
            self, "Open config file", "../Messungen", "Config Files (*.cfg)"
        )

        if not filename:
            return

        # 1. Remove all Signals from View and transitively from Model.
        # 2. Put all signals into SignalModel.
        # 3. Add all new Signals from Model to View.

        self.remove_all_signals()

        self.controller.load_signals(filename[0])

        for signal in self.model.get_signals():
            self.signal_container_layout.addWidget(
                SingleSignalView(signal, self.controller, self)
            )

        self.update_source_graphs()

    def menu_file_save_as_dialog(self, s):
        file_dialog = QFileDialog()
        file_dialog.setDefaultSuffix(".cfg")
        filename = file_dialog.getSaveFileName(
            self, "Save config file", "../Messungen", "Config Files (*.cfg)"
        )

        if not filename:
            # TODO: Error
            return

        self.controller.save_signals(filename[0])

    def menu_file_export_dialog(self, s):
        file_dialog = QFileDialog()
        file_dialog.setDefaultSuffix(".wav")
        filename = file_dialog.getSaveFileName(
            self, "Save audio file", "../Messungen", "Wave Files (*.wav)"
        )

        if not filename:
            # TODO: Error
            return

        self.controller.export_audio(filename[0])

    def menu_file_save_dialog(self, s):
        # If a name is already set, use this for saving.
        if self.model.filename:
            self.controller.save_signals(self.model.filename)
            return
        # Otherwise choose one via the "Save As" dialog.
        self.menu_file_save_as_dialog("")

    def view_signals(self):
        for signal in self.model.get_signals():
            self.add_signal(signal)

    def add_signal(self):
        self.controller.add_signal()
        signal: SingleSignalModel = self.model.get_signals()[-1]
        self.signal_container_layout.addWidget(
            SingleSignalView(signal, self.controller, self)
        )
        self.update_source_graphs()

    def set_sweep(self): ...

    def set_analyser_interval(self, start: str | int, stop: str | int):
        self.controller.set_analyser_interval(int(start), int(stop))
        self.update_sink_graphs()

    def set_analyser_text_wrapper(
        self, start_field: QLineEdit, stop_field: QLineEdit, coords: tuple[float]
    ):
        start_field.setText(f"{int(coords[0] * 1000)}")
        stop_field.setText(f"{int(coords[1] * 1000)}")

    def update_source_graphs(self):
        # We want to update `graph` and `graph2` here.
        if not len(self.model.get_signals()):
            self.graphWidgetPlot.setData([], [])
            self.graph2WidgetPlot.setData([], [])

            return

        data = np.concatenate([x.data for x in self.model.get_signals()])
        data_range = np.linspace(0, len(data) / self.model.fs, len(data))
        data_fft = fft(data)
        data_fft = data_fft[: len(data_fft) // 2]
        data_fft_range = np.linspace(0, self.model.fs // 2, len(data_fft))

        self.graphWidgetPlot.setData(data_range, data)
        self.graph2WidgetPlot.setData(data_fft_range, abs(data_fft))

    def update_sink_graphs(self):
        # TODO: Move calulations away from here, e.g. in a seperate functions.py file.
        # TODO: make window changeable.
        # We want to update `graph3` and `graph4` here.
        if not len(self.model.recorded_data):
            self.graph3WidgetPlot.setData([], [])
            self.graph4WidgetPlot.setData([], [])

            return

        data = self.model.recorded_data
        data = data[
            self.model.get_frames(self.model.analyser_start) : self.model.get_frames(
                self.model.analyser_stop
            )
        ]
        data_range = np.linspace(0, len(data) / self.model.fs, len(data))
        data_fft = fft([s * w for s, w in zip(data, hann(len(data)), strict=True)])
        data_fft = data_fft[: len(data_fft) // 2]
        data_fft_range = np.linspace(0, self.model.fs // 2, len(data_fft))

        self.graph3WidgetPlot.setData(data_range, data)
        self.graph4WidgetPlot.setData(data_fft_range, np.abs(data_fft) / len(data_fft))
