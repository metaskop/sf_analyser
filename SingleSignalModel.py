import numpy as np
from dataclasses import dataclass
from scipy import signal


@dataclass
class SingleSignalModel:
    fs: int                       # sampling frequency in Hz, e.g. 44100.
    hertz: int                    # frequency in Hz.
    sigma: int                    # Parameter for Gauss.
    duration: int                 # time in ms.
    start_offset: int             # time in ms.
    stop_offset: int              # time in ms.
    window_function: str          # scipy.signal.windows; tuple only for Gauss.
    window_open_length: int       # time in ms.
    window_close_length: int      # time in ms.

    # NOTE: Consider using times above 10 ms to avoid division errors.
    # E.g. duration * fs / 1000 should result in a whole number.

    def __post_init__(self):
        # Creating an opening and a closing window with the full signal
        # inbetween, so that it resembles _/'''\_.
        # Before and after there is the start and stop offset (a null signal).
        # The windows are added to the main signal, thus are exclusive.
        window_function = (("gauss", self.sigma)
                           if "gauss" in self.window_function
                           else self.window_function)
        window_open = signal.windows.get_window(
            window_function,
            self.window_open_length * self.fs * 2 // 1000,
            fftbins=False)[:self.window_open_length * self.fs // 1000]
        ones = [1.0 for _ in range(self.duration * self.fs // 1000)]
        window_close = signal.windows.get_window(
            window_function,
            self.window_close_length * self.fs * 2 // 1000,
            fftbins=False)[self.window_close_length * self.fs // 1000:]
        window = np.concatenate([window_open, ones, window_close])
        window_length = (
            self.window_open_length + self.duration + self.window_close_length)
        unwindowed_signal = np.sin(
            2 * np.pi * self.hertz *
            np.linspace(
                0, window_length / 1000, self.fs * window_length // 1000))

        self._data = np.concatenate([
            [0 for _ in range(self.start_offset * self.fs // 1000)],
            [y * w for y, w in zip(unwindowed_signal, window)],
            [0 for _ in range(self.stop_offset * self.fs // 1000)]])

        self._window_list: tuple[str] = (
            "blackmanharris", "bartlett", "boxcar",
            "cosine", "hann", "gaussian", "tukey")

    def update(self, attributes: dict[str, str | int | tuple]):
        """Alter multiple class attributes at once to reduce computation
        overhead. This method will only alter attributes which do exist.

        After alteration the new signal will be computed."""

        for key, value in attributes.items():
            if key not in self.__dict__:
                continue
            self.__dict__[key] = value

        self.__post_init__()

    def get_windows(self) -> list[str]:
        return self._window_list

    @property
    def data(self) -> list[float]:
        return self._data

    @property
    def window(self) -> str | tuple[str, float]:
        return self.window_function
