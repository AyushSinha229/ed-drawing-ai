from pathlib import Path

from app.services.comparison import compare_drawings
from app.services.features import extract_features
from app.services.feedback import generate_text_feedback, generate_visual_feedback
from app.services.image_io import load_document_as_image
from app.services.preprocess import preprocess_drawing


def evaluate_submission(
    reference_features: dict,
    submission_path: Path,
    drawing_type: str,
    feedback_filename: str,
) -> dict:
    image = load_document_as_image(submission_path)
    preprocessed = preprocess_drawing(image)
    student_features = extract_features(preprocessed)
    comparison = compare_drawings(reference_features, student_features)
    feedback_text = generate_text_feedback(comparison, drawing_type)
    feedback_image = generate_visual_feedback(preprocessed.aligned, student_features, comparison, feedback_filename)
    return {
        "score": comparison["score"],
        "feedback_text": feedback_text,
        "result_json": {
            "comparison": comparison,
            "student_features": student_features,
            "drawing_type": drawing_type,
        },
        "feedback_image_path": feedback_image,
    }


def build_reference_features(reference_path: Path) -> tuple[dict, dict]:
    image = load_document_as_image(reference_path)
    preprocessed = preprocess_drawing(image)
    features = extract_features(preprocessed)
    return features, {"aligned_shape": preprocessed.aligned.shape[:2]}

