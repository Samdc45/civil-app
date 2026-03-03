from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.colors import HexColor, white
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import os

TEAL = HexColor('#0f766e')
TEAL_LIGHT = HexColor('#14b8a6')
DARK = HexColor('#0f172a')
GREY = HexColor('#334155')
LIGHT = HexColor('#f1f5f9')
GOLD = HexColor('#f59e0b')
W, H = A4

def ps(name, **kw):
    return ParagraphStyle(name, **kw)

def hdr(story, title, sub=None):
    rows = [[Paragraph(title, ps('ht', fontSize=18, textColor=white, fontName='Helvetica-Bold', leading=24, alignment=TA_CENTER))]]
    if sub:
        rows.append([Paragraph(sub, ps('hs', fontSize=10, textColor=TEAL_LIGHT, fontName='Helvetica', leading=14, alignment=TA_CENTER))])
    t = Table(rows, colWidths=[W-4*cm])
    t.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,-1),DARK),
        ('TOPPADDING',(0,0),(-1,-1),12),('BOTTOMPADDING',(0,0),(-1,-1),12),
        ('LEFTPADDING',(0,0),(-1,-1),16),('RIGHTPADDING',(0,0),(-1,-1),16),
    ]))
    story.append(t)
    story.append(Spacer(1,10))

def div(story):
    story.append(HRFlowable(width='100%',thickness=1,color=TEAL_LIGHT,spaceAfter=6,spaceBefore=6))

def body(txt, bold=False, color=None):
    return Paragraph(txt, ps('b', fontSize=10,
        textColor=color or (DARK if bold else GREY),
        fontName='Helvetica-Bold' if bold else 'Helvetica',
        leading=15, spaceAfter=4))

def cat_bar(story, title, color=DARK):
    t = Table([[Paragraph(title, ps('cb', fontSize=10, textColor=white, fontName='Helvetica-Bold', leading=14))]], colWidths=[W-4*cm])
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),color),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),('LEFTPADDING',(0,0),(-1,-1),10)]))
    story.append(t)
    story.append(Spacer(1,4))

def qblock(story, num, question, options):
    story.append(Paragraph(f'Q{num}. {question}', ps('q', fontSize=10, textColor=DARK, fontName='Helvetica-Bold', leading=15, spaceBefore=8, spaceAfter=3)))
    data = []
    for i, opt in enumerate(options):
        score = 4 - i
        data.append([str(score), 'o', opt])
    t = Table(data, colWidths=[0.7*cm, 0.5*cm, W-4*cm-1.2*cm])
    t.setStyle(TableStyle([
        ('FONTNAME',(0,0),(-1,-1),'Helvetica'),('FONTSIZE',(0,0),(-1,-1),9),
        ('TEXTCOLOR',(0,0),(1,-1),TEAL),('TEXTCOLOR',(2,0),(2,-1),GREY),
        ('ROWBACKGROUNDS',(0,0),(-1,-1),[LIGHT,white]),
        ('TOPPADDING',(0,0),(-1,-1),3),('BOTTOMPADDING',(0,0),(-1,-1),3),
        ('LEFTPADDING',(0,0),(0,-1),6),
        ('VALIGN',(0,0),(-1,-1),'TOP'),
    ]))
    story.append(t)

out = '/a0/usr/projects/project_south_consultants/south-lms/static/culture_starter_toolkit.pdf'
os.makedirs(os.path.dirname(out), exist_ok=True)
doc = SimpleDocTemplate(out, pagesize=A4, leftMargin=2*cm, rightMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm,
    title='Culture & Retention Starter Toolkit', author='South Consultants | Sam Dampier-Crossley')
story = []

# === COVER ===
story.append(Spacer(1, 1.5*cm))
cov = Table([
    [Paragraph('CULTURE &amp; RETENTION', ps('ct1', fontSize=28, textColor=white, fontName='Helvetica-Bold', leading=34, alignment=TA_CENTER))],
    [Paragraph('Starter Toolkit', ps('ct2', fontSize=18, textColor=TEAL_LIGHT, fontName='Helvetica', leading=24, alignment=TA_CENTER))],
    [Spacer(1,12)],
    [HRFlowable(width='50%', thickness=1, color=TEAL_LIGHT)],
    [Spacer(1,12)],
    [Paragraph('A self-assessment system for civil construction owners and managers', ps('cs', fontSize=11, textColor=white, fontName='Helvetica-Oblique', leading=16, alignment=TA_CENTER))],
    [Spacer(1,20)],
    [Paragraph('Sam Dampier-Crossley  |  South Consultants  |  New Zealand', ps('ca', fontSize=10, textColor=TEAL_LIGHT, fontName='Helvetica', leading=14, alignment=TA_CENTER))],
    [Paragraph('30 years in civil construction leadership', ps('ca2', fontSize=9, textColor=HexColor('#64748b'), fontName='Helvetica-Oblique', alignment=TA_CENTER))],
], colWidths=[W-4*cm])
cov.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),DARK),('ALIGN',(0,0),(-1,-1),'CENTER'),('TOPPADDING',(0,0),(-1,-1),10),('BOTTOMPADDING',(0,0),(-1,-1),10),('LEFTPADDING',(0,0),(-1,-1),30),('RIGHTPADDING',(0,0),(-1,-1),30)]))
story.append(cov)
story.append(Spacer(1,1*cm))

inside = Table([
    [Paragraph('WHAT IS INSIDE THIS TOOLKIT', ps('wi', fontSize=11, textColor=white, fontName='Helvetica-Bold', alignment=TA_CENTER))],
    [body('✅  20-Question Culture Self-Assessment with scoring guide')],
    [body('✅  Monthly Site Meeting Template — 40-minute format')],
    [body('✅  Annual Growth Review Template — fillable')],
    [body('✅  30-Day Culture Action Plan')],
    [body('✅  Full Culture Development Value Ladder ($10 — $1,000,000+)')],
], colWidths=[W-4*cm])
inside.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),TEAL),('BACKGROUND',(0,1),(-1,-1),LIGHT),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7),('LEFTPADDING',(0,0),(-1,-1),16),('RIGHTPADDING',(0,0),(-1,-1),16)]))
story.append(inside)
story.append(Spacer(1,8))
story.append(Paragraph('www.southconsultants.biz  |  civilbesafe@gmail.com', ps('ft', fontSize=8, textColor=GREY, fontName='Helvetica', alignment=TA_CENTER)))
story.append(PageBreak())

# === INTRO ===
hdr(story, 'Before You Begin', 'A message from Sam')
story.append(body('This toolkit is not about compliance. It is about something harder — whether you actually LEAD the people who work for you, or just manage them.', bold=True))
story.append(Spacer(1,6))
story.append(body('After 30 years on civil construction sites across New Zealand and Australia, I have watched hundreds of crews. The ones that perform best, stay longest, and have the fewest incidents all share one thing: the boss knows their people.'))
story.append(body('Not just names on a timesheet. Their goals. Their families. What lights them up. What worries them at 2am.'))
div(story)
cost = Table([
    [Paragraph('The Cost of Poor Culture', ps('ch', fontSize=10, textColor=white, fontName='Helvetica-Bold')), Paragraph('Real Impact', ps('ch', fontSize=10, textColor=white, fontName='Helvetica-Bold'))],
    ['Replacing a skilled operator', '$15,000 – $40,000 NZD'],
    ['Lost productivity during handover', '3 – 6 months'],
    ['Incident rate in low-trust teams', '3x higher'],
    ['Productivity gap: engaged vs disengaged', 'Up to 21%'],
], colWidths=[10*cm, 7*cm])
cost.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),TEAL),('TEXTCOLOR',(0,0),(-1,0),white),('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('FONTNAME',(0,1),(-1,-1),'Helvetica'),('FONTSIZE',(0,0),(-1,-1),10),('TEXTCOLOR',(0,1),(-1,-1),GREY),('ROWBACKGROUNDS',(0,1),(-1,-1),[LIGHT,white]),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),('LEFTPADDING',(0,0),(-1,-1),10),('GRID',(0,0),(-1,-1),0.5,HexColor('#e2e8f0'))]))
story.append(cost)
story.append(Spacer(1,10))
qt = Table([[Paragraph('"Train to replace yourself — then train them to replace themselves. That is how you build something that lasts."  — Sam Dampier-Crossley', ps('qt', fontSize=11, textColor=white, fontName='Helvetica-Oblique', leading=16, alignment=TA_CENTER))]], colWidths=[W-4*cm])
qt.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),TEAL),('TOPPADDING',(0,0),(-1,-1),14),('BOTTOMPADDING',(0,0),(-1,-1),14),('LEFTPADDING',(0,0),(-1,-1),20),('RIGHTPADDING',(0,0),(-1,-1),20)]))
story.append(qt)
story.append(PageBreak())

# === ASSESSMENT ===
hdr(story, '20-Question Culture Self-Assessment', 'Score: 4=Always  3=Usually  2=Occasionally  1=Never')
story.append(body('Answer honestly. No one is watching. Your score reveals your gaps.'))
story.append(Spacer(1,6))

cat_bar(story, 'PART A — KNOWING YOUR PEOPLE  (Q1–5)')
qblock(story,1,'Can you name every team member — first AND last name — without checking a list?',['Yes, every single one','Most — maybe miss 1 or 2','Permanent staff yes, casuals I would struggle','No — I would need to check'])
qblock(story,2,'Do you know at least ONE thing about each person\'s life outside work?',['Yes — family, hobbies, or personal goals for everyone','Some of them yes','Just the ones I have worked with a long time','Not really — I keep work and personal separate'])
qblock(story,3,'Do you know — within 3 months — how long each person has worked for you?',['Yes, I track and acknowledge work anniversaries','Roughly for most people','I know for core team, not for others','Not at all — I would have to check records'])
qblock(story,4,'Do you know what each person wants to be doing in 3 years?',['Yes — we have talked about their goals directly','For a few key people yes','I assume they want to keep doing what they do now','I have never asked'])
qblock(story,5,'Do you know what is causing stress for your people right now?',['Yes — I check in regularly and people tell me','I have a sense for some of them','Occasionally if it becomes obvious','I generally do not know until it becomes a problem'])

cat_bar(story, 'PART B — TRAINING & DEVELOPMENT  (Q6–10)')
qblock(story,6,'Do you know when each person last completed formal training or upskilling?',['Yes — I track this and plan ahead','Roughly for most','I know about compliance-required tickets only','No — training happens reactively'])
qblock(story,7,'Does each person have at least one training or development goal for this year?',['Yes — planned and agreed with each person','Some do, others not specifically','We plan only when tickets expire or compliance requires','No formal development planning at all'])
qblock(story,8,'When did you last take your team to a field day, demo, or industry event?',['Within the last 6 months','Within the last year','A few years ago','Never or I cannot remember'])
qblock(story,9,'Have you supported a team member to attend personal development outside of technical training?',['Yes — leadership, financial literacy, health, or similar','I would consider it if they asked','Not specifically — we focus on job-related training only','No — that is their own responsibility'])
qblock(story,10,'Do you know every current ticket, certificate and licence your team holds — and when they expire?',['Yes — I have a current register and check it','Mostly — I check when it becomes relevant','I rely on team members to tell me','Not in detail — it is not well tracked'])
story.append(PageBreak())

cat_bar(story, 'PART C — RECOGNITION & BELONGING  (Q11–15)')
qblock(story,11,'Did you give a specific, personal thank you to someone on your crew THIS WEEK?',['Yes — I do this regularly every week','This month yes, not necessarily every week','Occasionally when something really stands out','I cannot remember the last time I did it specifically'])
qblock(story,12,'When did you last acknowledge a personal or professional milestone for someone on your team?',['Recently — anniversaries, personal wins, certificates','Occasionally when I remember','At Christmas functions mostly','I do not typically acknowledge milestones'])
qblock(story,13,'Can the newest person on your site comfortably raise a concern without fear of judgment?',['Yes — we have built that trust deliberately','I believe so, though I cannot be certain','Probably for major safety issues but not everyday concerns','I am not sure — it has never been tested'])
qblock(story,14,'Do you know the REAL reason why people have left your business in the last 3 years?',['Yes — I have had honest exit conversations','I think so, though they may not have said everything','They said it was money — I took that at face value','I have not looked into the real reasons'])
qblock(story,15,'Have you directly asked your longest-serving person why they have stayed?',['Yes — I know their real reasons','Not directly but I think I know','No — it has not come up','No — I have never thought to ask'])

cat_bar(story, 'PART D — THE COACHING CHALLENGE  (Q16–20)')
qblock(story,16,'When did you last have a genuine one-on-one with each direct report — not about tasks, but about them?',['This month — I do this consistently','Every few months','Occasionally when prompted by a problem','I do not have structured one-on-ones'])
qblock(story,17,'Could your business run at full quality for 3 months without you on site?',['Yes — I have people ready to step up','Mostly, with some daily contact from me','It would struggle significantly','No — it depends almost entirely on me'])
qblock(story,18,'Do you regularly walk the site WITH your people — not to inspect, but to listen and observe?',['Yes — daily walk-arounds are part of how I lead','Occasionally when I have time','Rarely — I am usually too focused on tasks','No — my role keeps me away from that'])
qblock(story,19,'Have you talked to your team about where the industry is heading in 5 years?',['Yes — we discuss future tech and career readiness','Informally here and there','Not specifically — we focus on current work','No — the future has not been a topic we cover'])
qblock(story,20,'If you asked your team to describe site culture in 3 words — would their answer match yours?',['Yes — I am confident it would closely match','Mostly — there might be small differences','Probably not — we likely see it differently','I have no idea what they would say'])
story.append(PageBreak())

# === SCORING ===
hdr(story, 'Your Culture Score', 'Add up your scores from all 20 questions')
score = Table([
    [Paragraph('Score', ps('sh', fontSize=10, textColor=white, fontName='Helvetica-Bold')), Paragraph('Culture Stage', ps('sh', fontSize=10, textColor=white, fontName='Helvetica-Bold')), Paragraph('What It Means', ps('sh', fontSize=10, textColor=white, fontName='Helvetica-Bold'))],
    ['70 – 80', '🏆 Culture Leader', 'You are doing the hard work. Systemise it so it does not depend on you alone.'],
    ['55 – 69', '🔨 Culture Builder', 'Strong foundations with clear gaps. Build a 30-day plan around your 3 lowest scores.'],
    ['40 – 54', '🌱 Culture Aware', 'You understand the importance but it is not consistent practice. Start with one habit this week.'],
    ['20 – 39', '⚠️ Culture at Risk', 'High turnover and low engagement risk. Your team is telling you something — even if not in words.'],
], colWidths=[2.5*cm, 4*cm, 10.5*cm])
score.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),TEAL),('TEXTCOLOR',(0,0),(-1,0),white),('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('FONTNAME',(0,1),(-1,-1),'Helvetica'),('FONTSIZE',(0,0),(-1,-1),9),('TEXTCOLOR',(0,1),(-1,-1),GREY),('FONTNAME',(0,1),(0,-1),'Helvetica-Bold'),('TEXTCOLOR',(0,1),(0,-1),TEAL),('ROWBACKGROUNDS',(0,1),(-1,-1),[LIGHT,white]),('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),8),('LEFTPADDING',(0,0),(-1,-1),8),('VALIGN',(0,0),(-1,-1),'TOP'),('GRID',(0,0),(-1,-1),0.5,HexColor('#e2e8f0'))]))
story.append(score)
story.append(Spacer(1,12))
story.append(body('MY TOTAL SCORE: _____ / 80', bold=True))
story.append(Spacer(1,6))
story.append(body('MY CULTURE STAGE: _______________________________________', bold=True))
story.append(Spacer(1,10))
story.append(body('MY TOP 3 GAPS TO WORK ON:', bold=True))
gaps = Table([['1.', ''],['2.', ''],['3.', '']], colWidths=[0.8*cm, W-4*cm-0.8*cm])
gaps.setStyle(TableStyle([('FONTNAME',(0,0),(-1,-1),'Helvetica-Bold'),('TEXTCOLOR',(0,0),(0,-1),TEAL),('FONTSIZE',(0,0),(-1,-1),11),('LINEBELOW',(1,0),(1,-1),1,HexColor('#e2e8f0')),('TOPPADDING',(0,0),(-1,-1),10),('BOTTOMPADDING',(0,0),(-1,-1),10)]))
story.append(gaps)
story.append(PageBreak())

# === MONTHLY MEETING ===
hdr(story, 'Monthly Site Meeting Template', '40 minutes. 5 elements. Every month. Non-negotiable.')
story.append(body('A great monthly site meeting builds team — not just shares information. Copy this template. Run it every month.'))
story.append(Spacer(1,8))
fields = [('Date',''),('Location',''),('Team Present',''),('Facilitated by','')]
ft = Table([[body(f+':',bold=True), body('_'*50)] for f,_ in fields], colWidths=[4*cm, W-4*cm-4*cm])
ft.setStyle(TableStyle([('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]))
story.append(ft)
div(story)

sects = [
    ('1. RECOGNITION — 5 min','Name someone who did something worth recognising this month. Be specific. Say it in front of the team.'),
    ('2. WHAT IS WORKING — 10 min','Open question: What has gone well? What are we proud of this month?'),
    ('3. WHAT NEEDS ATTENTION — 10 min','No blame. No hierarchy. Honest: what could be better? What is slowing us down?'),
    ('4. LEARNING MOMENT — 10 min','Industry news, new equipment, field day recap, or course completed. One person shares something they learned.'),
    ('5. INDIVIDUAL SHOUTOUT — 5 min','Name one person. Say something specific about who they are as part of this team — not just what they did.'),
]
for title, desc in sects:
    st = Table([[Paragraph(title, ps('st', fontSize=10, textColor=white, fontName='Helvetica-Bold', leading=14))]], colWidths=[W-4*cm])
    st.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),TEAL),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5),('LEFTPADDING',(0,0),(-1,-1),10)]))
    story.append(st)
    story.append(Paragraph(desc, ps('sd', fontSize=9, textColor=GREY, fontName='Helvetica', leading=13, spaceBefore=3)))
    ln = Table([['_'*110],['_'*110]], colWidths=[W-4*cm])
    ln.setStyle(TableStyle([('FONTSIZE',(0,0),(-1,-1),8),('TEXTCOLOR',(0,0),(-1,-1),TEAL_LIGHT),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]))
    story.append(ln)
    story.append(Spacer(1,4))
story.append(Spacer(1,6))
story.append(body('Next meeting: ___________________________  |  Signed: ___________________________', bold=True))
story.append(PageBreak())

# === ANNUAL GROWTH REVIEW ===
hdr(story, 'Annual Growth Review', 'Not a performance review — a growth conversation.')
story.append(body('Schedule once per year for every team member. Send Part 2 questions ONE WEEK before the meeting so they can reflect honestly.', bold=True))
story.append(Spacer(1,8))
afields = [('Employee Name',''),('Role',''),('Start Date',''),('Years with us',''),('Review Date',''),('Conducted by','')]
aft = Table([[body(f+':',bold=True), body('_'*45)] for f,_ in afields], colWidths=[4*cm, W-4*cm-4*cm])
aft.setStyle(TableStyle([('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]))
story.append(aft)
div(story)

parts = [
    ('PART 1 — LOOKING BACK', DARK, [
        'What are you most proud of from the past 12 months?',
        'What did you find most challenging?',
        'Manager acknowledgment — what I noticed and want to thank you for specifically:',
    ]),
    ('PART 2 — LOOKING FORWARD  (Send these questions one week before)', TEAL, [
        'What would you like to learn or develop in the next 12 months?',
        'Is there a role, responsibility, or project you would like to take on?',
        'Where do you see yourself in 3 years?',
    ]),
    ('PART 3 — WHAT WOULD MAKE THIS A GREAT YEAR', DARK, [
        'What is one thing that would make coming to work better for you?',
        'Is there anything you wish I knew — or wish we talked about more?',
        'What would make this year a great year for you here?',
    ]),
]
for ptitle, pcolor, qs in parts:
    ph = Table([[Paragraph(ptitle, ps('ph', fontSize=10, textColor=white, fontName='Helvetica-Bold', leading=14))]], colWidths=[W-4*cm])
    ph.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),pcolor),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),('LEFTPADDING',(0,0),(-1,-1),10)]))
    story.append(ph)
    story.append(Spacer(1,4))
    for q in qs:
        story.append(body(q, bold=True))
        ql = Table([['_'*110],['_'*110]], colWidths=[W-4*cm])
        ql.setStyle(TableStyle([('FONTSIZE',(0,0),(-1,-1),8),('TEXTCOLOR',(0,0),(-1,-1),TEAL_LIGHT),('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4)]))
        story.append(ql)
    story.append(Spacer(1,6))

ch = Table([[Paragraph('PART 4 — COMMITMENTS', ps('ph', fontSize=10, textColor=white, fontName='Helvetica-Bold', leading=14))]], colWidths=[W-4*cm])
ch.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),TEAL),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),('LEFTPADDING',(0,0),(-1,-1),10)]))
story.append(ch)
story.append(Spacer(1,6))
comm = Table([
    [Paragraph('What', ps('ch2', fontSize=9, textColor=white, fontName='Helvetica-Bold')), Paragraph('Who', ps('ch2', fontSize=9, textColor=white, fontName='Helvetica-Bold')), Paragraph('By When', ps('ch2', fontSize=9, textColor=white, fontName='Helvetica-Bold'))],
    ['','',''],['','',''],['','',''],
], colWidths=[9*cm, 4*cm, 4*cm])
comm.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),TEAL),('GRID',(0,0),(-1,-1),0.5,HexColor('#e2e8f0')),('ROWBACKGROUNDS',(0,1),(-1,-1),[LIGHT,white]),('TOPPADDING',(0,0),(-1,-1),12),('BOTTOMPADDING',(0,0),(-1,-1),12),('LEFTPADDING',(0,0),(-1,-1),8)]))
story.append(comm)
story.append(Spacer(1,8))
story.append(body('Golden Rule: Whatever you commit to in this conversation — do it. Every broken promise costs 6 months of trust.', bold=True, color=TEAL))
story.append(Spacer(1,8))
sign = Table([['Employee signature: ___________________________  Date: ____________'],['Manager signature: ___________________________    Date: ____________']], colWidths=[W-4*cm])
sign.setStyle(TableStyle([('FONTNAME',(0,0),(-1,-1),'Helvetica'),('FONTSIZE',(0,0),(-1,-1),10),('TEXTCOLOR',(0,0),(-1,-1),DARK),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]))
story.append(sign)
story.append(PageBreak())

# === 30-DAY PLAN ===
hdr(story, '30-Day Culture Action Plan', 'One action per week. Do it. Then pick the next one.')
weeks = [
    ('WEEK 1: KNOW YOUR PEOPLE', TEAL, [
        'Write every team member name, role, one outside-work fact — from memory. Note the gaps.',
        'Have one conversation this week to fill a gap you found.',
        'Find your longest-serving person\'s exact start date. Acknowledge it this week.',
    ]),
    ('WEEK 2: RECOGNITION & CONNECTION', DARK, [
        'Give one specific, personal thank you each day for 5 working days.',
        'At your next toolbox talk — name someone who did something good this week.',
        'Ask one team member: what is one thing that would make your job better?',
    ]),
    ('WEEK 3: LEARNING & DEVELOPMENT', TEAL, [
        'List every team member\'s last formal training date and current tickets.',
        'Identify one person ready for a new ticket or development opportunity.',
        'Research one field day, demo, or industry event for the team this year.',
    ]),
    ('WEEK 4: SYSTEMS & STRUCTURE', DARK, [
        'Schedule monthly site meetings for the next 12 months. Lock them in.',
        'Book Annual Growth Conversations — one per team member, one per week.',
        'Send each team member their pre-meeting reflection questions.',
    ]),
]
for wtitle, wcolor, actions in weeks:
    wh = Table([[Paragraph(wtitle, ps('wh', fontSize=10, textColor=white, fontName='Helvetica-Bold', leading=14))]], colWidths=[W-4*cm])
    wh.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),wcolor),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7),('LEFTPADDING',(0,0),(-1,-1),10)]))
    story.append(wh)
    for action in actions:
        at = Table([['☐', Paragraph(action, ps('at', fontSize=10, textColor=GREY, fontName='Helvetica', leading=14))]], colWidths=[0.8*cm, W-4*cm-0.8*cm])
        at.setStyle(TableStyle([('FONTSIZE',(0,0),(0,-1),12),('TEXTCOLOR',(0,0),(0,-1),TEAL),('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]))
        story.append(at)
    story.append(Spacer(1,6))
div(story)
story.append(body('THE ONE QUESTION: At the end of every week, ask yourself — did anyone come to me with a problem they did not have to bring? If yes: you are becoming more approachable. If no: keep going.', bold=True))
story.append(PageBreak())

# === VALUE LADDER ===
hdr(story, 'Your Culture Development Journey', 'From starter toolkit to full transformation')
story.append(body('This toolkit is the beginning of a complete culture development pathway for civil construction businesses.'))
story.append(Spacer(1,10))

ladder = [
    ('$10', 'Culture Starter Toolkit', 'The PDF you are holding. Self-assessment, templates, 30-day plan. Immediate value.', TEAL_LIGHT, DARK),
    ('$97', 'Full Online Course + Certificate', '5-module online course with quizzes and a digital completion certificate. Share with your leadership team.', TEAL, white),
    ('$497', 'Team Culture Pack', 'Full course access for up to 5 staff. Ideal for site managers and supervisors. Includes team dashboard.', HexColor('#0d9488'), white),
    ('$997', 'Culture Audit + Personal Feedback', 'Submit your completed assessment to Sam. Receive a personalised written report with your top 5 gaps and a custom 90-day plan.', HexColor('#0f766e'), white),
    ('$2,997', 'Half-Day Culture Workshop', 'Virtual or in-person half-day with Sam for your leadership team. Live assessment review, team debrief, 12-month roadmap.', DARK, white),
    ('$9,997', '12-Month Transformation Program', 'Quarterly check-ins, monthly culture health reports, custom training calendar, and full team engagement tracking.', DARK, white),
    ('$50,000+', 'Enterprise Culture Advisory', 'Ongoing retainer for large organisations. Culture design, leadership development, retention strategy, and executive coaching.', DARK, GOLD),
    ('$1,000,000+', 'System Licensing Rights', 'License the South Consultants Culture System for use in your training organisation, franchise, or national rollout.', DARK, GOLD),
]
for price, title, desc, bg, fg in ladder:
    row = Table([[
        Paragraph(price, ps('lp', fontSize=14, textColor=white if fg==white else GOLD, fontName='Helvetica-Bold', leading=18, alignment=TA_CENTER)),
        Paragraph(f'<b>{title}</b><br/><font size=9>{desc}</font>', ps('ld', fontSize=10, textColor=fg, fontName='Helvetica', leading=14)),
    ]], colWidths=[2.8*cm, W-4*cm-2.8*cm])
    row.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),bg),('TOPPADDING',(0,0),(-1,-1),10),('BOTTOMPADDING',(0,0),(-1,-1),10),('LEFTPADDING',(0,0),(-1,-1),10),('RIGHTPADDING',(0,0),(-1,-1),10),('VALIGN',(0,0),(-1,-1),'MIDDLE')]))
    story.append(row)
    story.append(Spacer(1,3))

story.append(Spacer(1,12))
cta = Table([[Paragraph('Ready to take the next step?  Visit www.southconsultants.biz or email civilbesafe@gmail.com — mention this toolkit and Sam will personally respond within 24 hours.', ps('cta', fontSize=11, textColor=white, fontName='Helvetica-Bold', leading=18, alignment=TA_CENTER))]], colWidths=[W-4*cm])
cta.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),TEAL),('TOPPADDING',(0,0),(-1,-1),16),('BOTTOMPADDING',(0,0),(-1,-1),16),('LEFTPADDING',(0,0),(-1,-1),20),('RIGHTPADDING',(0,0),(-1,-1),20)]))
story.append(cta)
story.append(Spacer(1,10))
story.append(Paragraph('© 2026 South Consultants Limited  |  Sam Dampier-Crossley  |  www.southconsultants.biz', ps('ft', fontSize=8, textColor=GREY, fontName='Helvetica', alignment=TA_CENTER)))
story.append(Paragraph('This document is for personal and professional development use only. Not for resale or redistribution.', ps('ft2', fontSize=8, textColor=GREY, fontName='Helvetica', alignment=TA_CENTER)))

doc.build(story)
import os
size = os.path.getsize(out)
print(f'PDF BUILT: {out}')
print(f'Size: {size:,} bytes ({size//1024} KB)')
print('DONE')
