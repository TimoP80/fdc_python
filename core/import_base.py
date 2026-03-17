"""
Import Infrastructure Base Module

Provides common infrastructure for importing files including:
- Transaction support for atomic imports
- Progress reporting
- Error logging with meaningful messages
- Validation framework
"""

import logging
import traceback
from typing import List, Optional, Dict, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import threading

logger = logging.getLogger(__name__)


class ImportLevel(Enum):
    """Severity levels for import issues"""
    INFO = 1
    WARNING = 2
    ERROR = 3
    CRITICAL = 4


@dataclass
class ImportIssue:
    """Represents an issue found during import"""
    level: ImportLevel
    message: str
    line_number: Optional[int] = None
    column: Optional[int] = None
    context: str = ""  # Additional context for debugging
    recoverable: bool = True  # Whether the import can continue
    
    def __str__(self) -> str:
        location = ""
        if self.line_number is not None:
            location = f"Line {self.line_number}"
            if self.column is not None:
                location += f", Column {self.column}"
            location += ": "
        return f"{location}{self.message}"


@dataclass
class ImportResult:
    """Result of an import operation"""
    success: bool
    warnings: List[ImportIssue] = field(default_factory=list)
    errors: List[ImportIssue] = field(default_factory=list)
    imported_count: int = 0
    skipped_count: int = 0
    total_count: int = 0
    
    @property
    def has_warnings(self) -> bool:
        return len(self.warnings) > 0
    
    @property
    def has_errors(self) -> bool:
        return len(self.errors) > 0
    
    @property
    def is_recoverable(self) -> bool:
        """Check if import was recoverable despite errors"""
        return all(error.recoverable for error in self.errors) and len(self.errors) == 0
    
    def add_warning(self, message: str, line_number: Optional[int] = None, 
                    column: Optional[int] = None, context: str = ""):
        """Add a warning to the result"""
        self.warnings.append(ImportIssue(
            level=ImportLevel.WARNING,
            message=message,
            line_number=line_number,
            column=column,
            context=context
        ))
        logger.warning(f"Import warning: {message} (line {line_number})")
    
    def add_error(self, message: str, line_number: Optional[int] = None,
                  column: Optional[int] = None, recoverable: bool = True,
                  context: str = ""):
        """Add an error to the result"""
        self.errors.append(ImportIssue(
            level=ImportLevel.ERROR,
            message=message,
            line_number=line_number,
            column=column,
            recoverable=recoverable,
            context=context
        ))
        logger.error(f"Import error: {message} (line {line_number})")
    
    def add_critical_error(self, message: str, recoverable: bool = False):
        """Add a critical error that cannot be recovered from"""
        self.errors.append(ImportIssue(
            level=ImportLevel.CRITICAL,
            message=message,
            recoverable=recoverable
        ))
        logger.critical(f"Import critical error: {message}")


@dataclass
class ImportProgress:
    """Progress information for import operations"""
    current: int = 0
    total: int = 0
    current_file: str = ""
    current_operation: str = ""
    percentage: float = 0.0
    
    def update(self, current: int, total: int, current_file: str = "",
               current_operation: str = ""):
        """Update progress"""
        self.current = current
        self.total = total
        self.current_file = current_file
        self.current_operation = current_operation
        if total > 0:
            self.percentage = (current / total) * 100
        else:
            self.percentage = 0.0
    
    def increment(self, current_file: str = "", current_operation: str = ""):
        """Increment progress by 1"""
        self.current = min(self.current + 1, self.total)
        self.current_file = current_file
        self.current_operation = current_operation
        if self.total > 0:
            self.percentage = (self.current / self.total) * 100


class ImportTransaction:
    """
    Transaction support for atomic imports.
    
    Allows grouping multiple imports together with the ability to
    rollback if any import fails.
    """
    
    def __init__(self, name: str = "import"):
        self.name = name
        self._operations: List[Callable[[], bool]] = []
        self._rollback_handlers: List[Callable[[], None]] = []
        self._committed = False
        self._rolled_back = False
        self._completed_operations: List[Any] = []
        
    def add_operation(self, operation: Callable[[], bool], 
                      rollback_handler: Optional[Callable[[], None]] = None):
        """
        Add an operation to the transaction.
        
        Args:
            operation: Function that performs the operation and returns True on success
            rollback_handler: Optional function to call to rollback the operation
        """
        if self._committed:
            raise RuntimeError("Cannot add operations to a committed transaction")
        if self._rolled_back:
            raise RuntimeError("Cannot add operations to a rolled-back transaction")
        
        self._operations.append(operation)
        if rollback_handler:
            self._rollback_handlers.append(rollback_handler)
        else:
            self._rollback_handlers.append(lambda: None)  # No-op default
    
    def execute(self) -> ImportResult:
        """
        Execute all operations in the transaction.
        
        Returns:
            ImportResult with success status and any errors/warnings
        """
        result = ImportResult(success=True)
        
        for i, (operation, rollback) in enumerate(zip(self._operations, self._rollback_handlers)):
            try:
                if not operation():
                    # Operation failed, rollback and return
                    result.success = False
                    result.add_error(f"Transaction '{self.name}' failed at operation {i + 1}")
                    self._rollback_all()
                    return result
                
                # Operation succeeded, add rollback handler for potential future rollback
                self._completed_operations.append((operation, rollback))
                
            except Exception as e:
                result.success = False
                result.add_error(f"Transaction '{self.name}' failed with exception: {str(e)}")
                logger.exception(f"Exception during transaction '{self.name}' operation {i + 1}")
                self._rollback_all()
                return result
        
        self._committed = True
        result.success = True
        return result
    
    def _rollback_all(self):
        """Rollback all completed operations"""
        logger.info(f"Rolling back transaction '{self.name}'")
        self._rolled_back = True
        
        # Rollback in reverse order
        for operation, rollback in reversed(self._completed_operations):
            try:
                rollback()
                logger.debug(f"Rolled back operation")
            except Exception as e:
                logger.error(f"Error during rollback: {e}")
        
        self._completed_operations.clear()
    
    def is_committed(self) -> bool:
        return self._committed
    
    def is_rolled_back(self) -> bool:
        return self._rolled_back


class ImportProgressReporter:
    """Thread-safe progress reporter for import operations"""
    
    def __init__(self):
        self._lock = threading.Lock()
        self._progress = ImportProgress()
        self._subscribers: List[Callable[[ImportProgress], None]] = []
    
    def subscribe(self, callback: Callable[[ImportProgress], None]):
        """Subscribe to progress updates"""
        with self._lock:
            self._subscribers.append(callback)
    
    def unsubscribe(self, callback: Callable[[ImportProgress], None]):
        """Unsubscribe from progress updates"""
        with self._lock:
            if callback in self._subscribers:
                self._subscribers.remove(callback)
    
    def update(self, current: int, total: int, current_file: str = "",
               current_operation: str = ""):
        """Update progress and notify subscribers"""
        with self._lock:
            self._progress.update(current, total, current_file, current_operation)
            progress_copy = ImportProgress(
                current=self._progress.current,
                total=self._progress.total,
                current_file=self._progress.current_file,
                current_operation=self._progress.current_operation,
                percentage=self._progress.percentage
            )
        
        # Notify subscribers outside the lock
        for callback in self._subscribers:
            try:
                callback(progress_copy)
            except Exception as e:
                logger.error(f"Error in progress subscriber: {e}")
    
    def get_progress(self) -> ImportProgress:
        """Get current progress"""
        with self._lock:
            return ImportProgress(
                current=self._progress.current,
                total=self._progress.total,
                current_file=self._progress.current_file,
                current_operation=self._progress.current_operation,
                percentage=self._progress.percentage
            )


class ImportValidator:
    """Base class for import validation"""
    
    def __init__(self):
        self.errors: List[ImportIssue] = []
        self.warnings: List[ImportIssue] = []
    
    def validate(self) -> bool:
        """Run all validation checks. Returns True if validation passes."""
        raise NotImplementedError("Subclasses must implement validate()")
    
    def add_validation_error(self, message: str, line_number: Optional[int] = None,
                            column: Optional[int] = None):
        """Add a validation error"""
        self.errors.append(ImportIssue(
            level=ImportLevel.ERROR,
            message=message,
            line_number=line_number,
            column=column,
            recoverable=True
        ))
    
    def add_validation_warning(self, message: str, line_number: Optional[int] = None,
                              column: Optional[int] = None):
        """Add a validation warning"""
        self.warnings.append(ImportIssue(
            level=ImportLevel.WARNING,
            message=message,
            line_number=line_number,
            column=column
        ))
    
    def clear(self):
        """Clear all errors and warnings"""
        self.errors.clear()
        self.warnings.clear()


def log_import_exception(logger_instance: logging.Logger, context: str = "",
                        include_traceback: bool = True) -> str:
    """
    Log an exception that occurred during import.
    
    Returns:
        The error message that was logged
    """
    exc_type, exc_value, exc_traceback = sys.exc_info()
    
    error_msg = f"Import error"
    if context:
        error_msg += f" during {context}"
    error_msg += f": {exc_value}"
    
    if include_traceback:
        logger_instance.exception(error_msg)
    else:
        logger_instance.error(error_msg)
    
    return error_msg


import sys
