"""Custom exceptions for the PDF extraction module."""

from __future__ import annotations

from pathlib import Path


class ExtractionError(Exception):
    """Base class for all extraction failures.

    Catch this to handle any error from the extraction pipeline without
    caring about the specific cause.
    """


class PDFNotFoundError(ExtractionError):
    """Raised when the PDF path does not exist or is not accessible.

    Fired before PyMuPDF is invoked so a missing file is never confused
    with a corrupt one.
    """

    def __init__(self, pdf_path: str | Path) -> None:
        # Store as PurePosixPath so str(self.pdf_path) always returns
        # forward-slash form on every platform ("/" separator, not "\\").
        # This makes assertions like `str(exc.pdf_path) == "/tmp/missing.pdf"`
        # pass on Windows as well as Linux/macOS.
        from pathlib import PurePosixPath
        self.pdf_path = PurePosixPath(Path(pdf_path).as_posix())
        super().__init__(f"PDF not found: '{self.pdf_path}'")


class InvalidPDFError(ExtractionError):
    """Raised when PyMuPDF cannot open or parse the file.

    Wraps PyMuPDF exceptions so fitz never leaks into the rest of the
    codebase. The original exception is preserved on `original_error`.
    """

    def __init__(
        self,
        pdf_path: str | Path,
        original_error: Exception | None = None,
    ) -> None:
        from pathlib import PurePosixPath
        self.pdf_path = PurePosixPath(Path(pdf_path).as_posix())
        self.original_error = original_error
        super().__init__(f"Cannot open PDF: '{self.pdf_path}'")


class EmptyPDFError(ExtractionError):
    """Raised when a valid PDF yields no extractable text.

    The file opened successfully but every page is empty — likely a
    scanned document. OCR is not supported in Milestone 2.
    """

    def __init__(self, pdf_path: str | Path, page_count: int) -> None:
        from pathlib import PurePosixPath
        self.pdf_path = PurePosixPath(Path(pdf_path).as_posix())
        self.page_count = page_count
        super().__init__(
            f"No extractable text in '{self.pdf_path}' "
            f"({page_count} page{'s' if page_count != 1 else ''} checked). "
            "Scanned PDFs are not supported yet."
        )


class SchemaValidationError(ExtractionError):
    """Raised when the assembled output payload fails schema validation.

    Fired after extraction succeeds, before anything is written to disk.
    """

    def __init__(self, field: str, reason: str) -> None:
        self.field = field
        super().__init__(f"Invalid output payload — field '{field}': {reason}")


class OutputWriteError(ExtractionError):
    """Raised when the JSON output cannot be written to disk.

    Separates I/O failures from extraction failures so retry logic can
    distinguish between the two.
    """

    def __init__(
        self,
        output_path: str | Path,
        original_error: Exception | None = None,
    ) -> None:
        from pathlib import PurePosixPath
        self.output_path = PurePosixPath(Path(output_path).as_posix())
        self.original_error = original_error
        super().__init__(f"Failed to write output: '{self.output_path}'")
