# PlayBook: AI-Powered Soccer Intelligence

PlayBook is a professional sports analytics platform that transforms match footage into automated player performance metrics and tactical insights. By leveraging computer vision and generative AI, it provides a comprehensive dashboard for post-match analysis.

## 🚀 Features

* **Automated Player Tracking**: Uses YOLOv8 and ByteTrack to detect and track players, goalkeepers, referees, and the ball with over 90% accuracy.
* **Performance Metrics**: Real-time calculation of player speeds (km/h), distance covered, and ball possession percentages.
* **Team Classification**: K-Means clustering analyzes jersey colors to automatically assign players to their respective teams.
* **AI Tactical Insights**: Integration with OpenAI's GPT-4 to generate natural language summaries and answer specific tactical questions about the match.
* **Interactive Dashboard**: A modern React-based frontend featuring video overlays, statistical visualizations, and an AI assistant.
* **Camera Movement Compensation**: Optical flow estimation to ensure tracking accuracy even during rapid camera pans.

## 🛠️ Tech Stack

* **Frontend**: React, TypeScript, Vite, Tailwind CSS, Framer Motion, Lucide React.
* **Backend**: Flask, Python 3.12.
* **Machine Learning**: YOLOv8 (Ultralytics), Supervision, ByteTrack, Roboflow API, Scikit-learn (K-Means).
* **Generative AI**: OpenAI API (GPT-4).
* **Infrastructure**: AWS EC2 (distributed inference workers), Amazon RDS (data logging).

## 📦 Project Structure

```text
├── backend/
│   ├── models/                # Custom trained YOLO models (.pt files)
│   ├── src/
│   │   ├── services/          # Core logic for detection, tracking, and AI
│   │   ├── routes/            # Flask API endpoints
│   │   └── utils/             # Analytics and bounding box utilities
│   ├── advanced_tracker.py    # Main video processing pipeline
│   └── app.py                 # Flask server entry point
├── frontend/
│   ├── src/
│   │   ├── components/        # React UI components (AI Analysis, Video Input)
│   │   └── App.tsx            # Main application layout
│   └── tailwind.config.ts     # Styling configuration
└── README.md

```

## ⚙️ Installation & Setup

### Backend

1. Navigate to the `backend` directory.
2. Create a virtual environment: `python3.12 -m venv venv`.
3. Activate it: `source venv/bin/activate`.
4. Install dependencies: `pip install -r requirements.txt`.
5. Create a `.env` file and add your keys:
```text
ROBOFLOW_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here

```


6. Run the server: `python app.py` (defaults to port 5001).

### Frontend

1. Navigate to the `frontend` directory.
2. Install dependencies: `npm install`.
3. Run the development server: `npm run dev`.

## 📊 Analytics Workflow

1. **Inference**: Distributed EC2 workers process video at 10 FPS using YOLOv8.
2. **Tracking**: ByteTrack maintains consistent IDs across frames while handling occlusions.
3. **Data Extraction**: Raw coordinates are converted into team-based possession and movement stats.
4. **AI Summary**: Processed stats are stored in RDS and sent to GPT-4 to generate human-readable commentary.
