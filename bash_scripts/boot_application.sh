cd /home/domiroem/projects/personal/btc_instead
uvicorn app.api.main:app --reload --host 0.0.0.0 --port 8000

cd frontend
python -m http.server 3000