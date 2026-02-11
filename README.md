# PlayBook: AI-Powered Soccer Intelligence

PlayBook is a professional sports analytics platform that transforms match footage into automated player performance metrics and tactical insights. By leveraging computer vision and generative AI, it provides a comprehensive dashboard for deep post-match analysis.

## 🚀 Features

* **Automated Player Tracking**: Utilizes **YOLOv8** and **ByteTrack** to detect and track players, goalkeepers, referees, and the ball.
* **Performance Metrics**: Real-time calculation of player speeds (km/h), distance covered, and ball possession percentages.
* **Team Classification**: Employs **K-Means clustering** to analyze jersey colors and automatically assign players to their respective teams.
* **AI Tactical Insights**: Integration with the **OpenAI API (GPT-4)** to generate natural language summaries and answer specific questions about match dynamics.
* **Interactive Dashboard**: A modern **React** frontend featuring video previews, processed output playback, and an AI analysis assistant.
* **Camera Movement Compensation**: Uses Lucas-Kanade optical flow to adjust player positions and maintain tracking accuracy during camera pans.

## 🛠️ Tech Stack

* **Frontend**: React, TypeScript, Vite, Tailwind CSS, Framer Motion.
* **Backend**: Flask, Python 3.12.
* **Machine Learning**: YOLOv8 (Ultralytics), ByteTrack, Supervision.
* **Data Science**: Scikit-learn (K-Means), NumPy, Pandas.
* **Generative AI**: OpenAI API (GPT-4).
* **Infrastructure**: AWS EC2 (distributed inference) and Amazon RDS (data logging).

## 📦 Project Structure

```text
├── backend/
│   ├── src/
│   │   ├── services/          # Core detection, tracking, and AI logic
│   │   ├── routes/            # Flask API endpoints for analysis
│   │   └── utils/             # Analytics and bbox utilities
│   ├── advanced_tracker.py    # Main video processing pipeline
│   ├── team_assigner.py       # K-Means team color clustering
│   └── app.py                 # Flask server entry point
├── frontend/
│   ├── src/
│   │   ├── components/        # UI components (AI Analysis, Video Input)
│   │   └── App.tsx            # Main application dashboard
│   └── tailwind.config.ts     # Styling configuration
└── README.md

```

## ⚙️ Installation & Setup

### Backend

1. Navigate to the `backend` directory.
2. Create and activate a virtual environment:
```bash
python3.12 -m venv venv
source venv/bin/activate

```


3. Install dependencies:
```bash
pip install -r requirements.txt

```


4. Configure environment variables in a `.env` file:
```text
OPENAI_API_KEY=your_key_here

```


5. Run the server:
```bash
python app.py

```



### Frontend

1. Navigate to the `frontend` directory.
2. Install dependencies:
```bash
npm install

```


3. Run the development server:
```bash
npm run dev

```



## 📊 Analytics Workflow

1. **Inference**: Distributed EC2 workers process video at 10 FPS using a custom-trained YOLOv8 model.
2. **Tracking**: ByteTrack links detections across frames, maintaining persistent IDs even during player crossovers.
3. **Refinement**: The system interpolates missing ball positions and compensates for camera movement to ensure metric accuracy.
4. **AI Analysis**: Summarized statistics (possession, speed, passes) are sent to GPT-4 to provide contextual, data-driven insights.
