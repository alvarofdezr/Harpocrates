
from typing import Any, Type, Optional


class SecureString:
    """
    A context manager for sensitive strings (like passwords or master keys).
    It stores the string as a mutable bytearray and attempts to explicitly
    zero out the memory block when the context exits.
    """

    def __init__(self, data: str) -> None:
        if not isinstance(data, str):
            raise TypeError("SecureString requires a string input.")
        self._buffer: bytearray = bytearray(data, "utf-8")

    def __enter__(self) -> bytearray:
        return self._buffer

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[Any],
    ) -> None:
        self.destroy()

    def get_bytes(self) -> bytes:
        """Returns a copy of the buffer as bytes. Use cautiously."""
        return bytes(self._buffer)

    def destroy(self) -> None:
        """Overwrites the internal bytearray with zeros."""
        if hasattr(self, "_buffer") and self._buffer is not None:
            # Explicitly overwrite the mutable bytearray with zeros
            for i in range(len(self._buffer)):
                self._buffer[i] = 0
            del self._buffer
