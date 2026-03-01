web: python -c "from app import app, init_db; init_db()" && gunicorn app:app --bind 0.0.0.0:$PORT
