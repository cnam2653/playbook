# Sports Analytics Backend

## Setup

1. **Create virtual environment** (Python 3.12 required):
```bash
python3.12 -m venv venv
```

2. **Activate virtual environment**:
```bash
source venv/bin/activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

4. **Create .env file** (optional - for API keys):
```bash
touch .env
```

Add your API keys to `.env`:
```
ROBOFLOW_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here
```

## Run

```bash
python app.py
```

The server will run on `http://localhost:5001`

## Directories

- `models/` - Contains trained YOLO models (best.pt)
- `uploads/` - Uploaded video files
- `outputs/` - Processed video outputs
- `analysis_results/` - JSON analysis data
- `src/` - Source utilities

## Deactivate Virtual Environment

```bash
deactivate
```
