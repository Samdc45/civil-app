
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
    db.execute('PRAGMA journal_mode=WAL')
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
        CREATE TABLE IF NOT EXISTS cv_applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT,
            location TEXT,
            years_experience TEXT,
            current_role TEXT,
            destination_country TEXT,
            skills TEXT,
            cv_filename TEXT,
            cv_data BLOB,
            enrolled_course_id TEXT,
            student_id INTEGER,
            submitted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            contacted INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS meeting_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            meeting_date TEXT NOT NULL,
            meeting_time TEXT NOT NULL,
            site_name TEXT NOT NULL,
            supervisor TEXT NOT NULL,
            weather TEXT,
            attendees TEXT,
            carryover TEXT,
            work_plan TEXT,
            locates_confirmed INTEGER DEFAULT 0,
            hazard_1 TEXT,
            hazard_2 TEXT,
            hazard_3 TEXT,
            plant_status TEXT,
            floor_open TEXT,
            discussion_topic TEXT,
            discussion_notes TEXT,
            actions TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            student_id INTEGER
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

FLAG_EMOJI = {
    'NZ': '🇳🇿',
    'AU': '🇦🇺',
    'CA': '🇨🇦',
    'US': '🇺🇸',
    'GLOBAL': '🌏',
}

def load_courses():
    courses = []
    for f in sorted(os.listdir(COURSES_DIR)):
        if f.endswith('.json'):
            with open(os.path.join(COURSES_DIR, f)) as fh:
                c = json.load(fh)
            if not isinstance(c, dict):
                continue  # skip non-course files (e.g. discussion_cards list)
            c['flag_emoji'] = FLAG_EMOJI.get(c.get('flag',''), '🏳')
            c.setdefault('thumbnail', '🏗')
            c.setdefault('gumroad_intro', '#')
            c.setdefault('price_intro', 97)
            c.setdefault('level', 'Entry Level')
            c.setdefault('duration', '2-3 hours')
            c.setdefault('color', '#1f6feb')
            courses.append(c)
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


# ─────────────────────────────────────────────────────────────
# DAILY MEETING RECORD
# ─────────────────────────────────────────────────────────────
DISCUSSION_CARDS_PATH = os.path.join(COURSES_DIR, 'discussion_cards.json')

def load_discussion_cards():
    if os.path.exists(DISCUSSION_CARDS_PATH):
        with open(DISCUSSION_CARDS_PATH) as f:
            return json.load(f)
    return []

@app.route('/daily-record', methods=['GET', 'POST'])
def daily_record():
    cards = load_discussion_cards()
    today = datetime.now().strftime('%Y-%m-%d')
    now_time = datetime.now().strftime('%H:%M')
    if request.method == 'POST':
        d = request.form
        weather = ', '.join(request.form.getlist('weather'))
        locates = 1 if d.get('locates_confirmed') == 'yes' else 0
        db = get_db()
        cur = db.execute('''
            INSERT INTO meeting_records
            (meeting_date, meeting_time, site_name, supervisor, weather, attendees,
             carryover, work_plan, locates_confirmed, hazard_1, hazard_2, hazard_3,
             plant_status, floor_open, discussion_topic, discussion_notes, actions, student_id)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        ''',(
            d.get('meeting_date'), d.get('meeting_time'), d.get('site_name'),
            d.get('supervisor'), weather, d.get('attendees'),
            d.get('carryover'), d.get('work_plan'), locates,
            d.get('hazard_1'), d.get('hazard_2'), d.get('hazard_3'),
            d.get('plant_status'), d.get('floor_open'),
            d.get('discussion_topic'), d.get('discussion_notes'),
            d.get('actions'), session.get('student_id')
        ))
        db.commit()
        record_id = cur.lastrowid
        db.close()
        timestamp = datetime.now().strftime('%d %b %Y %H:%M')
        return render_template('daily_record.html', submitted=True,
                               record_id=record_id, timestamp=timestamp,
                               discussion_cards=cards)
    return render_template('daily_record.html', submitted=False,
                           today=today, now_time=now_time,
                           discussion_cards=cards)

@app.route('/daily-record/<int:record_id>/pdf')
def daily_record_pdf(record_id):
    db = get_db()
    r = db.execute('SELECT * FROM meeting_records WHERE id=?', (record_id,)).fetchone()
    db.close()
    if not r:
        abort(404)
    # Generate simple HTML PDF
    locates_str = '✅ CONFIRMED' if r['locates_confirmed'] else '⚠️ NOT RECORDED'
    html = f'''<!DOCTYPE html><html><head><meta charset="utf-8">
<title>Pre-Start Record #{record_id}</title>
<style>
body{{font-family:Arial,sans-serif;max-width:800px;margin:0 auto;padding:20px;color:#1a1a1a}}
h1{{background:#f59e0b;color:#000;padding:16px;border-radius:8px;margin-bottom:0}}
.header-sub{{background:#fef3c7;padding:8px 16px;border-radius:0 0 8px 8px;margin-bottom:24px;font-size:0.9rem}}
.section{{border:1px solid #e5e7eb;border-radius:8px;padding:16px;margin-bottom:16px}}
.section h3{{margin:0 0 8px;color:#b45309;font-size:1rem}}
.grid{{display:grid;grid-template-columns:1fr 1fr;gap:12px}}
.field{{margin-bottom:8px}}
.label{{font-size:0.75rem;color:#6b7280;font-weight:600;text-transform:uppercase}}
.value{{font-size:0.9rem;color:#111;padding:4px 0;border-bottom:1px solid #f3f4f6}}
.hazard{{background:#fef3c7;border-left:4px solid #f59e0b;padding:8px 12px;margin-bottom:8px;border-radius:0 4px 4px 0}}
.footer{{text-align:center;color:#9ca3af;font-size:0.75rem;margin-top:32px;border-top:1px solid #e5e7eb;padding-top:16px}}
</style></head><body>
<h1>📋 Pre-Start Meeting Record</h1>
<div class="header-sub">Civil App &bull; South Consultants NZ &bull; Record #{record_id}</div>
<div class="section"><h3>📍 Site Details</h3>
<div class="grid">
<div class="field"><div class="label">Date</div><div class="value">{r['meeting_date']}</div></div>
<div class="field"><div class="label">Time</div><div class="value">{r['meeting_time']}</div></div>
<div class="field"><div class="label">Site</div><div class="value">{r['site_name']}</div></div>
<div class="field"><div class="label">Supervisor</div><div class="value">{r['supervisor']}</div></div>
<div class="field"><div class="label">Weather</div><div class="value">{r['weather'] or 'Not recorded'}</div></div>
<div class="field"><div class="label">Service Locates</div><div class="value">{locates_str}</div></div>
</div></div>
<div class="section"><h3>👷 Attendees</h3>
<div class="value" style="white-space:pre-line">{r['attendees'] or 'Not recorded'}</div></div>
<div class="section"><h3>🔄 Step 1 — Yesterday's Carryover</h3>
<div class="value">{r['carryover'] or 'None noted'}</div></div>
<div class="section"><h3>📅 Step 2 — Today's Work Plan</h3>
<div class="value">{r['work_plan'] or 'Not recorded'}</div></div>
<div class="section"><h3>⚠️ Step 3 — The Big Three Hazards</h3>
<div class="hazard"><strong>1.</strong> {r['hazard_1'] or 'Not recorded'}</div>
<div class="hazard"><strong>2.</strong> {r['hazard_2'] or 'Not recorded'}</div>
<div class="hazard"><strong>3.</strong> {r['hazard_3'] or 'Not recorded'}</div></div>
<div class="section"><h3>🚧 Step 4 — Plant Status</h3>
<div class="value">{r['plant_status'] or 'All plant OK'}</div></div>
<div class="section"><h3>🙋 Step 5 — Floor Open</h3>
<div class="value">{r['floor_open'] or 'No items raised'}</div></div>
<div class="section"><h3>💬 Safety Discussion Topic</h3>
<div class="field"><div class="label">Topic</div><div class="value">{r['discussion_topic'] or 'Not selected'}</div></div>
<div class="field"><div class="label">Notes</div><div class="value">{r['discussion_notes'] or 'Not recorded'}</div></div></div>
<div class="section"><h3>✅ Actions Required</h3>
<div class="value">{r['actions'] or 'No actions'}</div></div>
<div class="footer">
Record #{record_id} &bull; Created: {r['created_at']} &bull; Civil App &bull; South Consultants NZ<br>
This record constitutes evidence of pre-start safety management under HSWA 2015 (NZ), WHS Act 2011 (AU), OSHA (US), OHS Code (CA).
</div></body></html>'''
    from flask import Response
    return Response(html, mimetype='text/html',
                    headers={'Content-Disposition': f'attachment; filename=prestart-record-{record_id}.html'})

@app.route('/daily-record/history')
def daily_record_history():
    if not session.get('is_admin') and not session.get('student_id'):
        return redirect(url_for('login'))
    db = get_db()
    if session.get('is_admin'):
        records = db.execute('SELECT * FROM meeting_records ORDER BY created_at DESC LIMIT 100').fetchall()
    else:
        records = db.execute('SELECT * FROM meeting_records WHERE student_id=? ORDER BY created_at DESC LIMIT 50',
                             (session['student_id'],)).fetchall()
    db.close()
    cards = load_discussion_cards()
    return render_template('record_history.html', records=records, discussion_cards=cards)

@app.route('/pricing')
def pricing():
    return render_template('pricing.html')



# ============================================================
# PHILIPPINES BETA ROUTES
# ============================================================

@app.route('/philippines')
@app.route('/ph-beta')
def ph_landing():
    return render_template('ph_landing.html')


@app.route('/ph-register', methods=['GET', 'POST'])
def ph_register():
    if request.method == 'POST':
        from werkzeug.security import generate_password_hash
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').lower().strip()
        password = request.form.get('password', '').strip()
        phone = request.form.get('phone', '')
        location = request.form.get('location', '')
        years_exp = request.form.get('years_experience', '')
        current_role = request.form.get('current_role', '')
        destination = request.form.get('destination_country', 'New Zealand')
        skills = request.form.get('skills', '')
        cv_file = request.files.get('cv_file')
        cv_filename = None
        cv_data = None
        if cv_file and cv_file.filename:
            cv_filename = cv_file.filename
            cv_data = cv_file.read()
        if not full_name or not email or not password:
            return render_template('ph_landing.html', error='Please fill in all required fields.')
        db = get_db()
        existing = db.execute('SELECT id FROM students WHERE email = ?', (email,)).fetchone()
        if existing:
            student_id = existing['id']
        else:
            pw_hash = generate_password_hash(password)
            cur = db.execute('INSERT INTO students (name, email, password_hash) VALUES (?, ?, ?)', (full_name, email, pw_hash))
            db.commit()
            student_id = cur.lastrowid
        db.execute('INSERT INTO cv_applications (full_name, email, phone, location, years_experience, current_role, destination_country, skills, cv_filename, cv_data, student_id, enrolled_course_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
            (full_name, email, phone, location, years_exp, current_role, destination, skills, cv_filename, cv_data, student_id, 'ph-civil-safety-intro'))
        existing_enroll = db.execute('SELECT id FROM enrollments WHERE student_id = ? AND course_id = ?', (student_id, 'ph-civil-safety-intro')).fetchone()
        if not existing_enroll:
            db.execute('INSERT INTO enrollments (student_id, course_id, tier) VALUES (?, ?, ?)', (student_id, 'ph-civil-safety-intro', 'beta_free'))
        db.commit()
        session['student_id'] = student_id
        session['student_name'] = full_name
        session['student_email'] = email
        session['is_admin'] = False
        return redirect(url_for('ph_welcome'))
    return render_template('ph_landing.html')


@app.route('/ph-welcome')
def ph_welcome():
    return render_template('ph_welcome.html', student_name=session.get('student_name', 'Ka-trabahador'))


@app.route('/admin/cvs')
def admin_cvs():
    if not session.get('is_admin'):
        return redirect(url_for('login'))
    db = get_db()
    cvs = db.execute('SELECT id, full_name, email, phone, location, years_experience, current_role, destination_country, skills, cv_filename, submitted_at, contacted FROM cv_applications ORDER BY submitted_at DESC').fetchall()
    return render_template('cv_admin.html', cvs=cvs)


@app.route('/admin/cv-download/<int:cv_id>')
def cv_download(cv_id):
    if not session.get('is_admin'):
        return redirect(url_for('login'))
    db = get_db()
    cv = db.execute('SELECT * FROM cv_applications WHERE id = ?', (cv_id,)).fetchone()
    if not cv or not cv['cv_data']:
        return 'CV not found', 404
    from flask import Response
    fname = cv['cv_filename'] or 'cv.pdf'
    return Response(cv['cv_data'], mimetype='application/octet-stream',
                    headers={'Content-Disposition': 'attachment; filename="' + fname + '"'})


@app.route('/admin/cv-contact/<int:cv_id>', methods=['POST'])
def cv_mark_contacted(cv_id):
    if not session.get('is_admin'):
        return jsonify({'ok': False}), 403
    db = get_db()
    db.execute('UPDATE cv_applications SET contacted = 1 WHERE id = ?', (cv_id,))
    db.commit()
    return jsonify({'ok': True})


def seed_admin():
    """Create default admin account on first run if none exists"""
    with app.app_context():
        db = get_db()
        admin = db.execute('SELECT id FROM students WHERE is_admin=1').fetchone()
        if not admin:
            from werkzeug.security import generate_password_hash
            pw = generate_password_hash('CivilApp2026!')
            db.execute(
                'INSERT INTO students (name, email, password_hash, is_admin) VALUES (?, ?, ?, 1)',
                ('Sam Admin', 'civilbesafe@gmail.com', pw)
            )
            db.commit()
            print('[SEED] Admin account created: civilbesafe@gmail.com')
        else:
            print('[SEED] Admin account already exists')

if __name__ == '__main__':
    init_db()
    app.run(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 5001)))
