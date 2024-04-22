import numpy as np
from PySide6.QtCore import QObject, Signal
from scipy import signal
from SingleSignalModel import SingleSignalModel


class SignalModel(QObject):
    # TODO: load and save settings and current status by specifiyng a file.
    _default_fs: int = 44100
    _default_hertz: int = 850
    _default_sigma: float = 2.5
    _default_duration: int = 600
    _default_start_offset: int = 0
    _default_stop_offset: int = 0
    _default_window: str = "cosine"
    _default_window_open_length: int = 200
    _default_window_close_length: int = 200
    _default_analyser_start: int = 0
    _default_analyser_stop: int = -1
    _default_calibration_sweep: str = "linear"
    _default_calibration_duration: int = 5000
    _default_calibration_freq_start: float = 220
    _default_calibration_freq_stop: float = 3520
    _filename: str = ""
    _recorded_data: list[float] = []
    _recorded_data_bak: list[float] = []

    _window_list: tuple[str] = (
        "blackmanharris",
        "bartlett",
        "boxcar",
        "cosine",
        "hann",
        "gaussian",
        "tukey",
    )
    _signal_list: list[SingleSignalModel] = []
    _sweep_list: tuple[str] = ("linear", "logarithmic", "hyperbolic")
    hertz_changed = Signal(float)

    def add_signal(self, signal: SingleSignalModel, index: int = -1):
        """Appends (default) or inserts a signal at a given `index`. If the
        `index` is out of range the signal will be appended."""
        if index <= -1:
            index = len(self._signal_list)
        # Python itself handles a positive out-of-range case, so nothing to do.
        self._signal_list.insert(index, signal)

    def remove_signal(self, index: int):
        self._signal_list.pop(index)

    def remove_all_signals(self):
        self._signal_list.clear()

    def get_windows(self) -> tuple[str]:
        return self._window_list

    def get_signals(self) -> list[SingleSignalModel]:
        return self._signal_list

    def get_frames(self, time: int) -> int:
        """Returns frame count with given time (in ms), according to self.fs."""
        return int(time * self.fs / 1000)

    def get_sweeps(self) -> tuple[str]:
        return self._sweep_list

    def generate_sweep(self) -> np.ndarray:
        return signal.chirp(
            np.linspace(0, self.calibration_duration / 1000, self.fs * self.calibration_duration // 1000),
            f0=self.calibration_freq_start,
            t1=self.calibration_duration / 1000,
            f1=self.calibration_freq_stop,
            method=self.calibration_sweep,
        )

    def __str__(self):
        return (
            f"{self.fs},{self.hertz},{self.sigma},{self.duration},"
            f"{self.start_offset},{self.stop_offset},{self.window},"
            f"{self.window_open_length},{self.window_close_length}"
        )

    @property
    def fs(self) -> int:
        return self._default_fs

    @fs.setter
    def fs(self, value):
        self._default_fs = value

    @property
    def hertz(self) -> float:
        return self._default_hertz

    @hertz.setter
    def hertz(self, value):
        self._default_hertz = value

    @property
    def sigma(self) -> float:
        return self._default_sigma

    @sigma.setter
    def sigma(self, value):
        self._default_sigma = value

    @property
    def duration(self) -> int:
        return self._default_duration

    @duration.setter
    def duration(self, value):
        self._default_duration = value

    @property
    def start_offset(self) -> int:
        return self._default_start_offset

    @start_offset.setter
    def start_offset(self, value):
        self._default_start_offset = value

    @property
    def stop_offset(self) -> int:
        return self._default_stop_offset

    @stop_offset.setter
    def stop_offset(self, value):
        self._default_stop_offset = value

    @property
    def window(self) -> str:
        return self._default_window

    @window.setter
    def window(self, value):
        self._default_window = value

    @property
    def window_open_length(self) -> int:
        return self._default_window_open_length

    @window_open_length.setter
    def window_open_length(self, value):
        self._default_window_open_length = value

    @property
    def window_close_length(self) -> int:
        return self._default_window_close_length

    @window_close_length.setter
    def window_close_length(self, value):
        self._default_window_close_length = value

    @property
    def filename(self) -> str:
        return self._filename

    @filename.setter
    def filename(self, value: str):
        self._filename = value

    @property
    def analyser_start(self) -> int:
        return self._default_analyser_start

    def set_analyser_start(self, value: int):
        self._default_analyser_start = max(0, value)

    @property
    def analyser_stop(self) -> int:
        return self._default_analyser_stop

    def set_analyser_stop(self, value: int):
        self._default_analyser_stop = value

    @property
    def calibration_sweep(self) -> str:
        return self._default_calibration_sweep

    @calibration_sweep.setter
    def calibration_sweep(self, value: str):
        self._default_calibration_sweep = value.lower()

    @property
    def calibration_duration(self) -> int:
        return self._default_calibration_duration

    @calibration_duration.setter
    def calibration_duration(self, value: int):
        self._default_calibration_duration = value

    @property
    def calibration_freq_start(self) -> float:
        return self._default_calibration_freq_start

    @calibration_freq_start.setter
    def calibration_freq_start(self, value: float):
        self._default_calibration_freq_start = value

    @property
    def calibration_freq_stop(self) -> float:
        return self._default_calibration_freq_stop

    @calibration_freq_stop.setter
    def calibration_freq_stop(self, value: float):
        self._default_calibration_freq_stop = value

    @property
    def recorded_data(self) -> list[float]:
        return self._recorded_data

    @recorded_data.setter
    def recorded_data(self, value: list[float]):
        self._recorded_data = value
