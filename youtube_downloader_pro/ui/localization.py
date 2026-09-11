"""Translate Qt's standard controls alongside the application's own catalogs."""

from PySide6.QtCore import QLibraryInfo, QLocale, QTranslator


def install_qt_language(app, code: str) -> None:
    previous = getattr(app, "_language_translator", None)
    if previous is not None:
        app.removeTranslator(previous)
        previous.deleteLater()
    translator = QTranslator(app)
    if code == "tr":
        directory = QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)
        if not translator.load("qtbase_tr", directory):
            raise RuntimeError("Qt Turkish translations are missing")
        app.installTranslator(translator)
    app._language_translator = translator
    QLocale.setDefault(QLocale("tr_TR" if code == "tr" else "en_US"))
