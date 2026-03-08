blog-video-ai
├── app
│   ├── api/routes/      # FastAPI/Flask endpoints (POST /video)
│   ├── schemas/         # Data validation (Pydantic models)
│   ├── services/        # Logic: Scraping, Scripting, Audio, Video
│   ├── workflows/       # Handoff between services (The "Glue")
│   └── utils/           # HTML cleaning and text processing
├── assets/              # Fonts, Background Music, and JSON templates
├── storage/             # Final MP4s and intermediate assets
└── run.py               # Entry point for the application
