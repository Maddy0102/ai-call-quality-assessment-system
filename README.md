# AI Call Quality Assessment System

An AI-powered call quality assessment platform that analyzes recorded conversations, generates speaker-separated transcripts, evaluates calls against configurable checklists, and provides quality reports.

## Features

- Audio file upload and call management
- Speaker-channel-based transcription
- Multilingual transcription support
- Automated checklist evaluation
- Evidence-based YES, NO, PARTIAL, and NOT_CLEAR statuses
- Human review flags
- Audio quality measurements
- Dashboard and call reports

## Technology Stack

### Backend
- Python
- FastAPI
- MongoDB
- OpenAI API
- NumPy
- SoundFile

### Frontend
- React
- Vite
- JavaScript
- CSS

## Project Structure

```text
ai-call-quality-system/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── checklists/
│   │   ├── database/
│   │   ├── schemas/
│   │   └── services/
│   ├── requirements.txt
│   └── inspect_audio.py
├── frontend/
│   ├── src/
│   │   ├── layouts/
│   │   ├── pages/
│   │   └── services/
│   ├── package.json
│   └── vite.config.js
├── .gitignore
└── README.md
```

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/Maddy0102/ai-call-quality-assessment-system.git
cd ai-call-quality-assessment-system
```

### 2. Backend setup

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Configure your environment variables using `backend/.env.example`.

### 3. Start the backend

```bash
uvicorn app.main:app --reload
```

Backend: http://localhost:8000

API documentation: http://localhost:8000/docs

### 4. Frontend setup

Open another terminal:

```bash
cd frontend
npm install
npm run dev
```

Frontend: http://localhost:5173

## Environment Variables

Create a `backend/.env` file using the variable names in `backend/.env.example`.

Never commit real API keys, database passwords, or other credentials.

## Testing

Run the backend test scripts from the backend directory as appropriate.

Frontend checks:

```bash
npm run lint
npm run build
```

## Important Notes

- Transcription and checklist evaluation are manually triggered.
- OpenAI API usage may incur charges.
- Audio quality measurements are diagnostic and are not a validated communication quality score.
- Actual call recordings and secrets should not be committed to Git.

## License

See the [LICENSE](LICENSE) file.
