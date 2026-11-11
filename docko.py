#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Docko — darmowa zamiana plików PDF na dokument Word (DOCX).

Działa jako zwykły skrypt oraz jako jeden plik Docko.exe (PyInstaller
--onefile --windowed). W trybie okienkowym Windows nie podłącza konsoli,
więc sys.stdout i sys.stderr są None — każde print albo zapis błędu
musi mieć wtedy bezpieczny strumień.
"""

from __future__ import annotations

import io
import os
import sys
import traceback
from pathlib import Path

NAZWA = "Docko"
WERSJA = "1.0.0"


def napraw_stdio() -> None:
    """Podmienia puste stdout/stderr, które zostawia zamrożony program okienkowy.

    Biblioteki (NumPy, OpenCV, pdf2docx) piszą ostrzeżenia na sys.stderr.
    Gdy strumień to None, kończy się to wyjątkiem AttributeError i program
    zamyka się, zanim pokaże okno.
    """
    if sys.stdout is None:
        sys.stdout = _pusty_strumien()
    if sys.stderr is None:
        sys.stderr = _pusty_strumien()


def _pusty_strumien() -> io.TextIOWrapper:
    surowy = open(os.devnull, "wb", buffering=0)
    return io.TextIOWrapper(
        surowy,
        encoding="utf-8",
        errors="replace",
        line_buffering=True,
    )


napraw_stdio()
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
# PyMuPDF 1.28 wypisuje ostrzeżenie o module fitz. Użytkownikowi nic nie daje,
# a przy pustym stdout w exe potrafi przeszkadzać. Da się to wyłączyć zmienną.
os.environ.setdefault("PYMUPDF_MESSAGE", f"path:{os.devnull}")


def _katalog_programu() -> Path:
    """Katalog, w którym leży Docko.exe, a przy uruchomieniu ze źródeł — plik skryptu.

    W paczce PyInstallera ``__file__`` wskazuje tymczasowy folder rozpakowania
    (_MEIPASS), który znika po zamknięciu programu. Log błędu ma zostać obok exe.
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def _sciezka_zasobu(nazwa: str) -> Path:
    baza = getattr(sys, "_MEIPASS", None)
    if baza:
        return Path(baza) / nazwa
    return Path(__file__).resolve().parent / nazwa


def _przygotuj_windows() -> None:
    """Osobna ikona na pasku zadań.

    Bez tego Windows traktuje zamrożony program jak proces bez tożsamości
    i pokazuje domyślną ikonę. Świadomie nie włączamy DPI awareness:
    okno ma stały rozmiar w pikselach, a skalowanie czcionek ucięłoby treść.
    """
    if sys.platform != "win32":
        return
    try:
        import ctypes

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            "PremiumZadaszenia.Docko"
        )
    except Exception:
        pass


def _ustaw_ikone(okno) -> None:
    ikona = _sciezka_zasobu("docko.ico")
    if not ikona.is_file():
        return
    try:
        okno.iconbitmap(default=str(ikona))
    except Exception:
        try:
            okno.iconbitmap(str(ikona))
        except Exception:
            pass


def _opis_bledu(blad: BaseException) -> str:
    if isinstance(blad, FileNotFoundError):
        tekst = str(blad).strip()
        return tekst or "Nie znaleziono pliku PDF."
    if isinstance(blad, PermissionError):
        return (
            "Brak dostępu do pliku. Zamknij go, jeśli jest otwarty w innym "
            "programie, i spróbuj ponownie."
        )
    if isinstance(blad, (ValueError, RuntimeError)):
        tekst = str(blad).strip()
        if tekst:
            return tekst
    szczegoly = str(blad).strip()
    if szczegoly:
        return f"Nie udało się zamienić pliku. {szczegoly}"
    return "Nie udało się zamienić pliku."


def konwertuj_pdf(sciezka_pdf: Path, sciezka_docx: Path | None = None) -> Path:
    """Zamienia jeden plik PDF na DOCX. Zwraca ścieżkę zapisanego pliku."""
    pdf = sciezka_pdf.expanduser().resolve()
    if not pdf.is_file():
        raise FileNotFoundError(f"Nie znaleziono pliku: {pdf}")
    if pdf.suffix.lower() != ".pdf":
        raise ValueError(f"To nie jest plik PDF: {pdf.name}")

    docx = sciezka_docx.expanduser().resolve() if sciezka_docx else pdf.with_suffix(".docx")
    if docx == pdf:
        raise ValueError("Ścieżka wynikowa nie może być taka sama jak źródłowa.")

    from pdf2docx import Converter

    konwerter = Converter(str(pdf))
    try:
        # Wiele procesów w pliku exe odpala kolejne kopie okna. Zostawiamy jeden.
        konwerter.convert(str(docx), multi_processing=False)
    except Exception:
        if docx.is_file() and docx.stat().st_size == 0:
            try:
                docx.unlink()
            except OSError:
                pass
        raise
    finally:
        try:
            konwerter.close()
        except Exception:
            pass

    if not docx.is_file() or docx.stat().st_size == 0:
        if docx.is_file():
            try:
                docx.unlink()
            except OSError:
                pass
        raise RuntimeError(f"Nie udało się utworzyć pliku: {docx}")
    return docx


def _podlacz_konsola(wymusz: bool) -> None:
    """W pliku exe bez konsoli podłącz stdout do okna terminala, jeśli jest.

    ``--windowed`` zostawia sys.stdout puste. Uruchomienie ``Docko.exe plik.pdf``
    z wiersza poleceń ma pokazać postęp, a dwuklik (bez argumentów) nie może
    mignąć czarnym oknem.
    """
    if sys.platform != "win32" or not getattr(sys, "frozen", False):
        return
    try:
        import ctypes

        kernel = ctypes.windll.kernel32
        ma_konsola = bool(kernel.GetConsoleWindow())
        if not ma_konsola:
            ma_konsola = bool(kernel.AttachConsole(-1))
        if not ma_konsola and wymusz:
            ma_konsola = bool(kernel.AllocConsole())
        if not ma_konsola:
            return
        kernel.SetConsoleOutputCP(65001)
        kernel.SetConsoleCP(65001)
        sys.stdout = open("CONOUT$", "w", encoding="utf-8", errors="replace", buffering=1)
        sys.stderr = open("CONOUT$", "w", encoding="utf-8", errors="replace", buffering=1)
    except Exception:
        pass


def _polecenie() -> str:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).name
    return f"python {Path(sys.argv[0]).name}"


def uruchom_cli(argumenty: list[str]) -> int:
    """Tryb wiersza poleceń: Docko.exe plik.pdf [...]"""
    bledy = 0
    for argument in argumenty:
        pdf = Path(argument)
        try:
            wynik = konwertuj_pdf(pdf)
            print(f"OK: {pdf} -> {wynik}")
        except Exception as blad:
            bledy += 1
            print(f"BŁĄD: {pdf} — {_opis_bledu(blad)}", file=sys.stderr)
    if bledy:
        print(
            f"Zakończono z błędami: {bledy} z {len(argumenty)} plików.",
            file=sys.stderr,
        )
        return 1
    return 0


def uruchom_samokontrole() -> int:
    """Sprawdza, czy zamrożony program ma tkinter i bibliotekę konwersji.

    Używane w CI. Nie otwiera okna na stałe i nie woła mainloop.
    """
    import tkinter as tk

    from pdf2docx import Converter

    if not callable(getattr(Converter, "convert", None)):
        return 1
    okno = tk.Tk()
    try:
        okno.withdraw()
        okno.update_idletasks()
        _ustaw_ikone(okno)
    finally:
        okno.destroy()
    print(f"{NAZWA} {WERSJA}: samokontrola OK")
    return 0


def _pokaz_podsumowanie(okno, udane: list[str], nieudane: list[str]) -> None:
    from tkinter import messagebox

    if udane and not nieudane:
        messagebox.showinfo(
            "Gotowe",
            "Zapisano plik DOCX obok oryginału:\n\n" + "\n".join(udane),
            parent=okno,
        )
    elif udane and nieudane:
        messagebox.showwarning(
            "Częściowy sukces",
            "Zapisano:\n"
            + "\n".join(udane)
            + "\n\nNie udało się:\n"
            + "\n".join(nieudane),
            parent=okno,
        )
    else:
        messagebox.showerror(
            "Błąd",
            "Nie udało się zamienić plików:\n\n" + "\n".join(nieudane),
            parent=okno,
        )


def uruchom_okienko() -> int:
    """Okno z przyciskiem wyboru jednego lub wielu plików PDF."""
    try:
        import tkinter as tk
        from tkinter import filedialog
    except ImportError:
        print(
            "Brak biblioteki tkinter. Zainstaluj Pythona z python.org "
            "(zaznacz opcję tcl/tk) albo użyj trybu wiersza poleceń:\n"
            f"  {_polecenie()} plik.pdf",
            file=sys.stderr,
        )
        return 1

    _przygotuj_windows()

    okno = tk.Tk()
    okno.title(NAZWA)
    okno.geometry("460x300")
    okno.resizable(False, False)
    _ustaw_ikone(okno)

    ramka = tk.Frame(okno, padx=20, pady=18)
    ramka.pack(fill="both", expand=True)

    tk.Label(
        ramka,
        text=NAZWA,
        font=("Segoe UI", 16, "bold"),
    ).pack(anchor="w")
    tk.Label(
        ramka,
        text="Zamienia plik PDF na edytowalny dokument Word (.docx).\n"
        "Wynik zostanie zapisany obok oryginalnego pliku.",
        justify="left",
        font=("Segoe UI", 10),
    ).pack(anchor="w", pady=(6, 14))

    status = tk.StringVar(value="Możesz wybrać jeden lub kilka plików naraz.")

    def odswiez(tekst: str) -> bool:
        try:
            status.set(tekst)
            okno.update_idletasks()
            okno.update()
            return True
        except tk.TclError:
            return False

    def wybierz_i_zamien() -> None:
        sciezki = filedialog.askopenfilenames(
            parent=okno,
            title="Wybierz plik PDF",
            filetypes=[("Pliki PDF", "*.pdf"), ("Wszystkie pliki", "*.*")],
        )
        if not sciezki:
            return

        przycisk.config(state="disabled")
        if not odswiez("Trwa zamiana… to może chwilę potrwać."):
            return

        udane: list[str] = []
        nieudane: list[str] = []
        liczba = len(sciezki)
        for numer, sciezka in enumerate(sciezki, start=1):
            pdf = Path(sciezka)
            if not odswiez(f"Zamieniam {numer} z {liczba}: {pdf.name}"):
                return
            try:
                wynik = konwertuj_pdf(pdf)
                udane.append(f"{pdf.name} → {wynik.name}")
            except Exception as blad:
                nieudane.append(f"{pdf.name}: {_opis_bledu(blad)}")

        try:
            przycisk.config(state="normal")
        except tk.TclError:
            return

        if udane and not nieudane:
            odswiez("Gotowe. Plik DOCX zapisano obok oryginału.")
        elif udane and nieudane:
            odswiez("Część plików udało się zamienić.")
        else:
            odswiez("Nie udało się zamienić plików.")

        try:
            _pokaz_podsumowanie(okno, udane, nieudane)
        except tk.TclError:
            return

    przycisk = tk.Button(
        ramka,
        text="Wybierz PDF",
        command=wybierz_i_zamien,
        font=("Segoe UI", 11),
        width=18,
        height=1,
    )
    przycisk.pack(anchor="w")

    tk.Label(
        ramka,
        textvariable=status,
        justify="left",
        wraplength=410,
        font=("Segoe UI", 9),
        fg="#333333",
    ).pack(anchor="w", pady=(14, 0))

    tk.Label(
        ramka,
        text="Pliki zostają na tym komputerze. Internet nie jest potrzebny.",
        justify="left",
        wraplength=410,
        font=("Segoe UI", 9),
        fg="#555555",
    ).pack(anchor="w", pady=(10, 0))

    okno.mainloop()
    return 0


def _pomoc() -> str:
    polecenie = _polecenie()
    return (
        f"{NAZWA} {WERSJA} — zamiana PDF na Word (DOCX).\n\n"
        "Okienko:\n"
        f"  {polecenie}\n\n"
        "Wiersz poleceń:\n"
        f"  {polecenie} plik.pdf [kolejny.pdf ...]\n\n"
        "Plik .docx jest zapisywany obok oryginału.\n"
        "Skanowane PDF (same obrazy) nie dadzą edytowalnego tekstu bez OCR."
    )


def main(argumenty: list[str] | None = None) -> int:
    if argumenty is None:
        argumenty = sys.argv[1:]
    if argumenty:
        _podlacz_konsola(wymusz=argumenty[0] != "--self-check")
        if argumenty[0] in {"-h", "--help", "/?"}:
            print(_pomoc())
            return 0
        if argumenty[0] == "--self-check":
            return uruchom_samokontrole()
        return uruchom_cli(argumenty)
    return uruchom_okienko()


def _zapisz_blad(tekst: str) -> Path | None:
    import tempfile

    cele = [
        _katalog_programu() / "Docko-blad.log",
        Path(tempfile.gettempdir()) / "Docko-blad.log",
    ]
    for cel in cele:
        try:
            cel.write_text(tekst, encoding="utf-8")
            return cel
        except OSError:
            continue
    return None


def _pokaz_nieoczekiwany_blad(tekst: str) -> None:
    try:
        import tkinter as tk
        from tkinter import messagebox

        okno = tk.Tk()
        okno.withdraw()
        _ustaw_ikone(okno)
        messagebox.showerror(
            NAZWA,
            "Wystąpił nieoczekiwany błąd i program musi się zamknąć.\n\n" + tekst[-1200:],
        )
        okno.destroy()
    except Exception:
        pass


if __name__ == "__main__":
    import multiprocessing

    multiprocessing.freeze_support()
    napraw_stdio()
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception:
        raport = traceback.format_exc()
        try:
            print(raport, file=sys.stderr)
        except Exception:
            pass
        plik = _zapisz_blad(raport)
        skrot = raport.strip().splitlines()[-1] if raport.strip() else "nieznany błąd"
        if plik is not None:
            skrot = f"{skrot}\n\nSzczegóły zapisano w:\n{plik}"
        _pokaz_nieoczekiwany_blad(skrot)
        sys.exit(1)
