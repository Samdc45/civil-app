web: python -c "from app import app, init_db, seed_admin; init_db(); seed_admin()" && gunicorn app:app --bind 0.0.0.0:$PORT --timeout 120
