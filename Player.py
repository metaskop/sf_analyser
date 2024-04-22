from struct import pack

from PySide6.QtCore import QByteArray, QIODevice
from PySide6.QtMultimedia import QAudioFormat


class Player(QIODevice):
    def __init__(
        self, sample_format: QAudioFormat = QAudioFormat.Int16, fs: int = 44100
    ):
        """
        Converts floating point data to `sample_format` and pretends to be a \
            device with given data.
        """
        super().__init__()

        self._sample_format = sample_format
        self._fs = fs
        self._audio_format = QAudioFormat()
        self._audio_format.setSampleRate(self.fs)
        self._audio_format.setChannelCount(1)
        self._audio_format.setSampleFormat(self.sample_format)
        self.buffer = QByteArray()
        self.float_data = []
        self.m_pos = 0

    @property
    def sample_format(self) -> QAudioFormat:
        return self._sample_format

    @sample_format.setter
    def sample_format(self, value: QAudioFormat):
        self._sample_format = value

    @property
    def fs(self) -> int:
        return self._fs

    @fs.setter
    def fs(self, value: int):
        self._fs = value

    @property
    def audio_format(self) -> QAudioFormat:
        return self._audio_format

    @audio_format.setter
    def audio_format(self, value: QAudioFormat):
        self._audio_format = value

    def start(self):
        if self.isOpen():
            self.stop()
        self.open(QIODevice.ReadOnly)

    def startSource(self):
        self.open(QIODevice.WriteOnly)

    def stop(self):
        self.m_pos = 0
        self.close()  # Inherited from QIODevice.

    def set_pos(self, pos: int):
        # Set position within reasonable limits of [0, len(buffer) - 1]
        self.m_pos = max(min(self.buffer.size() - 1, pos), 0)

    def set_data(self, float_data: list[float]):
        self.float_data = float_data
        self.generate_data()

    def set_raw_data(self, raw_data: QByteArray):
        self.buffer = raw_data

    def generate_data(self):
        self.buffer.clear()

        # TODO: consider variable sample format. Now it is Int16.
        # TODO: Shouldn't it be `chunk * 32767.5 - 0.5`?
        for chunk in self.float_data:
            self.buffer.append(pack("<h", int(chunk * 32767)))

    def readData(self, maxlen: int) -> bytes:
        old_pos = self.m_pos
        self.m_pos = min(self.buffer.size(), self.m_pos + maxlen)

        return self.buffer.data()[old_pos : self.m_pos]

    def writeData(self, data) -> int:
        return 0

    def bytesAvailable(self) -> int:
        return self.buffer.size() + super().bytesAvailable()
