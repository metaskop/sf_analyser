from struct import unpack

import numpy as np
from ConfigParser import ConfigParser
from Player import Player
from PySide6.QtCore import QByteArray, QIODevice, QTimer
from PySide6.QtMultimedia import (
    QAudio,
    QAudioDevice,
    QAudioFormat,
    QAudioSink,
    QAudioSource,
    QMediaDevices,
)
from Recorder import Recorder
from scipy.io import wavfile
from SignalModel import SignalModel
from SingleSignalModel import SingleSignalModel


class Controller:
    def __init__(self, model: SignalModel):
        self._model = model
        self.view = None
        self._input_device = self.get_audio_inputs()[0]
        self._output_device = self.get_audio_outputs()[0]
        self.init_player()
        self.init_recorder()

    def set_view(self, view):
        self.view = view

    def init_player(self):
        self._player = Player(QAudioFormat.Int16, self.model.fs)
        self._audio_sink = QAudioSink(self.output_device, self.player.audio_format)
        self._audio_sink.stateChanged.connect(self.handle_state_changed)

    def reset_player(self):
        del self._player
        del self._audio_sink
        self.init_player()

    def init_recorder(self):
        self._record_buffer: QByteArray = QByteArray()
        self._recorder = Recorder(QAudioFormat.Int16, self.model.fs)
        self._recorder.readyRead.connect(self.handle_ready_read)
        self._audio_source = QAudioSource(self.input_device, self.recorder.audio_format)

    @property
    def model(self) -> SignalModel:
        return self._model

    @property
    def player(self) -> QIODevice:
        return self._player

    @property
    def recorder(self) -> QAudioDevice:
        return self._recorder

    @recorder.setter
    def recorder(self, value: QIODevice):
        self._recorder = value

    @property
    def audio_sink(self) -> QAudioSink:
        return self._audio_sink

    @property
    def audio_source(self) -> QAudioSource:
        return self._audio_source

    def set_fs(self, fs: str):
        self.model.fs = int(fs)

    def set_hertz(self, hertz: str):
        self.model.fs = int(hertz)

    def set_sigma(self, sigma: str):
        self.model.sigma = float(sigma)

    def set_duration(self, duration: str):
        self.model.duration = duration

    def set_start_offset(self, start_offset: str):
        self.model.start_offset = int(start_offset)

    def set_stop_offset(self, stop_offset: str):
        self.model.stop_offset = int(stop_offset)

    def set_window(self, window: str):
        if window.lower() not in self.model.get_windows():
            window = self.model.window
        self.model.window = window.lower()

    def set_window_open_length(self, window_open_length: str):
        self.model.window_open_length = int(window_open_length)

    def set_window_close_length(self, window_close_length: str):
        self.model.window_close_length = int(window_close_length)

    def set_analyser_interval(self, start: float, stop: float):
        self.model.set_analyser_start(start)
        self.model.set_analyser_stop(stop)

    def set_save_filename(self, filename: str):
        self.model.filename = filename

    def set_calibration(self, sweep: str, duration: int, f_start: float, f_stop: float):
        self.set_calibration_sweep(sweep)
        self.set_calibration_duration(duration)
        self.set_calibration_freq_start(f_start)
        self.set_calibration_freq_stop(f_stop)

    def set_calibration_sweep(self, value: str):
        self.model.calibration_sweep = value

    def set_calibration_duration(self, value: int):
        self.model.calibration_duration = value

    def set_calibration_freq_start(self, value: float):
        self.model.calibration_freq_start = value

    def set_calibration_freq_stop(self, value: float):
        self.model.calibration_freq_stop = value

    def add_signal(self):
        self.model.add_signal(
            SingleSignalModel(
                int(self.model.fs),
                int(self.model.hertz),
                float(self.model.sigma),
                int(self.model.duration),
                int(self.model.start_offset),
                int(self.model.stop_offset),
                self.model.window.lower(),
                int(self.model.window_open_length),
                int(self.model.window_close_length),
            ),
            -1,
        )

    def load_signals(self, filename: str):
        signals = ConfigParser.load(filename)
        self.set_save_filename(filename)

        if len(signals) == 0:
            # TODO: Viewer window with Loading Error.
            return

        for signal in signals:
            self.model.add_signal(signal)

    def save_signals(self, filename: str):
        ConfigParser.save(filename, self.model.get_signals())
        self.set_save_filename(filename)

    def remove_signal(self, signal: SingleSignalModel):
        self.model.remove_signal(self.model.get_signals().index(signal))

    @staticmethod
    def get_audio_inputs() -> list[QAudioDevice]:
        return QMediaDevices.audioInputs()

    @property
    def input_device(self) -> QAudioDevice:
        return self._input_device

    def set_input_device(self, device_num: int):
        self.input_device.swap(self.get_audio_inputs()[device_num])
        self.init_recorder()

    def set_input_format(self, format_num: int):
        self.recorder.audio_format = self.supported_audio_formats(self.input_device)[format_num]
        self.model.fs = self.supported_audio_formats(self.input_device)[format_num].sampleRate()

    @staticmethod
    def get_audio_outputs() -> list[QAudioDevice]:
        return QMediaDevices.audioOutputs()

    @property
    def output_device(self) -> QAudioDevice:
        return self._output_device

    def supported_audio_formats(self, audio_device: QAudioDevice) -> list[QAudioFormat]:
        format_list = []
        for fs in (22050, 44100, 48000, 96000, 192000):
            qformat = QAudioFormat()
            qformat.setSampleRate(fs)
            qformat.setChannelCount(1)
            qformat.setSampleFormat(QAudioFormat.Int16)

            if audio_device.isFormatSupported(qformat):
                format_list.append(qformat)

        return format_list

    def set_output_device(self, device_num: int):
        self.output_device.swap(self.get_audio_outputs()[device_num])
        self.reset_player()

    def set_output_format(self, format_num: int):
        self.player.audio_format = self.supported_audio_formats(self.output_device)[format_num]

    def record(self):
        self._record_buffer.clear()
        # FIXME: Why is Recorder() not working? Thanks Qt!
        # FIXME: self._record_buffer -> self.recorder.buffer.
        self.recorder = self.audio_source.start()
        self.recorder.readyRead.connect(self.handle_ready_read)

    def play_record(self, data: list[float] | bool = False):
        if data is False:
            data = np.concatenate([s.data for s in self.model.get_signals()])
        self.player.set_data(data)
        self.record()
        self.player.start()
        self.audio_sink.start(self.player)

    def handle_ready_read(self):
        # .readAll() is inherited by QIODevice.
        self._record_buffer.append(self.recorder.readAll())

    def handle_state_changed(self, state: QAudio.State | QAudio.Error):
        if state == QAudio.IdleState:
            self._audio_sink.stop()
            self.player.stop()
            QTimer.singleShot(500, self.stop_recording_with_offset)

        if self.audio_sink.error() != QAudio.NoError:
            print(self.audio_sink.error())

    def stop_recording_with_offset(self):
        # TODO: possible bug in conversion. Do we need to convert at all?
        self.audio_source.stop()
        self.model.recorded_data = np.array(
            [
                i / 32767
                for i in unpack(
                    f"<{len(self._record_buffer.data()) >> 1}h",
                    self._record_buffer.data(),
                )
            ]
        )

        self.view.update_sink_graphs()
        # TODO: automatically update_sink_graphs() in View.

    def export_audio(self, filename: str):
        wavfile.write(filename, self.model.fs, self.model.recorded_data)
