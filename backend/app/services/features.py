from itertools import combinations
from typing import Any

import cv2
import numpy as np

from app.services.preprocess import PreprocessResult


def extract_features(preprocessed: PreprocessResult) -> dict[str, Any]:
    lines = detect_lines(preprocessed.edges)
    intersections = detect_intersections(lines)
    shapes = detect_shapes(preprocessed.edges)
    angles = detect_angles(intersections)
    return {
        "lines": lines,
        "angles": angles,
        "shapes": shapes,
        "intersections": intersections,
        "metadata": preprocessed.metadata,
    }


def detect_lines(edges: np.ndarray) -> list[dict[str, Any]]:
    raw_lines = cv2.HoughLinesP(
        edges,
        rho=1,
        theta=np.pi / 180,
        threshold=70,
        minLineLength=max(20, int(min(edges.shape[:2]) * 0.05)),
        maxLineGap=12,
    )
    if raw_lines is None:
        return []
    diagonal = float(np.hypot(edges.shape[0], edges.shape[1]))
    output: list[dict[str, Any]] = []
    for item in raw_lines[:, 0]:
        x1, y1, x2, y2 = [int(v) for v in item]
        length = float(np.hypot(x2 - x1, y2 - y1))
        if length < 15:
            continue
        angle = float(np.degrees(np.arctan2(y2 - y1, x2 - x1)))
        output.append(
            {
                "p1": [x1, y1],
                "p2": [x2, y2],
                "length": length,
                "norm_length": length / diagonal,
                "angle": normalize_angle(angle),
                "midpoint": [(x1 + x2) / 2, (y1 + y2) / 2],
            }
        )
    return deduplicate_lines(output)


def deduplicate_lines(lines: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deduped: list[dict[str, Any]] = []
    for line in sorted(lines, key=lambda item: item["length"], reverse=True):
        exists = False
        for accepted in deduped:
            if (
                abs(line["angle"] - accepted["angle"]) < 4
                and np.linalg.norm(np.array(line["midpoint"]) - np.array(accepted["midpoint"])) < 16
            ):
                exists = True
                break
        if not exists:
            deduped.append(line)
    return deduped


def detect_intersections(lines: list[dict[str, Any]]) -> list[dict[str, Any]]:
    intersections: list[dict[str, Any]] = []
    for left, right in combinations(lines, 2):
        point = segment_intersection(left["p1"], left["p2"], right["p1"], right["p2"])
        if point is None:
            continue
        intersections.append({"point": [float(point[0]), float(point[1])], "angles": [left["angle"], right["angle"]]})
    return intersections


def detect_angles(intersections: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for item in intersections:
        angle_a, angle_b = item["angles"]
        diff = abs(angle_a - angle_b) % 180
        if diff > 90:
            diff = 180 - diff
        output.append({"point": item["point"], "value": round(diff, 2)})
    return output


def detect_shapes(edges: np.ndarray) -> list[dict[str, Any]]:
    contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    shapes: list[dict[str, Any]] = []
    for contour in contours:
        area = cv2.contourArea(contour)
        if area < 300:
            continue
        perimeter = cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, 0.03 * perimeter, True)
        x, y, w, h = cv2.boundingRect(approx)
        shape_type = "polygon"
        if len(approx) == 3:
            shape_type = "triangle"
        elif len(approx) == 4:
            shape_type = "rectangle"
        else:
            circularity = 4 * np.pi * area / (perimeter * perimeter + 1e-6)
            if circularity > 0.7:
                shape_type = "circle"
        shapes.append(
            {
                "type": shape_type,
                "area": float(area),
                "bbox": [int(x), int(y), int(w), int(h)],
                "center": [float(x + w / 2), float(y + h / 2)],
            }
        )
    return deduplicate_shapes(shapes)


def deduplicate_shapes(shapes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for shape in shapes:
        duplicate = False
        for saved in result:
            if shape["type"] == saved["type"] and np.linalg.norm(np.array(shape["center"]) - np.array(saved["center"])) < 15:
                duplicate = True
                break
        if not duplicate:
            result.append(shape)
    return result


def segment_intersection(a1: list[int], a2: list[int], b1: list[int], b2: list[int]) -> tuple[float, float] | None:
    a1v = np.array(a1, dtype=float)
    a2v = np.array(a2, dtype=float)
    b1v = np.array(b1, dtype=float)
    b2v = np.array(b2, dtype=float)
    da = a2v - a1v
    db = b2v - b1v
    denominator = da[0] * db[1] - da[1] * db[0]
    if abs(denominator) < 1e-6:
        return None
    diff = b1v - a1v
    t = (diff[0] * db[1] - diff[1] * db[0]) / denominator
    u = (diff[0] * da[1] - diff[1] * da[0]) / denominator
    if 0 <= t <= 1 and 0 <= u <= 1:
        point = a1v + t * da
        return float(point[0]), float(point[1])
    return None


def normalize_angle(angle: float) -> float:
    angle = angle % 180
    return float(angle if angle >= 0 else angle + 180)

