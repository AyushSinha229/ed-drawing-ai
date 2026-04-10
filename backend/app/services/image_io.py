from pathlib import Path

import cv2
import fitz
import numpy as np


def load_document_as_image(file_path: Path) -> np.ndarray:
    suffix = file_path.suffix.lower()
    if suffix == ".pdf":
        return pdf_to_image(file_path)
    image = cv2.imread(str(file_path))
    if image is None:
        raise ValueError(f"Unsupported or unreadable file: {file_path}")
    return image


def pdf_to_image(file_path: Path, dpi: int = 220) -> np.ndarray:
    document = fitz.open(file_path)
    pages = []
    zoom = dpi / 72
    matrix = fitz.Matrix(zoom, zoom)
    for page in document:
        pix = page.get_pixmap(matrix=matrix, alpha=False)
        image = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
        pages.append(cv2.cvtColor(image, cv2.COLOR_RGB2BGR))
    document.close()
    if not pages:
        raise ValueError(f"PDF has no pages: {file_path}")
    return np.vstack(pages)

