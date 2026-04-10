# AI Engineering Drawing Evaluation System

Production-oriented full-stack application for evaluating engineering drawing answer sheets against a reference drawing using computer vision and geometric scoring.

## Stack

- Backend: FastAPI, SQLAlchemy, OpenCV, NumPy, Pandas
- Frontend: React, Vite, Recharts
- Storage: local filesystem with PostgreSQL-ready SQLAlchemy configuration
- Input: JPG, PNG, PDF

## Folder Structure

```text
backend/
  app/
    core/
    routers/
    services/
frontend/
  src/
sample_data/
tools/
storage/
```

## Backend Setup

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

## API Endpoints

- `POST /api/upload-reference`
- `POST /api/upload-students`
- `POST /api/process`
- `GET /api/results`
- `GET /api/results/{batch_id}`

## Processing Pipeline

1. Normalize the drawing with perspective correction, denoising, edge detection, and auto-rotation.
2. Extract lines, intersections, angles, and shape candidates from the reference and student sheets.
3. Match student features against the reference with tolerance-aware scoring.
4. Generate feedback text plus an annotated overlay image.
5. Export batch results to Excel.

## Notes

- Default database is SQLite for zero-friction local execution. Change `DATABASE_URL` in `.env` to PostgreSQL for deployment.
- PDF ingestion uses PyMuPDF, so Poppler is not required.
- Static output files are served from `storage/`.

