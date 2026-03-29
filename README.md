# AI Video Architect SaaS

An enterprise-grade programmatic video generation product powered by Groq, Manim, Remotion, and Three.js.

## Architecture

- **Backend (`/backend`)**: Python FastAPI orchestrator.
  - Generates JSON schemas from prompts via Groq.
  - Converts text to speech using `gTTS`.
  - Dynamically runs `Manim` Python scripts for whiteboard & math animations.
  - Stitches visual overlays and audio using `MoviePy`.
- **Frontend (`/frontend`)**: Next.js & React Dashboard.
  - Beautiful glassmorphism UI for users to type prompts.
  - React Three Fiber & Remotion `<DynamicScene />` for rendering 3D programmatic videos directly in the browser.
  - Real-time job polling from the backend.

## Quick Start Guide

### 1. Start the Backend

Open a terminal and start the Python API:

```bash
cd backend
# 1. Ensure dependencies are installed
pip install -r requirements.txt

# 2. Add your Groq key
# Open backend/.env and ensure you have:
# GROQ_API_KEY=gsk_your_key_here

# 3. Start the server
uvicorn main:app --reload
```
*Backend runs on http://localhost:8000*

### 2. Start the Frontend

Open a second terminal:

```bash
cd frontend

# 1. Install standard dependencies (Next.js is already bootstrapping)
npm install

# 2. Install video engine dependencies
npm install remotion @remotion/player @remotion/three three @react-three/fiber @react-three/drei

# 3. Start the Next.js development server
npm run dev
```
*Frontend runs on http://localhost:3000*

## Usage
Navigate to http://localhost:3000, type a prompt like *"Explain Quantum Computing"*, select your desired format, and watch the system orchestrate LLMs, audio, and video compositing pipeline in real-time!
