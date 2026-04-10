from pathlib import Path
from typing import Any

import cv2
import numpy as np

from app.config import settings


def generate_visual_feedback(
    aligned_image: np.ndarray,
    student_features: dict[str, Any],
    comparison: dict[str, Any],
    filename: str,
) -> Path:
    canvas = aligned_image.copy()
    matched_students = {match["student_index"] for match in comparison.get("line_matches", [])}
    for index, line in enumerate(student_features.get("lines", [])):
        p1 = tuple(map(int, line["p1"]))
        p2 = tuple(map(int, line["p2"]))
        color = (0, 180, 0) if index in matched_students else (0, 0, 255)
        thickness = 2 if index in matched_students else 3
        cv2.line(canvas, p1, p2, color, thickness)

    heatmap = create_heatmap(aligned_image.shape[:2], student_features)
    overlay = cv2.addWeighted(canvas, 0.82, heatmap, 0.18, 0)
    output_path = settings.storage_dir / "visual_feedback" / filename
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(output_path), overlay)
    return output_path


def create_heatmap(shape: tuple[int, int], student_features: dict[str, Any]) -> np.ndarray:
    height, width = shape
    intensity = np.zeros((height, width), dtype=np.uint8)
    for line in student_features.get("lines", []):
        cv2.line(
            intensity,
            tuple(map(int, line["p1"])),
            tuple(map(int, line["p2"])),
            color=min(255, int(100 + line["length"] * 0.08)),
            thickness=6,
        )
    return cv2.applyColorMap(intensity, cv2.COLORMAP_JET)


def generate_text_feedback(comparison: dict[str, Any], drawing_type: str) -> str:
    score = comparison["score"]
    summary = comparison["summary"]
    component_scores = comparison["component_scores"]
    issues = comparison.get("errors", [])
    lines = [
        f"Drawing type: {drawing_type}",
        f"Overall score: {score}/100",
        summary,
        (
            "Component breakdown: "
            f"angles {component_scores['angles']:.1f}, "
            f"proportions {component_scores['proportions']:.1f}, "
            f"alignment {component_scores['alignment']:.1f}, "
            f"completeness {component_scores['completeness']:.1f}."
        ),
    ]
    if issues:
        lines.append("Key corrections:")
        lines.extend(f"- {issue}" for issue in issues[:6])
    else:
        lines.append("No significant geometric issues were detected.")
    return "\n".join(lines)

