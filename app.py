
import os, json, sqlite3, hashlib, secrets, re
from datetime import datetime
from functools import wraps
from flask import (
    Flask, render_template, request, redirect,
    url_for, session, jsonify, send_file, abort
)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'civilapp-2026')
DB = os.path.join(os.path.dirname(__file__), 'lms.db')
COURSES_DIR = os.path.join(os.path.dirname(__file__), 'courses')

# ─────────────────────────────────────────────────────────────
# DATABASE
# ─────────────────────────────────────────────────────────────
def get_db():
    db = sqlite3.connect(DB)
    db.row_factory = sqlite3.Row
    return db

def init_db():
    db = get_db()
    db.executescript('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now')),
            is_admin INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS enrollments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            course_id TEXT NOT NULL,
            tier TEXT DEFAULT 'intro',
            enrolled_at TEXT DEFAULT (datetime('now')),
            gumroad_sale_id TEXT,
            UNIQUE(student_id, course_id)
        );
        CREATE TABLE IF NOT EXISTS progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            course_id TEXT NOT NULL,
            module_id INTEGER NOT NULL,
            lesson_idx INTEGER NOT NULL,
            completed INTEGER DEFAULT 0,
            score INTEGER,
            completed_at TEXT,
            UNIQUE(student_id, course_id, module_id, lesson_idx)
        );
        CREATE TABLE IF NOT EXISTS certificates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            course_id TEXT NOT NULL,
            issued_at TEXT DEFAULT (datetime('now')),
            cert_code TEXT UNIQUE NOT NULL,
            score INTEGER
        );
    '''
    )
    db.commit()
    db.close()

# ─────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────
def hash_pw(pw): return hashlib.sha256(pw.encode()).hexdigest()

def load_courses():
    courses = []
    for f in sorted(os.listdir(COURSES_DIR)):
        if f.endswith('.json'):
            with open(os.path.join(COURSES_DIR, f)) as fh:
                courses.append(json.load(fh))
    return courses

def load_course(course_id):
    for c in load_courses():
        if c['id'] == course_id:
            return c
    return None

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'student_id' not in session:
            return redirect(url_for('login', next=request.path))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('is_admin'):
            abort(403)
        return f(*args, **kwargs)
    return decorated

def get_student_progress(student_id, course_id):
    db = get_db()
    rows = db.execute(
        'SELECT * FROM progress WHERE student_id=? AND course_id=?',
        (student_id, course_id)
    ).fetchall()
    db.close()
    completed = set()
    scores = {}
    for r in rows:
        if r['completed']:
            completed.add((r['module_id'], r['lesson_idx']))
            if r['score'] is not None:
                scores[(r['module_id'], r['lesson_idx'])] = r['score']
    return completed, scores

# ─────────────────────────────────────────────────────────────
# ROUTES — Public
# ─────────────────────────────────────────────────────────────
@app.route('/')
def index():
    courses = load_courses()
    db = get_db()
    enrolled_ids = []
    if 'student_id' in session:
        rows = db.execute(
            'SELECT course_id FROM enrollments WHERE student_id=?',
            (session['student_id'],)
        ).fetchall()
        enrolled_ids = [r['course_id'] for r in rows]
    db.close()
    return render_template('index.html', courses=courses, enrolled_ids=enrolled_ids)

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        email = request.form['email'].lower().strip()
        name  = request.form['name'].strip()
        pw    = request.form['password']
        if len(pw) < 6:
            return render_template('auth.html', mode='register', error='Password must be 6+ characters')
        db = get_db()
        try:
            db.execute(
                'INSERT INTO students (email,name,password_hash) VALUES (?,?,?)',
                (email, name, hash_pw(pw))
            )
            db.commit()
            row = db.execute('SELECT * FROM students WHERE email=?', (email,)).fetchone()
            session['student_id'] = row['id']
            session['student_name'] = row['name']
            session['is_admin'] = bool(row['is_admin'])
            db.close()
            return redirect(url_for('dashboard'))
        except sqlite3.IntegrityError:
            db.close()
            return render_template('auth.html', mode='register', error='Email already registered')
    return render_template('auth.html', mode='register')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form['email'].lower().strip()
        pw    = request.form['password']
        db = get_db()
        row = db.execute(
            'SELECT * FROM students WHERE email=? AND password_hash=?',
            (email, hash_pw(pw))
        ).fetchone()
        db.close()
        if row:
            session['student_id']   = row['id']
            session['student_name'] = row['name']
            session['is_admin']     = bool(row['is_admin'])
            next_url = request.args.get('next', url_for('dashboard'))
            return redirect(next_url)
        return render_template('auth.html', mode='login', error='Invalid email or password')
    return render_template('auth.html', mode='login')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# ─────────────────────────────────────────────────────────────
# ROUTES — Student
# ─────────────────────────────────────────────────────────────
@app.route('/dashboard')
@login_required
def dashboard():
    db = get_db()
    enrols = db.execute(
        'SELECT * FROM enrollments WHERE student_id=?',
        (session['student_id'],)
    ).fetchall()
    certs = db.execute(
        'SELECT * FROM certificates WHERE student_id=?',
        (session['student_id'],)
    ).fetchall()
    db.close()
    courses = {c['id']: c for c in load_courses()}
    enrolled_courses = []
    for e in enrols:
        c = courses.get(e['course_id'])
        if c:
            completed, _ = get_student_progress(session['student_id'], c['id'])
            total = sum(len(m['lessons']) for m in c['modules'])
            pct = int(len(completed) / total * 100) if total else 0
            enrolled_courses.append({'course': c, 'enrollment': e, 'progress': pct, 'cert': None})
    cert_ids = {c['course_id']: c for c in certs}
    for ec in enrolled_courses:
        ec['cert'] = cert_ids.get(ec['course']['id'])
    return render_template('dashboard.html', enrolled_courses=enrolled_courses)

@app.route('/course/<course_id>')
@login_required
def course(course_id):
    c = load_course(course_id)
    if not c: abort(404)
    db = get_db()
    enrol = db.execute(
        'SELECT * FROM enrollments WHERE student_id=? AND course_id=?',
        (session['student_id'], course_id)
    ).fetchone()
    cert = db.execute(
        'SELECT * FROM certificates WHERE student_id=? AND course_id=?',
        (session['student_id'], course_id)
    ).fetchone()
    db.close()
    if not enrol:
        return render_template('enroll.html', course=c)
    completed, scores = get_student_progress(session['student_id'], course_id)
    total = sum(len(m['lessons']) for m in c['modules'])
    pct = int(len(completed) / total * 100) if total else 0
    return render_template('course.html', course=c, completed=completed,
                           scores=scores, progress=pct, cert=cert)

@app.route('/course/<course_id>/lesson/<int:module_id>/<int:lesson_idx>')
@login_required
def lesson(course_id, module_id, lesson_idx):
    c = load_course(course_id)
    if not c: abort(404)
    db = get_db()
    enrol = db.execute(
        'SELECT * FROM enrollments WHERE student_id=? AND course_id=?',
        (session['student_id'], course_id)
    ).fetchone()
    db.close()
    if not enrol: return redirect(url_for('course', course_id=course_id))
    mod = next((m for m in c['modules'] if m['id'] == module_id), None)
    if not mod or lesson_idx >= len(mod['lessons']): abort(404)
    les = mod['lessons'][lesson_idx]
    completed, scores = get_student_progress(session['student_id'], course_id)
    # next lesson
    next_url = None
    if lesson_idx + 1 < len(mod['lessons']):
        next_url = url_for('lesson', course_id=course_id, module_id=module_id, lesson_idx=lesson_idx+1)
    else:
        next_mod_idx = next((i+1 for i,m in enumerate(c['modules']) if m['id']==module_id), None)
        if next_mod_idx and next_mod_idx < len(c['modules']):
            next_url = url_for('lesson', course_id=course_id,
                               module_id=c['modules'][next_mod_idx]['id'], lesson_idx=0)
    return render_template('lesson.html', course=c, module=mod, lesson=les,
                           lesson_idx=lesson_idx, completed=completed,
                           scores=scores, next_url=next_url)

@app.route('/api/complete', methods=['POST'])
@login_required
def complete_lesson():
    data = request.json
    course_id  = data.get('course_id')
    module_id  = int(data.get('module_id', 0))
    lesson_idx = int(data.get('lesson_idx', 0))
    score      = data.get('score')
    db = get_db()
    db.execute(
        '''INSERT INTO progress (student_id,course_id,module_id,lesson_idx,completed,score,completed_at)
        VALUES (?,?,?,?,1,?,datetime('now'))
        ON CONFLICT(student_id,course_id,module_id,lesson_idx)
        DO UPDATE SET completed=1, score=excluded.score, completed_at=excluded.completed_at''',
        (session['student_id'], course_id, module_id, lesson_idx, score)
    )
    db.commit()
    # Check if course complete
    c = load_course(course_id)
    total = sum(len(m['lessons']) for m in c['modules'])
    done_count = db.execute(
        'SELECT COUNT(*) as n FROM progress WHERE student_id=? AND course_id=? AND completed=1',
        (session['student_id'], course_id)
    ).fetchone()['n']
    cert_issued = False
    cert_code = None
    if done_count >= total:
        existing = db.execute(
            'SELECT cert_code FROM certificates WHERE student_id=? AND course_id=?',
            (session['student_id'], course_id)
        ).fetchone()
        if not existing:
            cert_code = secrets.token_hex(6).upper()
            db.execute(
                'INSERT INTO certificates (student_id,course_id,cert_code,score) VALUES (?,?,?,?)',
                (session['student_id'], course_id, cert_code, score)
            )
            db.commit()
            cert_issued = True
        else:
            cert_code = existing['cert_code']
    db.close()
    pct = int(done_count / total * 100) if total else 0
    return jsonify({'ok': True, 'progress': pct, 'cert_issued': cert_issued, 'cert_code': cert_code})

@app.route('/certificate/<course_id>')
@login_required
def certificate(course_id):
    db = get_db()
    cert = db.execute(
        'SELECT * FROM certificates WHERE student_id=? AND course_id=?',
        (session['student_id'], course_id)
    ).fetchone()
    db.close()
    if not cert: abort(404)
    c = load_course(course_id)
    return render_template('certificate.html', course=c, cert=cert,
                           student_name=session['student_name'],
                           issued_at=cert['issued_at'][:10])

# ─────────────────────────────────────────────────────────────
# ROUTES — Gumroad Webhook (auto-enrol)
# ─────────────────────────────────────────────────────────────
PRODUCT_MAP = {
    'nzciflexi':      'nzci-flexi-excavator',
    'nzciflexicert':  'nzci-flexi-excavator',
    'compaction101':  'compaction-101',
    'compaction101cert': 'compaction-101',
}

@app.route('/webhook/gumroad', methods=['POST'])
def gumroad_webhook():
    data = request.form
    email     = data.get('email', '').lower().strip()
    name      = data.get('full_name', email.split('@')[0])
    permalink = data.get('product_permalink', '').lower()
    sale_id   = data.get('sale_id', '' )
    tier      = 'cert' if 'cert' in permalink else 'intro'
    course_id = PRODUCT_MAP.get(permalink)
    if not course_id or not email:
        return jsonify({'ok': False, 'msg': 'Unknown product'}), 400
    db = get_db()
    student = db.execute('SELECT * FROM students WHERE email=?', (email,)).fetchone()
    if not student:
        tmp_pw = secrets.token_hex(8)
        db.execute(
            'INSERT OR IGNORE INTO students (email,name,password_hash) VALUES (?,?,?)',
            (email, name, hash_pw(tmp_pw))
        )
        db.commit()
        student = db.execute('SELECT * FROM students WHERE email=?', (email,)).fetchone()
    db.execute(
        'INSERT OR IGNORE INTO enrollments (student_id,course_id,tier,gumroad_sale_id) VALUES (?,?,?,?)',
        (student['id'], course_id, tier, sale_id)
    )
    db.commit()
    db.close()
    return jsonify({'ok': True, 'enrolled': course_id})

# ─────────────────────────────────────────────────────────────
# ROUTES — Admin
# ─────────────────────────────────────────────────────────────
@app.route('/admin')
@login_required
@admin_required
def admin():
    db = get_db()
    students = db.execute('SELECT * FROM students ORDER BY created_at DESC').fetchall()
    enrollments = db.execute('SELECT * FROM enrollments ORDER BY enrolled_at DESC').fetchall()
    certs = db.execute('SELECT * FROM certificates ORDER BY issued_at DESC').fetchall()
    db.close()
    return render_template('admin.html', students=students,
                           enrollments=enrollments, certs=certs)

@app.route('/admin/enroll', methods=['POST'])
@login_required
@admin_required
def admin_enroll():
    email     = request.form['email'].lower().strip()
    name      = request.form.get('name', email.split('@')[0])
    course_id = request.form['course_id']
    tier      = request.form.get('tier', 'intro')
    db = get_db()
    student = db.execute('SELECT * FROM students WHERE email=?', (email,)).fetchone()
    if not student:
        tmp_pw = secrets.token_hex(8)
        db.execute(
            'INSERT INTO students (email,name,password_hash) VALUES (?,?,?)',
            (email, name, hash_pw(tmp_pw))
        )
        db.commit()
        student = db.execute('SELECT * FROM students WHERE email=?', (email,)).fetchone()
    db.execute(
        'INSERT OR IGNORE INTO enrollments (student_id,course_id,tier) VALUES (?,?,?)',
        (student['id'], course_id, tier)
    )
    db.commit()
    db.close()
    return redirect(url_for('admin'))

# ─────────────────────────────────────────────────────────────
# HEALTH CHECK
# ─────────────────────────────────────────────────────────────
@app.route('/health')
def health():
    db = get_db()
    students = db.execute('SELECT COUNT(*) as n FROM students').fetchone()['n']
    enrols = db.execute('SELECT COUNT(*) as n FROM enrollments').fetchone()['n']
    certs = db.execute('SELECT COUNT(*) as n FROM certificates').fetchone()['n']
    db.close()
    return jsonify({'status': 'ok', 'students': students,
                    'enrollments': enrols, 'certificates': certs,
                    'courses': len(load_courses())})

if __name__ == '__main__':
    init_db()
    app.run(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 5001)))
