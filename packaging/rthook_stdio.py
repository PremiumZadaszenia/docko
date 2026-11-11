"""Najwcześniejsza poprawka stdout/stderr dla PyInstaller --windowed.

Runtime hook uruchamia się przed skryptem. W programie bez konsoli oba
strumienie są None i pierwszy zapis (nawet ostrzeżenie biblioteki) wywala proces.
"""

import io
import os
import sys


def _pusty() -> io.TextIOWrapper:
    return io.TextIOWrapper(
        open(os.devnull, "wb", buffering=0),
        encoding="utf-8",
        errors="replace",
        line_buffering=True,
    )


if sys.stdout is None:
    sys.stdout = _pusty()
if sys.stderr is None:
    sys.stderr = _pusty()

# PyInstaller czasem kładzie DLL obok pliku exe w katalogu rozpakowania,
# a moduł .pyd szuka ich u siebie. Bez tego import pymupdf albo cv2 pada.
if sys.platform == "win32" and getattr(sys, "frozen", False):
    baza = getattr(sys, "_MEIPASS", None)
    if baza:
        os.environ["PATH"] = baza + os.pathsep + os.environ.get("PATH", "")
        if hasattr(os, "add_dll_directory"):
            os.add_dll_directory(baza)
            for podkatalog in ("pymupdf", "cv2", "numpy.libs"):
                sciezka = os.path.join(baza, podkatalog)
                if os.path.isdir(sciezka):
                    os.add_dll_directory(sciezka)
