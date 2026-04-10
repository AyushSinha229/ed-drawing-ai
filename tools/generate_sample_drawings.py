from pathlib import Path

import cv2
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "sample_data"


def blank_canvas() -> np.ndarray:
    return np.full((900, 700, 3), 255, dtype=np.uint8)


def draw_reference() -> np.ndarray:
    canvas = blank_canvas()
    cv2.rectangle(canvas, (120, 160), (540, 620), (0, 0, 0), 4)
    cv2.line(canvas, (120, 160), (330, 60), (0, 0, 0), 4)
    cv2.line(canvas, (540, 160), (330, 60), (0, 0, 0), 4)
    cv2.circle(canvas, (330, 390), 70, (0, 0, 0), 4)
    cv2.line(canvas, (120, 620), (540, 620), (0, 0, 0), 4)
    cv2.line(canvas, (120, 620), (220, 760), (0, 0, 0), 4)
    cv2.line(canvas, (540, 620), (440, 760), (0, 0, 0), 4)
    cv2.line(canvas, (220, 760), (440, 760), (0, 0, 0), 4)
    cv2.putText(canvas, "REF-01", (70, 820), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (0, 0, 0), 2, cv2.LINE_AA)
    return canvas


def draw_student_variant(kind: str) -> np.ndarray:
    canvas = blank_canvas()
    if kind == "good":
        cv2.rectangle(canvas, (130, 165), (540, 620), (0, 0, 0), 4)
        cv2.line(canvas, (130, 165), (328, 74), (0, 0, 0), 4)
        cv2.line(canvas, (540, 165), (328, 74), (0, 0, 0), 4)
        cv2.circle(canvas, (332, 398), 69, (0, 0, 0), 4)
        cv2.line(canvas, (130, 620), (540, 620), (0, 0, 0), 4)
        cv2.line(canvas, (130, 620), (224, 752), (0, 0, 0), 4)
        cv2.line(canvas, (540, 620), (438, 754), (0, 0, 0), 4)
        cv2.line(canvas, (224, 752), (438, 754), (0, 0, 0), 4)
    elif kind == "tilted":
        cv2.rectangle(canvas, (150, 180), (520, 610), (0, 0, 0), 4)
        cv2.line(canvas, (150, 180), (350, 82), (0, 0, 0), 4)
        cv2.line(canvas, (520, 180), (350, 82), (0, 0, 0), 4)
        cv2.circle(canvas, (338, 400), 58, (0, 0, 0), 4)
        cv2.line(canvas, (150, 610), (520, 610), (0, 0, 0), 4)
        cv2.line(canvas, (150, 610), (255, 730), (0, 0, 0), 4)
        cv2.line(canvas, (520, 610), (420, 740), (0, 0, 0), 4)
        matrix = cv2.getRotationMatrix2D((350, 450), 7.5, 1.0)
        canvas = cv2.warpAffine(canvas, matrix, (700, 900), borderValue=(255, 255, 255))
    elif kind == "incomplete":
        cv2.rectangle(canvas, (120, 160), (540, 620), (0, 0, 0), 4)
        cv2.line(canvas, (120, 160), (330, 60), (0, 0, 0), 4)
        cv2.line(canvas, (540, 160), (330, 60), (0, 0, 0), 4)
        cv2.line(canvas, (120, 620), (540, 620), (0, 0, 0), 4)
        cv2.line(canvas, (120, 620), (220, 760), (0, 0, 0), 4)
        cv2.line(canvas, (540, 620), (440, 760), (0, 0, 0), 4)
    elif kind == "extra":
        canvas = draw_reference()
        cv2.line(canvas, (90, 100), (600, 680), (0, 0, 0), 3)
        cv2.line(canvas, (540, 110), (80, 650), (0, 0, 0), 2)
    cv2.putText(canvas, kind.upper(), (70, 820), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (0, 0, 0), 2, cv2.LINE_AA)
    return canvas


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(OUTPUT_DIR / "reference_bracket.png"), draw_reference())
    for kind in ["good", "tilted", "incomplete", "extra"]:
        cv2.imwrite(str(OUTPUT_DIR / f"student_{kind}.png"), draw_student_variant(kind))


if __name__ == "__main__":
    main()

