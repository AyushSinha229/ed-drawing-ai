# Sample Dataset

This folder contains synthetic engineering drawing samples for quick testing:

- `reference_bracket.png`
- `student_good.png`
- `student_tilted.png`
- `student_incomplete.png`
- `student_extra.png`

Generate or refresh the files with:

```bash
python tools/generate_sample_drawings.py
```

The variants cover the main edge cases requested for validation:

- tilted drawing
- incomplete drawing
- extra lines
- near-correct drawing

