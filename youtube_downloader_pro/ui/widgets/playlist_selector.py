from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QDialog, QHBoxLayout, QListWidget, QListWidgetItem, QVBoxLayout

from youtube_downloader_pro.i18n import tr
from youtube_downloader_pro.ui.widgets.common import button, label


class PlaylistSelector(QDialog):
    page_requested = Signal(int)

    def __init__(self, media: dict, selected: list[dict], parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(tr("Select playlist videos"))
        self.resize(700, 580)
        self.selected = {item["url"]: item for item in selected}
        self.media = media
        layout = QVBoxLayout(self)
        layout.addWidget(label(media["title"], "section", True, translate=False))
        self.info = label("", "muted")
        layout.addWidget(self.info)
        self.list = QListWidget()
        layout.addWidget(self.list, 1)
        controls = QHBoxLayout()
        controls.addWidget(button("Select All on page", lambda: self._select(True)))
        controls.addWidget(button("Select None", self._clear))
        self.previous = button("Previous", lambda: self._request(-100))
        self.next = button("Next 100", lambda: self._request(100))
        controls.addWidget(self.previous)
        controls.addWidget(self.next)
        layout.addLayout(controls)
        layout.addWidget(
            label(
                "Selections are kept across pages. Formats are checked per video "
                "when the queue starts.",
                "muted",
                True,
            )
        )
        self.done_button = button("Use selected videos", self.accept, True)
        layout.addWidget(self.done_button)
        self.set_page(media)

    def _remember(self) -> None:
        for i in range(self.list.count()):
            entry = self.list.item(i)
            media = entry.data(Qt.ItemDataRole.UserRole)
            if entry.checkState() == Qt.CheckState.Checked:
                self.selected[media["url"]] = media
            else:
                self.selected.pop(media["url"], None)

    def _select(self, checked: bool) -> None:
        for i in range(self.list.count()):
            self.list.item(i).setCheckState(
                Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked
            )

    def _clear(self) -> None:
        self.selected.clear()
        self._select(False)

    def _request(self, delta: int) -> None:
        self._remember()
        self.previous.setEnabled(False)
        self.next.setEnabled(False)
        self.done_button.setEnabled(False)
        self.info.setText(tr("Loading playlist page…"))
        self.page_requested.emit(self.media["start"] + delta)

    def set_page(self, media: dict) -> None:
        self.media = media
        self.list.clear()
        for entry in media["entries"]:
            row = QListWidgetItem(f"{entry.get('playlist_index') or '•'}   {entry['title']}")
            row.setData(Qt.ItemDataRole.UserRole, entry)
            row.setCheckState(
                Qt.CheckState.Checked if entry["url"] in self.selected else Qt.CheckState.Unchecked
            )
            self.list.addItem(row)
        self.info.setText(
            tr(
                "{count} videos · Showing {start}–{end}",
                count=media.get("count") or tr("Unknown total"),
                start=media["start"],
                end=media["start"] + len(media["entries"]) - 1,
            )
        )
        self.previous.setEnabled(media["start"] > 1)
        self.next.setEnabled(media["has_more"])
        self.done_button.setEnabled(True)

    def accept(self) -> None:
        self._remember()
        super().accept()
