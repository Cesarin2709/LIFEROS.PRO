from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import create_engine, Column, Integer, String, Float, Text
from sqlalchemy.orm import sessionmaker, declarative_base, Session
import random
import html as html_tools
from datetime import date
import os

app = FastAPI()

# ✅ CAMBIO CLAVE: base de datos en /data para que persista en Fly.io
DATABASE_URL = "sqlite:////data/lifeos_pro_v1.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ----------------------
# MODELS
# ----------------------

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    email = Column(String)

class Habit(Base):
    __tablename__ = "habits"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    date = Column(String, default="")
    time = Column(String, default="")
    status = Column(String, default="Pendiente")

class Expense(Base):
    __tablename__ = "expenses"
    id = Column(Integer, primary_key=True)
    category = Column(String)
    amount = Column(Float)

class Journal(Base):
    __tablename__ = "journal"
    id = Column(Integer, primary_key=True)
    entry = Column(Text)

class Budget(Base):
    __tablename__ = "budget"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    amount = Column(Float, default=0.0)

class EmotionalLog(Base):
    __tablename__ = "emotional_log"
    id = Column(Integer, primary_key=True)
    status = Column(String)
    reason = Column(String)
    action = Column(String)

Base.metadata.create_all(bind=engine)

# ----------------------
# AI ENGINE
# ----------------------

def recommend_scripture():
    verses = [
        "Mosíah 2:17 - Cuando os halláis al servicio de vuestros semejantes, solo estáis al servicio de vuestro Dios",
        "Alma 37:6 - Por medio de cosas pequeñas y sencillas se realizan grandes cosas",
        "Moroni 7:45 - La caridad es el amor puro de Cristo",
        "Proverbios 3:5 - Confía en Jehová con todo tu corazón"
    ]
    return random.choice(verses)

def recommend_habit():
    habits = [
        "Hacer ejercicio 20 minutos",
        "Leer las escrituras",
        "Escribir en el diario de gratitud",
        "Servir a alguien hoy",
        "Planificar tu día"
    ]
    return random.choice(habits)

# ----------------------
# HTML TEMPLATE
# ----------------------

def dashboard_html(content, request: Request):
    path = request.url.path
    finanzas_display = "block" if path in ["/finances", "/pasajes", "/comida"] else "none"

    return f"""
    <html>
    <head>
    <title>liferos.pro</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script>
    function toggle(id) {{
        var x = document.getElementById(id);
        if (x.style.display === "none") {{
            x.style.display = "block";
        }} else {{
            x.style.display = "none";
        }}
    }}
    </script>
    <style>
    body {{ margin:0; font-family:Arial; display:flex; }}
    .sidebar {{ width:220px; background:#111; color:white; height:100vh; padding:20px; }}
    .sidebar a {{ display:block; color:white; padding:10px; text-decoration:none; }}
    .sidebar a:hover {{ background:#333; }}
    .content {{ flex:1; padding:40px; }}
    input,button {{ padding:10px; margin:5px; }}
    @media (max-width: 768px) {{
        body {{ flex-direction: column; }}
        .sidebar {{ width: auto; height: auto; }}
    }}
    </style>
    </head>
    <body>
    <div class="sidebar">
    <h2>liferos.pro</h2>
    <a href="/">Inicio</a>
    <a href="/habits">Hábitos</a>
    <div style="display:flex; align-items:center;">
        <a href="/finances" style="flex-grow:1;">Finanzas</a>
        <button onclick="toggle('sub-finanzas')" style="background:none; border:none; color:white; cursor:pointer; font-size:1.2em; padding:0 10px;">▼</button>
    </div>
    <div id="sub-finanzas" style="display:{finanzas_display}; background:#222; margin-left:10px; border-left:2px solid #4CAF50;">
        <a href="/pasajes" style="font-size:0.9em;">🚌 Pasajes</a>
        <a href="/comida" style="font-size:0.9em;">🍔 Comida</a>
    </div>
    <a href="/journal">Diario</a>
    <a href="/emotional">Emocionalmente</a>
    <a href="/ai">Coach IA</a>
    </div>
    <div class="content">
    {content}
    </div>
    </body>
    </html>
    """

# ----------------------
# DASHBOARD
# ----------------------

@app.get("/", response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(get_db)):
    today_str = date.today().isoformat()
    habits_today = db.query(Habit).filter(Habit.date == today_str).count()
    pending_today = db.query(Habit).filter(Habit.date == today_str, Habit.status == "Pendiente").count()
    expenses = db.query(Expense).count()
    journals = db.query(Journal).count()

    content = f"""
    <h1>Tablero Principal</h1>
    <div style="background:#e8f5e9; padding:15px; border-radius:8px; border:1px solid #4CAF50; margin-bottom:20px;">
        <h3 style="margin-top:0; color:#2E7D32;">📅 Resumen de Hoy</h3>
        <p style="font-size:1.1em;">Tienes <b>{pending_today}</b> hábitos pendientes de {habits_today} programados.</p>
        <a href="/habits" style="background:#4CAF50; color:white; padding:8px 15px; text-decoration:none; border-radius:5px; display:inline-block;">Ir a Hábitos</a>
    </div>
    <p><b>Gastos registrados:</b> {expenses}</p>
    <p><b>Entradas de diario:</b> {journals}</p>
    """
    return dashboard_html(content, request=request)

# ----------------------
# HABITS
# ----------------------

@app.get("/habits", response_class=HTMLResponse)
def habits(request: Request, db: Session = Depends(get_db)):
    habits_list = db.query(Habit).order_by(Habit.date, Habit.time).all()
    today_str = date.today().isoformat()
    todays_habits = [h for h in habits_list if h.date == today_str]
    total_today = len(todays_habits)
    completed_today = len([h for h in todays_habits if h.status == "Cumplida"])
    progress_pct = int((completed_today / total_today) * 100) if total_today > 0 else 0

    html = "<h1>Hábitos</h1>"
    html += f"""
    <div style="margin-bottom:20px; background:white; padding:15px; border-radius:8px; border:1px solid #ddd;">
        <div style="display:flex; justify-content:space-between; margin-bottom:5px;">
            <b>🚀 Progreso de Hoy</b>
            <span>{progress_pct}% ({completed_today}/{total_today})</span>
        </div>
        <div style="background:#eee; border-radius:10px; height:20px; width:100%;">
            <div style="background:#4CAF50; height:100%; border-radius:10px; width:{progress_pct}%; transition:width 0.3s;"></div>
        </div>
    </div>
    """

    calendar_url = "https://calendar.google.com/calendar/embed?src=cesarvillegas2709%40gmail.com&ctz=America%2FLima"
    html += f"""
    <button onclick="toggle('calendar-frame')" style="background:#2196F3; color:white; border:none; width:100%; text-align:left; padding:10px; cursor:pointer;">📅 Mostrar/Ocultar Calendario</button>
    <div id="calendar-frame" style="display:none; margin-top:10px; margin-bottom:20px;">
    <iframe src="{calendar_url}" style="border: 0" width="100%" height="500" frameborder="0" scrolling="no"></iframe>
    </div>
    """

    html += """
    <form method="post" style="background:#eee; padding:15px; border-radius:8px; margin-bottom:20px; display:flex; gap:10px; flex-wrap:wrap; align-items:center;">
        <input name="name" placeholder="Hábito (ej. Ejercicio)" required style="flex-grow:1;">
        <input type="date" name="date" required>
        <input type="time" name="time" required>
        <button style="background:#4CAF50; color:white; border:none;">Programar</button>
    </form>
    """

    for h in habits_list:
        color_status = "#999"
        if h.status == "Cumplida": color_status = "green"
        if h.status == "Pospuesta": color_status = "orange"

        html += f"""
        <div style="border:1px solid #ddd; padding:10px; border-radius:5px; margin-bottom:10px; display:flex; justify-content:space-between; align-items:center; background:white;">
            <div>
                <div style="font-weight:bold; font-size:1.1em;">{html_tools.escape(h.name)}</div>
                <div style="font-size:0.9em; color:#555;">📅 {h.date} | ⏰ {h.time}</div>
                <div style="font-size:0.8em; color:{color_status}; font-weight:bold;">Estado: {h.status}</div>
            </div>
            <div style="display:flex; gap:5px;">
                <form action="/habits/{h.id}/status" method="post" style="margin:0;">
                    <input type="hidden" name="action" value="complete">
                    <button title="Cumplida" style="background:#4CAF50; color:white; border:none; cursor:pointer;">✅</button>
                </form>
                <form action="/habits/{h.id}/status" method="post" style="margin:0;">
                    <input type="hidden" name="action" value="postpone">
                    <button title="Posponer" style="background:#FF9800; color:white; border:none; cursor:pointer;">⏭️</button>
                </form>
                <form action="/habits/{h.id}/status" method="post" style="margin:0;">
                    <input type="hidden" name="action" value="delete">
                    <button title="Eliminar" style="background:#f44336; color:white; border:none; cursor:pointer;">🗑️</button>
                </form>
            </div>
        </div>
        """
    return dashboard_html(html, request=request)

@app.post("/habits")
def add_habit(name: str = Form(...), date: str = Form(default=""), time: str = Form(default=""), db: Session = Depends(get_db)):
    habit = Habit(name=name, date=date, time=time, status="Pendiente")
    db.add(habit)
    db.commit()
    return RedirectResponse("/habits", status_code=303)

@app.post("/habits/{habit_id}/status")
def update_habit_status(habit_id: int, action: str = Form(...), db: Session = Depends(get_db)):
    habit = db.query(Habit).filter(Habit.id == habit_id).first()
    if habit:
        if action == "complete":
            habit.status = "Cumplida"
        elif action == "postpone":
            habit.status = "Pospuesta"
        elif action == "delete":
            db.delete(habit)
        db.commit()
    return RedirectResponse("/habits", status_code=303)

# ----------------------
# FINANCES
# ----------------------

@app.get("/finances", response_class=HTMLResponse)
def finances(request: Request, db: Session = Depends(get_db)):
    cesar = db.query(Budget).filter(Budget.name == "Cesar").first()
    rosita = db.query(Budget).filter(Budget.name == "Rosita").first()
    ingreso_cesar = cesar.amount if cesar else 0.0
    ingreso_rosita = rosita.amount if rosita else 0.0
    total_ingresos = ingreso_cesar + ingreso_rosita
    diez_porciento = total_ingresos * 0.10
    expenses = db.query(Expense).all()
    total_pasajes = sum(e.amount for e in expenses if (e.category or "").startswith("Pasajes"))
    total_comida = sum(e.amount for e in expenses if (e.category or "").startswith("Comida"))
    total_otros = sum(e.amount for e in expenses if not (e.category or "").startswith("Pasajes") and not (e.category or "").startswith("Comida"))
    saldo_final = total_ingresos - diez_porciento - total_pasajes - total_comida - total_otros

    html = "<h1>Finanzas</h1>"
    html += f"""
    <div style="border:1px solid #ccc; padding:10px; border-radius:8px; margin-bottom:15px;">
        <h3 style="margin-top:0;">💰 Presupuesto</h3>
        <form action="/finances/budget" method="post" style="display:flex; gap:5px; align-items:center; flex-wrap:wrap; margin-bottom:5px;">
            <input name="cesar" type="number" step="0.01" value="{ingreso_cesar}" placeholder="César" style="width:90px; padding:5px;">
            <input name="rosita" type="number" step="0.01" value="{ingreso_rosita}" placeholder="Rosita" style="width:90px; padding:5px;">
            <button style="background:#4CAF50; color:white; border:none; padding:5px 10px;">Guardar</button>
        </form>
        <div style="font-size:0.9em;">
            <span><b>Total:</b> S/.{total_ingresos:,.2f}</span> | 
            <span><b>10%:</b> S/.{diez_porciento:,.2f}</span>
        </div>
    </div>
    <div style="background:#f4f4f4; padding:15px; border-radius:8px; margin-bottom:20px;">
        <h3>Resumen por Categoría</h3>
        <p>🚌 <b>Total Pasajes:</b> S/.{total_pasajes:,.2f} (<a href="/pasajes" style="color:#1E88E5;">ver detalle</a>)</p>
        <p>🍔 <b>Total Comida:</b> S/.{total_comida:,.2f} (<a href="/comida" style="color:#1E88E5;">ver detalle</a>)</p>
        <p>📝 <b>Saldo disponible:</b> S/.{saldo_final:,.2f}</p>
    </div>
    """
    return dashboard_html(html, request=request)

@app.post("/finances")
def add_expense(category: str = Form(...), amount: float = Form(...), db: Session = Depends(get_db)):
    expense = Expense(category=category, amount=amount)
    db.add(expense)
    db.commit()
    return RedirectResponse("/finances", status_code=303)

@app.post("/finances/budget")
def update_budget(cesar: float = Form(...), rosita: float = Form(...), db: Session = Depends(get_db)):
    b_cesar = db.query(Budget).filter(Budget.name == "Cesar").first()
    if not b_cesar:
        b_cesar = Budget(name="Cesar")
        db.add(b_cesar)
    b_cesar.amount = cesar
    b_rosita = db.query(Budget).filter(Budget.name == "Rosita").first()
    if not b_rosita:
        b_rosita = Budget(name="Rosita")
        db.add(b_rosita)
    b_rosita.amount = rosita
    db.commit()
    return RedirectResponse("/finances", status_code=303)

# ----------------------
# PASAJES
# ----------------------

@app.get("/pasajes", response_class=HTMLResponse)
def pasajes(request: Request, db: Session = Depends(get_db)):
    expenses = db.query(Expense).filter(Expense.category.like("Pasajes%")).all()
    html = "<h1>🚌 Pasajes</h1>"
    html += """
    <form method="post">
    <input name="description" placeholder="Descripción (ej. Bus, Taxi)">
    <input name="amount" placeholder="Monto" type="number" step="0.01">
    <button>Agregar Pasaje</button>
    </form>
    """
    total = 0
    for e in expenses:
        display_name = e.category.replace("Pasajes: ", "")
        html += f"<div style='background:#4CAF50; color:white; padding:10px; border-radius:5px; margin-bottom:10px;'>{html_tools.escape(display_name)} - S/.{e.amount}</div>"
        total += e.amount
    html += f"<h3>Total Pasajes: S/.{total}</h3>"
    return dashboard_html(html, request=request)

@app.post("/pasajes")
def add_pasaje(description: str = Form(...), amount: float = Form(...), db: Session = Depends(get_db)):
    expense = Expense(category=f"Pasajes: {description}", amount=amount)
    db.add(expense)
    db.commit()
    return RedirectResponse("/pasajes", status_code=303)

# ----------------------
# COMIDA
# ----------------------

@app.get("/comida", response_class=HTMLResponse)
def comida(request: Request, db: Session = Depends(get_db)):
    expenses = db.query(Expense).filter(Expense.category.like("Comida%")).all()
    html = "<h1>🍔 Comida</h1>"
    html += """
    <form method="post">
    <input name="description" placeholder="Descripción (ej. Almuerzo, Super)">
    <input name="amount" placeholder="Monto" type="number" step="0.01">
    <button>Agregar Comida</button>
    </form>
    """
    total = 0
    for e in expenses:
        display_name = e.category.replace("Comida: ", "")
        html += f"<div style='background:#4CAF50; color:white; padding:10px; border-radius:5px; margin-bottom:10px;'>{html_tools.escape(display_name)} - S/.{e.amount}</div>"
        total += e.amount
    html += f"<h3>Total Comida: S/.{total}</h3>"
    return dashboard_html(html, request=request)

@app.post("/comida")
def add_comida(description: str = Form(...), amount: float = Form(...), db: Session = Depends(get_db)):
    expense = Expense(category=f"Comida: {description}", amount=amount)
    db.add(expense)
    db.commit()
    return RedirectResponse("/comida", status_code=303)

# ----------------------
# JOURNAL
# ----------------------

@app.get("/journal", response_class=HTMLResponse)
def journal(request: Request, db: Session = Depends(get_db)):
    entries = db.query(Journal).all()
    html = "<h1>Diario</h1>"
    html += """
    <form method="post">
    <input name="entry" placeholder="Escribe algo..." style="width:60%;">
    <button>Guardar</button>
    </form>
    """
    for e in entries:
        html += f"<div style='background:#4CAF50; color:white; padding:10px; border-radius:5px; margin-bottom:10px;'>{html_tools.escape(e.entry)}</div>"
    return dashboard_html(html, request=request)

@app.post("/journal")
def add_entry(entry: str = Form(...), db: Session = Depends(get_db)):
    db.add(Journal(entry=entry))
    db.commit()
    return RedirectResponse("/journal", status_code=303)

# ----------------------
# EMOCIONALMENTE
# ----------------------

@app.get("/emotional", response_class=HTMLResponse)
def emotional(request: Request, db: Session = Depends(get_db)):
    if db.query(EmotionalLog).count() == 0:
        initial_data = [
            {"status": "LLAMAMIENTO", "reason": "TIEMPO GANAS Agenda y planes", "action": "actividad 22 de marzo"},
            {"status": "TRABAJO", "reason": "Capacitacion pc ,RAQUEL ,esposo de jefa , y jefa embarazada", "action": "Mandar bolteas , CAMBIAR A RAQUEL"},
            {"status": "NO SER MAMA", "reason": "?", "action": ""},
            {"status": "NO ENTENDER AL ESPOSO, EN CASA", "reason": "", "action": "ESGARDITO MOTIVADO Y SIN DOLORES"},
            {"status": "COMPARTIR EL EVANGELIO CON LA FAMILIA", "reason": "domingo de familia , al Salir de la capilla ir a visitar", "action": ""},
            {"status": "NO AVANZAR ECONOMICAMENTE", "reason": "sabado 7 ir a recoger a rosa e ir a hermano edgar y famy ( improviso )", "action": "Plan b hayde"},
            {"status": "INESTABILIDAD EN VIEVIENDA", "reason": "", "action": ""},
            {"status": "CASA NO PROPIA", "reason": "", "action": ""},
            {"status": "VIVIR EN CASA DE CUÑADO", "reason": "", "action": ""},
            {"status": "DECEPCIONADA DE LOS LIDERES Y NO CONFIAR EN NADIE", "reason": "", "action": ""}
        ]
        for item in initial_data:
            db.add(EmotionalLog(**item))
        db.commit()

    entries = db.query(EmotionalLog).all()
    html = """
    <h1>🧠 Cómo están emocionalmente</h1>
    <div style="background:#f9f9f9; padding:15px; border-radius:8px; margin-bottom:20px; border:1px solid #ddd;">
        <form method="post" style="display:flex; gap:10px; flex-wrap:wrap;">
            <input name="status" placeholder="1. Cómo estás (Estado)" required style="flex:1; min-width:200px;">
            <input name="reason" placeholder="2. Motivo" style="flex:1; min-width:200px;">
            <input name="action" placeholder="3. Qué haremos (Acción)" style="flex:1; min-width:200px;">
            <button style="background:#4CAF50; color:white; border:none;">Agregar</button>
        </form>
    </div>
    <table style="width:100%; border-collapse:collapse; margin-top:20px; background:white; font-size:0.95em;">
        <thead>
            <tr style="background:#4CAF50; color:white; text-align:left;">
                <th style="padding:12px; border:1px solid #ddd;">1. CÓMO ESTÁS</th>
                <th style="padding:12px; border:1px solid #ddd;">2. MOTIVO</th>
                <th style="padding:12px; border:1px solid #ddd;">3. QUÉ HAREMOS</th>
                <th style="padding:12px; border:1px solid #ddd; width:50px;">Borrar</th>
            </tr>
        </thead>
        <tbody>
    """
    for row in entries:
        html += f"""
        <tr>
            <td style="padding:10px; border:1px solid #ddd; font-weight:bold;">{row.status}</td>
            <td style="padding:10px; border:1px solid #ddd;">{row.reason}</td>
            <td style="padding:10px; border:1px solid #ddd;">{row.action}</td>
            <td style="padding:10px; border:1px solid #ddd; text-align:center;">
                <form action="/emotional/delete/{row.id}" method="post" style="margin:0;">
                    <button style="background:#ff4444; color:white; border:none; cursor:pointer; padding:5px 10px; border-radius:4px;">X</button>
                </form>
            </td>
        </tr>
        """
    html += "</tbody></table>"
    return dashboard_html(html, request=request)

@app.post("/emotional")
def add_emotional(status: str = Form(...), reason: str = Form(default=""), action: str = Form(default=""), db: Session = Depends(get_db)):
    db.add(EmotionalLog(status=status, reason=reason, action=action))
    db.commit()
    return RedirectResponse("/emotional", status_code=303)

@app.post("/emotional/delete/{entry_id}")
def delete_emotional(entry_id: int, db: Session = Depends(get_db)):
    entry = db.query(EmotionalLog).filter(EmotionalLog.id == entry_id).first()
    if entry:
        db.delete(entry)
        db.commit()
    return RedirectResponse("/emotional", status_code=303)

# ----------------------
# AI COACH
# ----------------------

@app.get("/ai", response_class=HTMLResponse)
def ai_coach(request: Request):
    habit = recommend_habit()
    verse = recommend_scripture()
    html = f"""
    <h1>Coach IA</h1>
    <p><b>Hábito recomendado:</b> {habit}</p>
    <p><b>Escritura:</b> {verse}</p>
    """
    return dashboard_html(html, request=request)

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    print(f"🚀 Iniciando servidor en el puerto {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
