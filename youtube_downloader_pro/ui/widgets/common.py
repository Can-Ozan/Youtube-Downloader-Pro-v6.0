from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from youtube_downloader_pro.i18n import tr, translate_message
from youtube_downloader_pro.ui.design import CONTROL_HEIGHT
from youtube_downloader_pro.ui.icons import icon


def label(text: str, style: str = "", wrap: bool = False, *, translate: bool = True) -> QLabel:
    widget = QLabel(tr(text) if translate else text)
    widget.setTextFormat(Qt.TextFormat.PlainText)
    widget.setObjectName(style)
    widget.setWordWrap(wrap)
    return widget


def button(text: str, callback=None, primary: bool = False, icon_name: str = "") -> QPushButton:
    widget = QPushButton(tr(text))
    widget.setMinimumHeight(CONTROL_HEIGHT)
    widget.setCursor(Qt.CursorShape.PointingHandCursor)
    widget.setAccessibleName(tr(text))
    if primary:
        widget.setObjectName("primary")
    if icon_name:
        widget.setIcon(icon(icon_name))
        widget.setIconSize(QSize(18, 18))
        widget.setProperty("icon_name", icon_name)
    if callback:
        widget.clicked.connect(callback)
    return widget


def check(text: str = "") -> QCheckBox:
    return QCheckBox(tr(text))


class ChoiceCombo(QComboBox):
    """Translated display labels with stable values, including legacy selection calls."""

    display_names = {
        "en": "English",
        "tr": "Türkçe",
        "dark": "Dark",
        "light": "Light",
        "system": "System",
        "none": "None",
        "preferred": "Preferred languages",
        "manual": "Selected languages",
        "video": "Video",
        "audio": "Audio",
        "custom": "Custom",
        "Best Available": "Best",
    }

    def addItem(self, text: str, userData=None) -> None:
        value = text if userData is None else userData
        display = self.display_names.get(
            text,
            text.upper() if text in {"mp4", "webm", "mp3", "m4a", "opus", "flac", "wav"} else text,
        )
        super().addItem(tr(display), value)

    def addItems(self, texts) -> None:
        for text in texts:
            self.addItem(text)

    def value(self) -> str:
        return super().currentText() if self.isEditable() else (self.currentData() or "")

    def currentText(self) -> str:
        # Existing callers expect engine values. Display remains Qt's translated itemText.
        return self.value()

    def findText(self, text: str, *_args) -> int:
        return self.findData(text)

    def setCurrentText(self, text: str) -> None:
        index = self.findData(text)
        if index >= 0:
            self.setCurrentIndex(index)
        elif self.isEditable():
            self.setEditText(text)


def combo(items: list[str], current: str = "") -> ChoiceCombo:
    widget = ChoiceCombo()
    widget.addItems(items)
    if current:
        widget.setCurrentText(current)
    return widget


def card() -> tuple[QFrame, QVBoxLayout]:
    frame = QFrame()
    frame.setObjectName("card")
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(16, 16, 16, 16)
    layout.setSpacing(12)
    return frame, layout


class Page(QWidget):
    def __init__(self, title: str, subtitle: str = "") -> None:
        super().__init__()
        self.setObjectName("page")
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(24, 24, 24, 16)
        self.layout.setSpacing(16)
        self.layout.addWidget(label(title, "heading"))
        if subtitle:
            self.layout.addWidget(label(subtitle, "muted", True))


class EmptyState(QWidget):
    def __init__(self, title: str, description: str, icon_name: str = "download") -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.addStretch()
        image = label("")
        image.setPixmap(icon(icon_name).pixmap(32, 32))
        image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(image)
        for text, style in ((title, "section"), (description, "muted")):
            item = label(text, style, True)
            item.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(item)
        layout.addStretch()


class UrlInput(QLineEdit):
    dropped = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.setPlaceholderText(tr("Paste a video or playlist URL"))
        self.setAccessibleName(tr("Media link"))
        self.setAcceptDrops(True)
        self.setMinimumHeight(44)
        self.setMaxLength(8192)

    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasText() or event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event) -> None:
        mime = event.mimeData()
        text = mime.urls()[0].toString() if mime.hasUrls() else mime.text()
        self.setText(text.strip())
        self.dropped.emit(text.strip())
        event.acceptProposedAction()


class Banner(QFrame):
    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("banner")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 8, 16, 8)
        row = QHBoxLayout()
        self.text = label("", wrap=True)
        self.details = label("", "muted", True)
        self.details.hide()
        self.expand = button(
            "Details", lambda: self.details.setVisible(not self.details.isVisible())
        )
        row.addWidget(self.text, 1)
        row.addWidget(self.expand)
        row.addWidget(button("Dismiss", self.hide))
        layout.addLayout(row)
        layout.addWidget(self.details)
        self.hide()

    def show_message(self, text: str, details: str = "") -> None:
        self.text.setText(translate_message(text))
        self.details.setText(translate_message(details))
        self.expand.setVisible(bool(details))
        self.details.hide()
        self.show()
