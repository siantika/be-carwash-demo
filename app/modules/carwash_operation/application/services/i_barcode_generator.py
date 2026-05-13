"""
Interface for generating barcodes during ticket creation.
"""

from typing import Protocol


class IBarcodeGenerator(Protocol):
    def generate(): ...
