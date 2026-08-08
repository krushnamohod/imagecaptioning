# AI-Powered Image Captioning and Content Generation System

> **B.Tech Final Year Engineering Project**  
> A full-stack AI platform combining Computer Vision (Salesforce BLIP) and Large Language Models (Qwen2.5-3B via Ollama) to convert images into context-aware captions, social media posts, multi-language descriptions, and overlay-captioned visuals.

---

## 📌 Project Overview

This project implements an end-to-end multimodal content generation system. Users can upload an image, which is first processed by **Salesforce BLIP** (a state-of-the-art Vision-Language model running locally via PyTorch/Transformers) to extract a raw visual description. This description is then passed to **Qwen2.5-3B-Instruct** (served via Ollama's local API) to synthesize rich, context-aware content adapted for target platforms (Instagram, LinkedIn, X, Facebook), writing styles (Creative, Marketing, Humorous, etc.), and languages (English, Hindi, Marathi).

Finally, the generated text can be dynamically overlaid onto the original image using Pillow image processing to produce a shareable captioned output image.

---

## 🏗️ System Architecture

```
                       +---------------------------------------+
                       |    Vite + React Frontend (UI)         |
                       | - Image Upload & Interactive Preview   |
                       | - Style, Language & Platform Controls |
                       +-------------------+-------------------+
                                           |
                                           | HTTP REST API
                                           v
                       +---------------------------------------+
                       |    FastAPI Python Backend             |
                       | - Async Route Controllers             |
                       | - Input Validation & Pydantic Models  |
                       +---------+-------------------+---------+
                                 |                   |
            +--------------------+                   +--------------------+
            |                                                             |
            v                                                             v
+-----------------------+                                     +-----------------------+
|  BLIP Vision Model    |                                     | Ollama Service API    |
| - Salesforce BLIP Base|                                     | - Qwen2.5-3B-Instruct |
| - PyTorch Engine      |                                     | - Prompt Engineering  |
+-----------+-----------+                                     +-----------+-----------+
            |                                                             |
            | Visual Description                                          | Rewritten Caption
            +----------------------------------+--------------------------+
                                               |
                                               v
                                   +-----------------------+
                                   | Pillow Image Service  |
                                   | (Caption Text Overlay)|
                                   +-----------+-----------+
                                               |
                                               v
                                   +-----------------------+
                                   | SQLite Database       |
                                   | (History & Metadata)  |
                                   +-----------------------+
```

---

## 🛠️ Technology Stack

### Frontend
- **Framework**: React.js (v18) initialized with Vite
- **Styling**: Modern Vanilla CSS with CSS custom properties (Variables), dark mode support, glassmorphism, and responsive layouts
- **HTTP Client**: Axios

### Backend
- **Framework**: FastAPI (Python 3.10+)
- **Server**: Uvicorn (ASGI)
- **Validation**: Pydantic v2
- **Image Processing**: Pillow (PIL), OpenCV

### AI / ML Core
- **Vision-Language Model**: `Salesforce/blip-image-captioning-base` (PyTorch + Hugging Face Transformers)
- **Local LLM Engine**: Ollama running `qwen2.5:3b` (Qwen2.5-3B-Instruct)

### Database
- **Storage**: SQLite3 (persisting caption history, parameters, and generated image paths)

### Future Fine-Tuning Module (`training/`)
- **Frameworks**: Unsloth, Hugging Face PEFT (LoRA/QLoRA)

---

## 📁 Repository Structure

```text
AI-Image-Captioning/
│
├── frontend/                  # React + Vite Frontend
│   ├── src/
│   │   ├── components/        # Reusable UI components
│   │   ├── pages/             # Main page layouts
│   │   ├── services/          # API integration layer (Axios)
│   │   ├── App.jsx            # Main app container
│   │   ├── main.jsx           # React entry point
│   │   └── index.css          # Design system & styles
│   ├── package.json
│   └── vite.config.js
│
├── backend/                   # FastAPI Backend
│   ├── app/
│   │   ├── main.py            # FastAPI entry point
│   │   ├── config.py          # App configuration & constants
│   │   ├── api/               # Router endpoints (caption, content, image, history)
│   │   ├── services/          # Core AI & Image services (blip, ollama, image)
│   │   ├── models/            # Schemas & SQLite Database models
│   │   └── utils/             # Helper utilities (file handling, image formatting)
│   ├── uploads/               # Temporary uploaded user images
│   ├── outputs/               # Rendered captioned images
│   ├── requirements.txt       # Python dependencies
│   └── .env                   # Environment config
│
├── training/                  # LLM Fine-Tuning module (Unsloth / LoRA)
│   ├── dataset/               # Custom dataset storage
│   ├── scripts/               # Training scripts
│   └── notebooks/             # Jupyter notebooks for experimentation
│
├── data/                      # Local SQLite database file storage
├── README.md                  # Project documentation
└── .gitignore                 # Version control exclusion rules
```

---

## ⚡ Setup & Installation

### 1. Prerequisites
- **Python**: 3.10 or higher
- **Node.js**: v18.0 or higher
- **Ollama**: Installed locally ([https://ollama.com](https://ollama.com))

### 2. Ollama Local Model Setup
Pull the Qwen 2.5 3B Instruct model using Ollama:
```bash
ollama pull qwen2.5:3b
```
Ensure the Ollama service is running in the background (default port `11434`).

### 3. Backend Setup
1. Open a terminal and navigate to the backend folder:
   ```bash
   cd backend
   ```
2. Activate your virtual environment (e.g. the existing `dev` environment or create one):
   ```bash
   # On Windows (PowerShell):
   ..\dev\Scripts\Activate.ps1
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the FastAPI development server:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

### 4. Frontend Setup
1. Open a second terminal and navigate to the frontend folder:
   ```bash
   cd frontend
   ```
2. Install Node dependencies:
   ```bash
   npm install
   ```
3. Start the Vite dev server:
   ```bash
   npm run dev
   ```
4. Access the web application at `http://localhost:3000`.

---

## ⚙️ Development Strategy & Roadmap

The development of this project follows a 15-phase incremental workflow:

- **Phase 1**: Project Structure & Configuration Setup *(Current)*
- **Phase 2**: FastAPI Server Skeleton & Health Endpoint
- **Phase 3**: Dependency Installation & Validation
- **Phase 4**: BLIP Vision Service Implementation
- **Phase 5**: Image Captioning API Endpoint (`/api/caption`)
- **Phase 6**: API Testing via Swagger UI (`http://localhost:8000/docs`)
- **Phase 7**: Ollama Integration Service (`ollama_service.py`)
- **Phase 8**: Content Generation API Endpoint (`/api/generate`)
- **Phase 9**: Combined End-to-End Pipeline Endpoint (`/api/generate-from-image`)
- **Phase 10**: React Frontend Components & State Integration
- **Phase 11**: Image Caption Overlay Service (Pillow)
- **Phase 12**: History & Persistence Engine (SQLite)
- **Phase 13**: Modern UI Polish & Micro-animations
- **Phase 14**: System Verification & End-to-End Testing
- **Phase 15**: Model Fine-Tuning Pipeline Setup (`training/`)

---

## 📄 License & Academic Credit
This project is developed for B.Tech Final Year Academic Dissertation & Capstone Demonstration. All rights reserved.
