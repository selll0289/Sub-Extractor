"""Qt table models for displaying audio/subtitle track data."""

from __future__ import annotations

from typing import List

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt

from sub_extractor.models import AudioTrack, SubtitleTrack


class AudioTrackTableModel(QAbstractTableModel):
    """Table model for AudioTrack lists."""

    _HEADERS = ["#", "Codec", "Language", "Channels", "Title"]

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._tracks: List[AudioTrack] = []

    def set_tracks(self, tracks: List[AudioTrack]) -> None:
        """Replace all rows with new track data."""
        self.beginResetModel()
        self._tracks = list(tracks)
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self._tracks)

    def columnCount(self, parent=QModelIndex()) -> int:
        return len(self._HEADERS)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        if not index.isValid() or role != Qt.DisplayRole:
            return None
        track = self._tracks[index.row()]
        col = index.column()
        if col == 0:
            return str(track.index)
        elif col == 1:
            return track.codec
        elif col == 2:
            return track.language or "—"
        elif col == 3:
            return str(track.channels)
        elif col == 4:
            return track.title or "—"
        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self._HEADERS[section]
        return None


class SubtitleTrackTableModel(QAbstractTableModel):
    """Table model for embedded SubtitleTrack lists."""

    _HEADERS = ["#", "Codec", "Language", "Flags", "Title"]

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._tracks: List[SubtitleTrack] = []

    def set_tracks(self, tracks: List[SubtitleTrack]) -> None:
        """Replace all rows with new track data."""
        self.beginResetModel()
        self._tracks = list(tracks)
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self._tracks)

    def columnCount(self, parent=QModelIndex()) -> int:
        return len(self._HEADERS)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        if not index.isValid() or role != Qt.DisplayRole:
            return None
        track = self._tracks[index.row()]
        col = index.column()
        if col == 0:
            return str(track.index)
        elif col == 1:
            return track.codec
        elif col == 2:
            return track.language or "—"
        elif col == 3:
            flags = []
            if track.is_default:
                flags.append("default")
            if track.is_forced:
                flags.append("forced")
            if track.is_hearing_impaired:
                flags.append("SDH")
            return ", ".join(flags) if flags else "—"
        elif col == 4:
            return track.title or "—"
        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self._HEADERS[section]
        return None


class ExternalSubTableModel(QAbstractTableModel):
    """Table model for external subtitle files."""

    _HEADERS = ["Codec", "Language", "File"]

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._tracks: List[SubtitleTrack] = []

    def set_tracks(self, tracks: List[SubtitleTrack]) -> None:
        """Replace all rows with new data."""
        self.beginResetModel()
        self._tracks = list(tracks)
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self._tracks)

    def columnCount(self, parent=QModelIndex()) -> int:
        return len(self._HEADERS)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        if not index.isValid() or role != Qt.DisplayRole:
            return None
        track = self._tracks[index.row()]
        col = index.column()
        if col == 0:
            return track.codec
        elif col == 1:
            return track.language or "—"
        elif col == 2:
            return track.title or "—"
        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self._HEADERS[section]
        return None
