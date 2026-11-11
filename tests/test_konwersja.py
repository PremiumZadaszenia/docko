# -*- coding: utf-8 -*-
"""Testy zamiany PDF na DOCX i poprawek pod program bez konsoli."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import docko  # noqa: E402


class TestDocko(unittest.TestCase):
    def test_brak_pliku(self) -> None:
        with self.assertRaises(FileNotFoundError):
            docko.konwertuj_pdf(Path("nie-ma-takiego-pliku.pdf"))

    def test_to_nie_pdf(self) -> None:
        with tempfile.TemporaryDirectory() as katalog:
            plik = Path(katalog) / "notatka.txt"
            plik.write_text("cześć", encoding="utf-8")
            with self.assertRaises(ValueError):
                docko.konwertuj_pdf(plik)

    def test_puste_stdout_i_stderr_nie_wywalaja_print(self) -> None:
        stary_out, stary_err = sys.stdout, sys.stderr
        try:
            sys.stdout = None
            sys.stderr = None
            docko.napraw_stdio()
            print("ok")
            print("błąd", file=sys.stderr)
            self.assertIsNotNone(sys.stdout)
            self.assertIsNotNone(sys.stderr)
        finally:
            for strumien in (sys.stdout, sys.stderr):
                if strumien is not None and strumien not in (stary_out, stary_err):
                    strumien.close()
            sys.stdout = stary_out
            sys.stderr = stary_err

    def test_pomoc(self) -> None:
        import io
        from contextlib import redirect_stdout

        bufor = io.StringIO()
        with redirect_stdout(bufor):
            self.assertEqual(docko.main(["--help"]), 0)
        tekst = bufor.getvalue()
        self.assertIn("Docko", tekst)
        self.assertIn(".docx", tekst)

    def test_opis_bledu_po_polsku(self) -> None:
        self.assertIn("Brak dostępu", docko._opis_bledu(PermissionError(13, "Permission denied")))
        self.assertEqual(
            "Nie udało się zamienić pliku.",
            docko._opis_bledu(RuntimeError("")),
        )

    def test_okno_nazywa_sie_docko(self) -> None:
        import tkinter as tk

        try:
            sonda = tk.Tk()
        except tk.TclError as blad:
            self.skipTest(f"brak ekranu: {blad}")
        sonda.withdraw()
        sonda.destroy()

        zebrane: dict[str, object] = {}

        def zatrzymaj(okno: tk.Tk) -> None:
            teksty: list[str] = []

            def zbierz(widget: tk.Misc) -> None:
                if isinstance(widget, (tk.Label, tk.Button)):
                    teksty.append(str(widget.cget("text")))
                for dziecko in widget.winfo_children():
                    zbierz(dziecko)

            zbierz(okno)
            zebrane["tytul"] = okno.title()
            zebrane["teksty"] = teksty
            okno.destroy()

        oryginal = tk.Tk.mainloop
        tk.Tk.mainloop = zatrzymaj  # type: ignore[method-assign]
        try:
            self.assertEqual(docko.uruchom_okienko(), 0)
        finally:
            tk.Tk.mainloop = oryginal  # type: ignore[method-assign]

        self.assertEqual(zebrane["tytul"], "Docko")
        teksty = zebrane["teksty"]
        assert isinstance(teksty, list)
        self.assertIn("Wybierz PDF", teksty)
        self.assertTrue(any("docx" in tekst for tekst in teksty))

    def test_prosty_pdf_daje_docx(self) -> None:
        import fitz

        with tempfile.TemporaryDirectory() as katalog:
            pdf = Path(katalog) / "Zażółć gęślą.pdf"
            dokument = fitz.open()
            try:
                strona = dokument.new_page()
                strona.insert_text((72, 72), "Docko")
                dokument.save(pdf)
            finally:
                dokument.close()

            wynik = docko.konwertuj_pdf(pdf)
            self.assertEqual(wynik.suffix, ".docx")
            self.assertEqual(wynik.name, pdf.with_suffix(".docx").name)
            # Windows potrafi zwrócić tę samą teczkę raz jako długą ścieżkę,
            # a raz jako skróconą (RUNNER~1). samefile porównuje sam folder.
            self.assertTrue(wynik.parent.samefile(pdf.parent))
            self.assertTrue(wynik.is_file())
            self.assertGreater(wynik.stat().st_size, 0)
            self.assertEqual(wynik.read_bytes()[:2], b"PK")


if __name__ == "__main__":
    unittest.main()
