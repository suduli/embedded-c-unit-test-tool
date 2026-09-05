# app.py
import sys
import time
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget
from clang.cindex import Index


def parse_trivial_c() -> str:
    """One real libclang parse, so the bundle demonstrably needs libclang
    at runtime — not just at import time."""
    index = Index.create()
    tu = index.parse("probe.c", args=["-std=c11"], unsaved_files=[("probe.c", "int main(void) { return 0; }")])
    functions = [c.spelling for c in tu.cursor.get_children() if c.spelling == "main"]
    return f"libclang parsed OK, found: {functions}"


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Spike 03 — Packaging Probe")
        central = QWidget()
        layout = QVBoxLayout(central)
        layout.addWidget(QLabel("PySide6 + libclang, bundled by PyInstaller."))
        layout.addWidget(QLabel(parse_trivial_c()))
        self.setCentralWidget(central)
        self.resize(420, 120)


if __name__ == "__main__":
    t0 = time.perf_counter()
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    # Print, don't just show — measure.ps1 greps stdout for this line to
    # get an in-process cold-start number independent of process-launch overhead.
    print(f"COLD_START_MS={(time.perf_counter() - t0) * 1000:.1f}")
    sys.exit(app.exec())
