from dataclasses import dataclass
from typing import Any

import cv2
import numpy as np


@dataclass
class PreprocessResult:
    original: np.ndarray
    grayscale: np.ndarray
    blurred: np.ndarray
    edges: np.ndarray
    aligned: np.ndarray
    metadata: dict[str, Any]


def preprocess_drawing(image: np.ndarray) -> PreprocessResult:
    grayscale = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(grayscale, (5, 5), 0)
    denoised = cv2.fastNlMeansDenoising(blurred, None, h=7, templateWindowSize=7, searchWindowSize=21)
    corrected = correct_perspective(image, denoised)
    aligned, rotation = auto_rotate(corrected)
    aligned_gray = cv2.cvtColor(aligned, cv2.COLOR_BGR2GRAY)
    aligned_blur = cv2.GaussianBlur(aligned_gray, (5, 5), 0)
    edges = cv2.Canny(aligned_blur, 50, 150, apertureSize=3)
    return PreprocessResult(
        original=image,
        grayscale=aligned_gray,
        blurred=aligned_blur,
        edges=edges,
        aligned=aligned,
        metadata={"rotation_applied": float(rotation), "shape": [int(aligned.shape[0]), int(aligned.shape[1])]},
    )


def correct_perspective(color: np.ndarray, grayscale: np.ndarray) -> np.ndarray:
    thresh = cv2.threshold(grayscale, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    thresh = 255 - thresh
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return color
    biggest = max(contours, key=cv2.contourArea)
    epsilon = 0.02 * cv2.arcLength(biggest, True)
    approx = cv2.approxPolyDP(biggest, epsilon, True)
    if len(approx) != 4 or cv2.contourArea(approx) < 0.35 * color.shape[0] * color.shape[1]:
        return color
    src = order_points(approx.reshape(4, 2).astype("float32"))
    width = int(max(np.linalg.norm(src[0] - src[1]), np.linalg.norm(src[2] - src[3])))
    height = int(max(np.linalg.norm(src[0] - src[3]), np.linalg.norm(src[1] - src[2])))
    dst = np.array([[0, 0], [width - 1, 0], [width - 1, height - 1], [0, height - 1]], dtype="float32")
    matrix = cv2.getPerspectiveTransform(src, dst)
    return cv2.warpPerspective(color, matrix, (width, height))


def auto_rotate(image: np.ndarray) -> tuple[np.ndarray, float]:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150)
    lines = cv2.HoughLines(edges, 1, np.pi / 180, threshold=180)
    if lines is None:
        return image, 0.0
    angles = []
    for rho_theta in lines[:40]:
        _, theta = rho_theta[0]
        angle = np.degrees(theta) - 90
        if -45 <= angle <= 45:
            angles.append(angle)
    if not angles:
        return image, 0.0
    rotation = float(np.median(angles))
    h, w = image.shape[:2]
    matrix = cv2.getRotationMatrix2D((w / 2, h / 2), rotation, 1.0)
    rotated = cv2.warpAffine(image, matrix, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    return rotated, rotation


def order_points(points: np.ndarray) -> np.ndarray:
    rect = np.zeros((4, 2), dtype="float32")
    sums = points.sum(axis=1)
    rect[0] = points[np.argmin(sums)]
    rect[2] = points[np.argmax(sums)]
    diffs = np.diff(points, axis=1)
    rect[1] = points[np.argmin(diffs)]
    rect[3] = points[np.argmax(diffs)]
    return rect
