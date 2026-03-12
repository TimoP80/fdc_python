"""
Background worker for FMF parsing with progress reporting
"""

from PyQt6.QtCore import QThread, pyqtSignal
from pathlib import Path
from typing import Optional

from .fmf_parser import FMFParser
from models.dialogue import Dialogue


class ParseWorker(QThread):
    """Worker thread for parsing FMF files with progress updates"""

    # Signals
    progress_updated = pyqtSignal(int, str)  # progress percentage, current operation
    parsing_finished = pyqtSignal(Dialogue)  # parsed dialogue
    parsing_error = pyqtSignal(str)  # error message

    def __init__(self, file_path: Path):
        super().__init__()
        self.file_path = file_path
        self.parser = FMFParser()
        self.parser.progress_updated.connect(self.progress_updated.emit)

    def run(self):
        """Execute parsing in background thread"""
        try:
            import logging
            logger = logging.getLogger(__name__)
            logger.debug(f"FMF background parsing thread started for file: {self.file_path}")
            # Load and parse the file
            dialogue = self.parser.load_from_file(self.file_path)
            logger.debug(f"FMF background parsing thread: Parser returned dialogue with {dialogue.nodecount} nodes")

            # Emit completion
            logger.debug("FMF background parsing thread: Emitting 100% progress and parsing finished signal")
            self.progress_updated.emit(100, "Parsing complete")
            self.parsing_finished.emit(dialogue)
            logger.debug("FMF background parsing thread: Signals emitted, thread finishing")

        except Exception as e:
            logger.error(f"FMF background parsing thread error: {e}")
            self.parsing_error.emit(str(e))