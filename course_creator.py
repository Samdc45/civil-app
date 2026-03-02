"""
course_creator.py — South Consultants / Civil App LMS
Course Creator Subagent Module

Philosophy:
  - Adult learning (Andragogy): self-directed, experience-based, problem-centred
  - Vocational emphasis: every lesson maps to a real on-site task or decision
  - Train the Trainer: every learner pathway leads to becoming a trainer/affiliate
  - Lifelong affiliate model: certification → referral → community → income
  - Sam's principle: 'Train to replace yourself. Then train them to replace themselves.'

Author: South Consultants NZ — Civil App LMS
Date: 2026
"""

import os
import json
import re
import sys
import time
import asyncio
import logging
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional

# ─────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────
LMS_DIR     = Path(__file__).parent
COURSES_DIR = LMS_DIR / 'courses'

OPENROUTER_KEY  = os.environ.get('API_KEY_OPENROUTER', '')
OPENAI_KEY      = os.environ.get('API_KEY_OPENAI', '')
LLM_API_KEY     = OPENROUTER_KEY or OPENAI_KEY
LLM_BASE_URL    = 'https://openrouter.ai/api/v1' if OPENROUTER_KEY else 'https://api.openai.com/v1'
LLM_MODEL       = 'anthropic/claude-sonnet-4-5' if OPENROUTER_KEY else 'gpt-4o'

LOG_FILE = '/tmp/course_linkedin_scheduler.log'

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_FILE, mode='a')
    ]
)
log = logging.getLogger('course_creator')

# Country metadata
COUNTRY_META = {
    'NZ': {
        'name': 'New Zealand', 'flag': '🇳🇿',
        'regulator': 'WorkSafe NZ', 'legislation': 'Health and Safety at Work Act 2015 (HSWA)',
        'standards': 'NZS, CoPTTM, AS/NZS', 'currency': 'NZD',
        'phone': '0800 030 040'
    },
    'AU': {
        'name': 'Australia', 'flag': '🇦🇺',
        'regulator': 'Safe Work Australia', 'legislation': 'Work Health and Safety Act 2011 (WHS)',
        'standards': 'AS/NZS, PCBU, Safe Work Method Statements (SWMS)', 'currency': 'AUD',
        'phone': '1800 003 338'
    },
    'US': {
        'name': 'United States', 'flag': '🇺🇸',
        'regulator': 'OSHA', 'legislation': 'Occupational Safety and Health Act 1970',
        'standards': 'OSHA 29 CFR, ANSI, ASTM', 'currency': 'USD',
        'phone': '1-800-321-OSHA'
    },
    'CA': {
        'name': 'Canada', 'flag': '🇨🇦',
        'regulator': 'CCOHS', 'legislation': 'Canada Labour Code / Provincial OHS Acts',
        'standards': 'CSA, OHS Regulations', 'currency': 'CAD',
        'phone': '1-800-668-4284'
    },
    'PH': {
        'name': 'Philippines', 'flag': '🇵🇭',
        'regulator': 'DOLE / OSHC', 'legislation': 'Occupational Safety and Health Standards (OSHS) RA 11058',
        'standards': 'DOLE OSHS, Philippine Electrical Code', 'currency': 'PHP',
        'phone': '(02) 8527-8000'
    },
    'GLOBAL': {
        'name': 'Global / International', 'flag': '🌏',
        'regulator': 'ISO / ILO', 'legislation': 'ISO 45001:2018 / ILO-OSH 2001',
        'standards': 'ISO 45001, ISO 9001, ILO Conventions', 'currency': 'USD',
        'phone': 'ISO Helpdesk'
    },
}

# Adult learning / vocational course generation system prompt
SYSTEM_PROMPT_COURSE = """
You are the course development engine for South Consultants NZ / Civil App LMS.

CORE PHILOSOPHY:
"Train to replace yourself. Then train them to replace themselves." — Sam Dampier-Crossley

ADULT LEARNING PRINCIPLES (Andragogy — Knowles Framework):
1. Self-directed: Learners choose their pace and path
2. Experience-based: Every lesson connects to real site experience
3. Problem-centred: Content solves real on-the-job problems
4. Immediate relevance: Learners must see the practical value NOW
5. Internal motivation: Pride in craft, career advancement, team respect

VOCATIONAL EMPHASIS:
- Every lesson has a 'on-site application' section
- Real scenarios from civil construction (trenching, plant, traffic, hazmat)
- Competency statements: 'After this lesson you can...'
- Skills linked to nationally recognised qualifications and unit standards
- Assessment maps to real-world tasks, not theory recall

TRAIN THE TRAINER PATHWAY:
- Every course ends with a 'Teach This' section — how to pass this knowledge on
- Affiliate pathway: graduate → trainer → affiliate → income
- Micro-teaching moments embedded in lesson content
- Leadership language: 'When you're the supervisor on site...'

LIFELONG AFFILIATE MODEL:
- Certification creates identity: 'I am a Civil App certified trainer'
- Each module has a shareable achievement card concept
- LinkedIn-ready achievement statement per module
- Referral hooks: 'Know someone who needs this? Share your certificate link'

BRAND VOICE:
- Direct, practical, grounded in 30 years on-site experience
- Not corporate, not generic — sounds like a foreman who's built things
- Plain English with correct construction terminology
- 'Not compliance boxes. Culture builders.'

CONTENT QUALITY:
- Rich, substantive lesson content (300-500 words each)
- Specific numbers, regulations, standards — never vague
- Country-appropriate: correct legislation, regulators, phone numbers
- Real hazard scenarios from the industry
"""

# ─────────────────────────────────────────────────────────────
# LLM HELPER
# ─────────────────────────────────────────────────────────────
def call_llm(prompt: str, system: str = None, temperature: float = 0.7, max_tokens: int = 4000) -> str:
    """Call LLM via OpenAI-compatible API."""
    try:
        from openai import OpenAI
        client = OpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL)
        messages = []
        if system:
            messages.append({'role': 'system', 'content': system})
        messages.append({'role': 'user', 'content': prompt})
        resp = client.chat.completions.create(
            model=LLM_MODEL,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        log.error(f'LLM call failed: {e}')
        raise


def slugify(text: str) -> str:
    """Convert text to a filesystem-safe slug."""
    s = text.lower().strip()
    s = re.sub(r'[^\w\s-]', '', s)
    s = re.sub(r'[\s_-]+', '_', s)
    s = re.sub(r'^-+|-+$', '', s)
    return s


def load_course_file(course_name: str) -> dict:
    """Load a course JSON file by name (with or without .json)."""
    name = course_name.replace('.json', '')
    path = COURSES_DIR / f'{name}.json'
    if not path.exists():
        # Try to find by course id
        for f in COURSES_DIR.glob('*.json'):
            try:
                data = json.loads(f.read_text())
                if isinstance(data, dict) and data.get('id') == name:
                    return data
            except Exception:
                pass
        raise FileNotFoundError(f'Course not found: {course_name}')
    return json.loads(path.read_text())


def save_course_file(course_name: str, data: dict) -> Path:
    """Save a course JSON file."""
    name = course_name.replace('.json', '')
    path = COURSES_DIR / f'{name}.json'
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    return path


# ─────────────────────────────────────────────────────────────
# 1. CHECK COURSE — Health Audit
# ─────────────────────────────────────────────────────────────
def check_course(course_name: str) -> dict:
    """
    Audit a course JSON file.
    Returns a comprehensive health report with scores.
    """
    log.info(f'Checking course: {course_name}')

    try:
        data = load_course_file(course_name)
    except FileNotFoundError as e:
        return {'error': str(e), 'status': 'not_found'}

    report = {
        'course_id':    data.get('id', 'unknown'),
        'title':        data.get('title', 'Untitled'),
        'country':      data.get('country', 'GLOBAL'),
        'checked_at':   datetime.now().isoformat(),
        'modules':      [],
        'totals':       {},
        'issues':       [],
        'score':        0,
        'grade':        '',
        'adult_learning_score': 0,
        'trainer_pathway_present': False,
        'affiliate_hooks_present': False,
    }

    total_lessons = 0
    total_quizzes = 0
    total_questions = 0
    empty_lessons = 0
    missing_quizzes = 0
    short_content = 0
    modules_without_quiz = []
    has_trainer_content = False
    has_affiliate_hooks = False
    adult_learning_indicators = 0

    for mod in data.get('modules', []):
        mod_report = {
            'id':            mod.get('id'),
            'title':         mod.get('title', 'Untitled'),
            'lesson_count':  0,
            'quiz_count':    0,
            'question_count': 0,
            'issues':        [],
        }

        has_quiz = False
        for lesson in mod.get('lessons', []):
            ltype = lesson.get('type', 'lesson')

            if ltype == 'lesson':
                total_lessons += 1
                mod_report['lesson_count'] += 1
                content = lesson.get('content', '')
                if not content or len(content) < 50:
                    empty_lessons += 1
                    mod_report['issues'].append(f'Empty/short lesson: {lesson.get("title")}')
                elif len(content) < 200:
                    short_content += 1
                    mod_report['issues'].append(f'Thin content ({len(content)} chars): {lesson.get("title")}')

                # Adult learning indicators
                content_lower = content.lower()
                for indicator in ['on site', 'on-site', 'supervisor', 'replace yourself',
                                   'apply', 'practical', 'when you are', 'competency',
                                   'trainer', 'teach', 'affiliate']:
                    if indicator in content_lower:
                        adult_learning_indicators += 1
                if 'train' in content_lower and 'trainer' in content_lower:
                    has_trainer_content = True
                if 'affiliate' in content_lower or 'refer' in content_lower:
                    has_affiliate_hooks = True

            elif ltype == 'quiz':
                total_quizzes += 1
                mod_report['quiz_count'] += 1
                has_quiz = True
                questions = lesson.get('questions', [])
                mod_report['question_count'] += len(questions)
                total_questions += len(questions)

                if len(questions) < 3:
                    mod_report['issues'].append(f'Quiz has only {len(questions)} question(s) — recommend 3+')

                for qi, q in enumerate(questions):
                    if not q.get('q') and not q.get('question'):
                        mod_report['issues'].append(f'Q{qi+1}: missing question text')
                    if len(q.get('options', [])) < 4:
                        mod_report['issues'].append(f'Q{qi+1}: fewer than 4 options')
                    if q.get('answer') is None and q.get('correct_answer') is None:
                        mod_report['issues'].append(f'Q{qi+1}: no correct_answer field')

        if not has_quiz:
            missing_quizzes += 1
            modules_without_quiz.append(mod.get('title', f'Module {mod.get("id")}'))
            mod_report['issues'].append('No quiz found in this module')

        report['modules'].append(mod_report)

    # Scoring
    base_score = 100
    deductions = []

    if empty_lessons > 0:
        d = min(empty_lessons * 10, 30)
        base_score -= d
        deductions.append(f'-{d} empty/missing lesson content ({empty_lessons} lessons)')
    if short_content > 0:
        d = min(short_content * 5, 20)
        base_score -= d
        deductions.append(f'-{d} thin content ({short_content} lessons under 200 chars)')
    if missing_quizzes > 0:
        d = missing_quizzes * 8
        base_score -= d
        deductions.append(f'-{d} missing quizzes ({missing_quizzes} modules)')
    if total_questions < (total_lessons * 2):
        d = 10
        base_score -= d
        deductions.append(f'-{d} insufficient quiz coverage (< 2 questions per lesson)')
    if not data.get('description'):
        base_score -= 5
        deductions.append('-5 missing course description')
    if not data.get('subtitle'):
        base_score -= 3
        deductions.append('-3 missing subtitle')

    # Adult learning score
    al_score = min(100, adult_learning_indicators * 5)

    base_score = max(0, base_score)
    if base_score >= 90:
        grade = 'A — Production Ready'
    elif base_score >= 75:
        grade = 'B — Good, minor fixes needed'
    elif base_score >= 60:
        grade = 'C — Usable, improvements recommended'
    elif base_score >= 40:
        grade = 'D — Significant gaps'
    else:
        grade = 'F — Major rebuild needed'

    report['totals'] = {
        'modules':              len(data.get('modules', [])),
        'lessons':              total_lessons,
        'quizzes':              total_quizzes,
        'questions':            total_questions,
        'empty_lessons':        empty_lessons,
        'short_content':        short_content,
        'modules_without_quiz': missing_quizzes,
    }
    report['issues'] = [
        f'Modules without quiz: {modules_without_quiz}' if modules_without_quiz else None,
        f'{empty_lessons} empty or near-empty lessons' if empty_lessons else None,
        f'{short_content} lessons with thin content' if short_content else None,
    ]
    report['issues'] = [i for i in report['issues'] if i]
    report['deductions'] = deductions
    report['score'] = base_score
    report['grade'] = grade
    report['adult_learning_score'] = al_score
    report['trainer_pathway_present'] = has_trainer_content
    report['affiliate_hooks_present'] = has_affiliate_hooks

    log.info(f'Health check complete: {grade} ({base_score}/100)')
    return report


# ─────────────────────────────────────────────────────────────
# 2. DEVELOP COURSE — AI Course Generation
# ─────────────────────────────────────────────────────────────
def develop_course(topic: str, country_code: str = 'GLOBAL', num_modules: int = 5) -> dict:
    """
    Generate a complete new course JSON using LLM.
    Applies adult learning, vocational, and train-the-trainer principles.
    Saves to courses/{topic_slug}.json
    """
    country_code = country_code.upper()
    meta = COUNTRY_META.get(country_code, COUNTRY_META['GLOBAL'])
    slug = slugify(topic)
    course_id = f'{country_code.lower()}-{slug}'

    log.info(f'Developing course: {topic} [{country_code}] — {num_modules} modules')

    prompt = f"""
Create a complete, production-ready course JSON for the Civil App LMS.

TOPIC: {topic}
COUNTRY: {meta['name']} ({country_code})
REGULATOR: {meta['regulator']}
LEGISLATION: {meta['legislation']}
STANDARDS: {meta['standards']}
NUMBER OF MODULES: {num_modules}

Return ONLY valid JSON — no markdown, no explanation, no code blocks.
The JSON must follow this exact schema:

{{
  "id": "{course_id}",
  "title": "Course Title",
  "subtitle": "Subtitle",
  "description": "Course description (2-3 sentences, direct, practical tone)",
  "duration": "X-Y hours",
  "level": "Entry Level|Intermediate|Advanced",
  "country": "{country_code}",
  "flag": "{country_code}",
  "color": "#hex",
  "price_intro": 97,
  "price_cert": 297,
  "modules": [
    {{
      "id": 1,
      "title": "Module Title",
      "duration": "30 min",
      "lessons": [
        {{
          "title": "Lesson Title",
          "type": "lesson",
          "content": "Full lesson content with markdown. MUST include:\n- Core concept with specific regulations/standards\n- Real on-site scenario or example\n- **Competency Statement:** After this lesson you can...\n- **On-Site Application:** When you are on site...\n- **Teach This Forward:** How to explain this to your crew..."
        }},
        {{
          "title": "Quiz",
          "type": "quiz",
          "pass_mark": 70,
          "questions": [
            {{
              "q": "Question text?",
              "options": ["Option A", "Option B", "Option C", "Option D"],
              "answer": 0
            }}
          ]
        }}
      ]
    }}
  ],
  "trainer_pathway": {{
    "description": "How graduates become certified trainers and affiliates",
    "steps": ["Complete all modules", "Share certificate", "Refer others", "Earn affiliate commission"],
    "affiliate_message": "LinkedIn-ready achievement statement"
  }}
}}

REQUIREMENTS:
1. Each module must have 2-4 lesson lessons AND 1 quiz
2. Lesson content must be 300-500 words minimum
3. Every lesson must include a real {meta['name']} scenario
4. Quote actual legislation: {meta['legislation']}
5. Include correct regulator details: {meta['regulator']} — {meta.get('phone', '')}
6. Last module MUST be 'Train the Trainer' — how graduates teach this to others
7. Each quiz must have 3-5 questions with 4 options each
8. Maintain Sam's voice: direct, practical, 30-years-on-site authority
9. Brand voice: 'Not compliance boxes. Culture builders.'
10. Include affiliate/referral hook in final lesson
"""

    log.info('Calling LLM for course generation...')
    raw = call_llm(prompt, system=SYSTEM_PROMPT_COURSE, temperature=0.7, max_tokens=6000)

    # Strip any accidental markdown code fences
    raw = re.sub(r'^```json\s*', '', raw.strip())
    raw = re.sub(r'^```\s*', '', raw.strip())
    raw = re.sub(r'\s*```$', '', raw.strip())

    try:
        course_data = json.loads(raw)
    except json.JSONDecodeError as e:
        log.error(f'LLM returned invalid JSON: {e}')
        log.error(f'Raw output (first 500 chars): {raw[:500]}')
        raise ValueError(f'Course generation failed — LLM returned invalid JSON: {e}')

    # Ensure required fields
    course_data.setdefault('id', course_id)
    course_data.setdefault('country', country_code)
    course_data.setdefault('flag', country_code)
    course_data.setdefault('color', '#1f6feb')
    course_data.setdefault('price_intro', 97)
    course_data.setdefault('price_cert', 297)

    # Save to file
    out_path = COURSES_DIR / f'{slug}.json'
    out_path.write_text(json.dumps(course_data, indent=2, ensure_ascii=False))

    log.info(f'Course saved to: {out_path}')
    return course_data


# ─────────────────────────────────────────────────────────────
# 3. GENERATE QUIZZES — Add missing quizzes to existing course
# ─────────────────────────────────────────────────────────────
def generate_quizzes(course_name: str, questions_per_lesson: int = 3) -> int:
    """
    Generate quiz questions for each lesson that doesn't have them.
    Updates the course JSON file in-place.
    Returns count of questions added.
    """
    log.info(f'Generating quizzes for: {course_name}')
    data = load_course_file(course_name)
    total_added = 0
    country_code = data.get('country', 'GLOBAL')
    meta = COUNTRY_META.get(country_code, COUNTRY_META['GLOBAL'])

    for mod in data.get('modules', []):
        # Collect lesson titles in this module
        lessons_in_mod = [l for l in mod.get('lessons', []) if l.get('type') == 'lesson']
        existing_quiz = next((l for l in mod.get('lessons', []) if l.get('type') == 'quiz'), None)

        # If quiz exists but has fewer than needed questions, regenerate
        needs_quiz = existing_quiz is None
        needs_more = existing_quiz and len(existing_quiz.get('questions', [])) < questions_per_lesson

        if not lessons_in_mod:
            continue

        if needs_quiz or needs_more:
            # Build context from lesson content
            context_parts = []
            for lesson in lessons_in_mod:
                context_parts.append(f"Lesson: {lesson.get('title')}\n{lesson.get('content', '')[:600]}")
            context = '\n\n'.join(context_parts)

            prompt = f"""
Create {questions_per_lesson} multiple choice quiz questions for this civil construction module.

MODULE: {mod.get('title')}
COUNTRY: {meta['name']}
LEGISLATION: {meta['legislation']}

LESSON CONTENT:
{context}

Return ONLY a JSON array of question objects. No markdown, no explanation.
Schema:
[
  {{
    "q": "Question text?",
    "options": ["A", "B", "C", "D"],
    "answer": 0
  }}
]

Requirements:
- Each question tests practical, on-site knowledge
- 4 options each, one clearly correct
- Mix recall, application, and scenario-based questions
- Base answers on {meta['legislation']} and {meta['regulator']} standards
- No trick questions — real knowledge workers need on site
"""

            log.info(f'  Generating quiz for module: {mod.get("title")}')
            raw = call_llm(prompt, temperature=0.5, max_tokens=1500)
            raw = re.sub(r'^```json\s*', '', raw.strip())
            raw = re.sub(r'^```\s*', '', raw.strip())
            raw = re.sub(r'\s*```$', '', raw.strip())

            try:
                questions = json.loads(raw)
            except json.JSONDecodeError:
                log.error(f'  Invalid JSON for module {mod.get("title")} quiz')
                continue

            if needs_quiz:
                quiz_lesson = {
                    'title': 'Quiz',
                    'type': 'quiz',
                    'pass_mark': 70,
                    'questions': questions
                }
                mod['lessons'].append(quiz_lesson)
                total_added += len(questions)
                log.info(f'  Added {len(questions)} questions to {mod.get("title")}')
            elif needs_more:
                existing_quiz['questions'] = questions
                total_added += len(questions)
                log.info(f'  Updated quiz with {len(questions)} questions in {mod.get("title")}')

    # Save updated course
    name = course_name.replace('.json', '')
    save_course_file(name, data)
    log.info(f'Updated course saved. Total questions added: {total_added}')
    return total_added


# ─────────────────────────────────────────────────────────────
# 4. GENERATE LINKEDIN QUESTIONS — Industry engagement posts
# ─────────────────────────────────────────────────────────────
def generate_linkedin_questions(course_name: str, num_posts: int = 5) -> list:
    """
    Generate engaging LinkedIn discussion questions from course content.
    Returns list of post texts ready for LinkedIn.
    Adult learning focus: provoke reflection, invite experience-sharing.
    """
    log.info(f'Generating LinkedIn questions for: {course_name} ({num_posts} posts)')
    data = load_course_file(course_name)

    # Extract key learning points from each module
    learning_points = []
    for mod in data.get('modules', []):
        for lesson in mod.get('lessons', []):
            if lesson.get('type') == 'lesson' and lesson.get('content'):
                learning_points.append({
                    'module': mod.get('title'),
                    'lesson': lesson.get('title'),
                    'snippet': lesson.get('content', '')[:400]
                })

    points_text = json.dumps(learning_points[:15], indent=2)

    prompt = f"""
You are the voice of Sam Dampier-Crossley — 30 years in NZ/AU civil construction.

Course: {data.get('title')}
Country: {data.get('country', 'NZ')}

KEY LEARNING POINTS FROM COURSE:
{points_text}

Generate {num_posts} LinkedIn posts. Return ONLY a JSON array of strings.

Each post must:
1. Start with a provocative question or bold statement from site experience
2. Reference a real scenario from the course content above
3. Invite comments: 'What's your experience?' / 'Drop your answer below'
4. Include 1-2 relevant emojis (construction themed)
5. End with 3-5 relevant hashtags
6. Be 150-300 words — punchy, not corporate
7. ALTERNATE between these post types:
   - Experience question: 'X years on site — what's the one thing...'
   - Safety insight: 'Most crews get this wrong...'
   - Train the trainer: 'The best supervisors I know all do this...'
   - Career hook: 'This certificate took 2 hours. Here's what it unlocked...'
   - Industry debate: 'Controversial take on [topic]...'

Sam's voice rules:
- Direct, confident, warm
- Sounds like a foreman who's been in a trench
- NO corporate language, no buzzwords
- 'Train to replace yourself.' energy throughout
- Mention Civil App naturally — never salesy

Return format: ["post text 1", "post text 2", ...]
"""

    raw = call_llm(prompt, temperature=0.85, max_tokens=3000)
    raw = re.sub(r'^```json\s*', '', raw.strip())
    raw = re.sub(r'^```\s*', '', raw.strip())
    raw = re.sub(r'\s*```$', '', raw.strip())

    try:
        posts = json.loads(raw)
        if not isinstance(posts, list):
            raise ValueError('Expected JSON array')
        log.info(f'Generated {len(posts)} LinkedIn posts')
        return posts
    except (json.JSONDecodeError, ValueError) as e:
        log.error(f'LinkedIn post generation error: {e}')
        # Fallback: try to extract individual items
        lines = [l.strip().strip('"') for l in raw.split('\n') if len(l.strip()) > 50]
        return lines[:num_posts]


# ─────────────────────────────────────────────────────────────
# 5. POST TO LINKEDIN — Playwright automation
# ─────────────────────────────────────────────────────────────
async def _async_post_to_linkedin(post_text: str) -> dict:
    """Async implementation of LinkedIn posting via Playwright."""
    from playwright.async_api import async_playwright

    result = {'success': False, 'error': None, 'timestamp': datetime.now().isoformat()}

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
        )
        ctx = await browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        page = await ctx.new_page()

        try:
            log.info('LinkedIn: Navigating to login...')
            await page.goto('https://www.linkedin.com/login', timeout=30000)
            await page.wait_for_selector('#username', timeout=10000)
            await page.fill('#username', 'civilbesafe@gmail.com')
            await page.fill('#password', 'joFpun-rajtob-domna9')
            await page.click('button[type=submit]')
            await asyncio.sleep(5)

            current_url = page.url
            if not any(x in current_url for x in ['feed', 'mynetwork', 'jobs', 'in/']):
                result['error'] = f'Login failed — landed on: {current_url}'
                log.error(result['error'])
                return result

            log.info('LinkedIn: Logged in. Navigating to feed...')
            await page.goto('https://www.linkedin.com/feed/', timeout=15000)
            await asyncio.sleep(3)

            # Click 'Start a post'
            btn = page.get_by_text('Start a post', exact=False)
            await btn.first.click(timeout=8000)
            await asyncio.sleep(2)

            # Type post text
            editor = page.locator('.ql-editor, [contenteditable=true], [role=textbox]').first
            await editor.click()
            await editor.type(post_text, delay=15)
            await asyncio.sleep(1)

            # Click Post button
            post_btn = page.get_by_role('button', name='Post', exact=True)
            await post_btn.click(timeout=8000)
            await asyncio.sleep(4)

            result['success'] = True
            log.info('LinkedIn: Post published successfully!')

        except Exception as e:
            result['error'] = str(e)
            log.error(f'LinkedIn posting error: {e}')
        finally:
            await browser.close()

    return result


def post_to_linkedin(post_text: str) -> dict:
    """Post text to LinkedIn as Henry Botha (Civil App account)."""
    return asyncio.run(_async_post_to_linkedin(post_text))


# ─────────────────────────────────────────────────────────────
# 6. SCHEDULE LINKEDIN CAMPAIGN — Background scheduler
# ─────────────────────────────────────────────────────────────
def schedule_linkedin_campaign(
    course_name: str,
    posts_per_day: int = 2,
    interval_hours: int = 4
) -> dict:
    """
    Generate LinkedIn questions from course and schedule them as
    background posts. Runs via nohup subprocess.
    Logs to /tmp/course_linkedin_scheduler.log
    """
    log.info(f'Scheduling LinkedIn campaign for: {course_name}')

    # Generate posts
    num_posts = posts_per_day * 3  # 3 days worth
    posts = generate_linkedin_questions(course_name, num_posts=num_posts)

    # Write schedule script
    scheduler_script = f"""
import sys, time, asyncio, json, logging
sys.path.insert(0, '{str(LMS_DIR)}')
from course_creator import post_to_linkedin

logging.basicConfig(
    filename='{LOG_FILE}',
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
log = logging.getLogger('scheduler')

posts = {json.dumps(posts)}

log.info(f'Campaign starting: {{len(posts)}} posts, every {interval_hours}h')
for i, post in enumerate(posts):
    log.info(f'Posting {{i+1}}/{{len(posts)}}...')
    result = post_to_linkedin(post)
    log.info(f'Result: {{result}}')
    if i < len(posts) - 1:
        log.info(f'Waiting {interval_hours} hours...')
        time.sleep({interval_hours} * 3600)
log.info('Campaign complete!')
"""

    script_path = '/tmp/linkedin_campaign_runner.py'
    with open(script_path, 'w') as f:
        f.write(scheduler_script)

    # Launch as background process
    venv_python = str(LMS_DIR / 'venv' / 'bin' / 'python')
    cmd = f'nohup {venv_python} {script_path} >> {LOG_FILE} 2>&1 &'
    os.system(cmd)

    result = {
        'status': 'scheduled',
        'course': course_name,
        'posts_count': len(posts),
        'interval_hours': interval_hours,
        'log_file': LOG_FILE,
        'script': script_path,
        'posts_preview': posts[:2],
    }
    log.info(f'Campaign scheduled: {len(posts)} posts every {interval_hours}h')
    return result


# ─────────────────────────────────────────────────────────────
# QUICK PRINT HELPERS
# ─────────────────────────────────────────────────────────────
def print_health_report(report: dict):
    """Pretty-print a health report to terminal."""
    print(f"\n{'='*60}")
    print(f"  COURSE HEALTH REPORT")
    print(f"{'='*60}")
    print(f"  Course:   {report.get('title')}")
    print(f"  ID:       {report.get('course_id')}")
    print(f"  Country:  {report.get('country')}")
    print(f"  Checked:  {report.get('checked_at')}")
    print(f"{'─'*60}")
    t = report.get('totals', {})
    print(f"  Modules:        {t.get('modules', 0)}")
    print(f"  Lessons:        {t.get('lessons', 0)}")
    print(f"  Quizzes:        {t.get('quizzes', 0)}")
    print(f"  Quiz Questions: {t.get('questions', 0)}")
    print(f"  Empty Lessons:  {t.get('empty_lessons', 0)}")
    print(f"  Missing Quizzes:{t.get('modules_without_quiz', 0)} modules")
    print(f"{'─'*60}")
    print(f"  HEALTH SCORE:  {report.get('score')}/100  —  {report.get('grade')}")
    print(f"  ADULT LEARNING: {report.get('adult_learning_score')}/100")
    print(f"  Train-Trainer:  {'✅ Present' if report.get('trainer_pathway_present') else '❌ Missing'}")
    print(f"  Affiliate Hooks:{'✅ Present' if report.get('affiliate_hooks_present') else '❌ Missing'}")
    if report.get('deductions'):
        print(f"{'─'*60}")
        print(f"  DEDUCTIONS:")
        for d in report.get('deductions', []):
            print(f"    • {d}")
    if report.get('issues'):
        print(f"{'─'*60}")
        print(f"  ISSUES:")
        for i in report.get('issues', []):
            print(f"    ⚠ {i}")
    # Per-module details
    print(f"{'─'*60}")
    print(f"  MODULE DETAIL:")
    for m in report.get('modules', []):
        status = '✅' if not m.get('issues') else '⚠'
        print(f"    {status} Module {m.get('id')}: {m.get('title')} "
              f"— {m.get('lesson_count')} lessons, {m.get('quiz_count')} quiz, "
              f"{m.get('question_count')} Qs")
        for issue in m.get('issues', [])[:3]:
            print(f"       └─ {issue}")
    print(f"{'='*60}\n")

