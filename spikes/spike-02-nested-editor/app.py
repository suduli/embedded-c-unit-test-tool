import sys
import time
from PySide6.QtWidgets import QApplication, QMainWindow, QTreeView
from model import TestDataModel, CONFIG_SCHEMA
from delegates import FieldDelegate


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Spike 02 — Nested Type-Aware Editor")
        self.model = TestDataModel(CONFIG_SCHEMA)
        self.view = QTreeView()
        self.view.setModel(self.model)
        self.view.setItemDelegate(FieldDelegate(self.view))
        self.view.expandAll()
        self.setCentralWidget(self.view)
        self.resize(480, 400)

        self._edit_start = None
        self.model.dataChanged.connect(self._on_data_changed)

    def _on_data_changed(self, *_):
        if self._edit_start is not None:
            elapsed_ms = (time.perf_counter() - self._edit_start) * 1000
            print(f"[latency] commit round-trip: {elapsed_ms:.1f} ms")
            self._edit_start = None


if __name__ == "__main__":
    app = QApplication(sys.argv)
    launch_start = time.perf_counter()
    window = MainWindow()
    window.show()
    print(f"[latency] cold start to visible window: {(time.perf_counter() - launch_start) * 1000:.1f} ms")
    sys.exit(app.exec())
