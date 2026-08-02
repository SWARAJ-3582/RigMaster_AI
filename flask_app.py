from datetime import timedelta
from flask import Flask, render_template, request, jsonify, Response, session
import requests
import json
import sqlite3
import os
from dotenv import load_dotenv
import csv
import io
import uuid

# Ye function teri .env file ko dhundhega aur uske variables ko system memory mein daal dega
#load_dotenv(), per ye sirf locally run krega server per nhi, server per run krane ke liye ye rha code
# SERVER KO EXACT PATH BATANA PADEGA:
project_folder = '/home/SWRJ/mysite'
load_dotenv(os.path.join(project_folder, '.env'))
app = Flask(__name__)
# Ab hum hardcoded string ki jagah memory (environment) se value uthayenge
app.secret_key = os.getenv("APP_SECRET_KEY")
API_KEY = os.getenv("GEMINI_API_KEY")
app.permanent_session_lifetime = timedelta(days=365)
DB_NAME = "rigmaster.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS scan_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            device_type TEXT,  -- NAYA COLUMN: PC ya Laptop
            cpu TEXT, gpu TEXT, ram TEXT, storage TEXT,
            mobo TEXT, psu TEXT, cooling TEXT,
            issue_type TEXT, status TEXT, diagnosis TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def get_fallback_response(language, device_type):
    print("WARNING: Live AI Engine Down! Using Offline Baseline Engine...")
    is_laptop = (device_type == 'Laptop')

    if "Hinglish" in language:
        solutions =["Laptop ko saaf karke achha thermal paste lagayein aur cooling pad use karein.", "RAM aur SSD upgrade karein stuttering rokne ke liye.", "Undervolting try karein taaki heat kam ho."] if is_laptop else["High-end GPU ke liye 850W+ Gold PSU lagayein.", "Liquid AIO cooler install karein taaki thermal throttling na ho.", "Motherboard BIOS update karein."]
        diag = f"RigMaster engine abhi 'Offline Baseline Mode' mein hai. Aapke {device_type} ke specs dekh ke lag raha hai ki thermal throttling ya hardware imbalance ka issue hai."
        return {"status": "Warning", "diagnosis": diag, "solutions": solutions}
    else:
        solutions =["Clean the internals and repaste the CPU/GPU.", "Use a quality cooling pad and undervolt to reduce temps.", "Upgrade RAM to dual-channel and use an NVMe SSD."] if is_laptop else["Ensure an 850W+ Gold-rated PSU for high-end GPUs.", "Install an AIO liquid cooler to prevent thermal throttling.", "Update Motherboard BIOS for better hardware compatibility."]
        diag = f"Operating in 'Baseline Mode'. Heuristics indicate a potential thermal throttling or hardware imbalance issue in your {device_type}."
        return {"status": "Warning", "diagnosis": diag, "solutions": solutions}

@app.route('/')
def index():
    session.permanent = True  # NAYI LINE
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    user_id = session.get('user_id', 'anonymous')
    data = request.json
    device_type = data.get('deviceType', 'Desktop PC')
    cpu = data.get('cpu', 'Not Specified')
    gpu = data.get('gpu', 'Not Specified')
    ram = data.get('ram', 'Not Specified')
    storage = data.get('storage', 'Not Specified')
    mobo = data.get('mobo', 'N/A')
    psu = data.get('psu', 'N/A')
    cooling = data.get('cooling', 'N/A')
    issue_type = data.get('issueType', 'General Check')
    symptoms = data.get('symptoms', 'None')
    language = data.get('language', 'English')

    prompt = f"""
    You are 'RigMaster AI', an elite hardware technician. Analyze this system:
    Device Type: {device_type}
    CPU: {cpu}, GPU: {gpu}, RAM: {ram}, Storage: {storage}
    Motherboard: {mobo}, PSU: {psu}, Cooling: {cooling}
    Analysis Type: {issue_type}, Symptoms: {symptoms}.

    CRITICAL RULES:
    1. If Device Type is 'Laptop', NEVER suggest upgrading the Motherboard, CPU, GPU, or PSU as they are soldered/fixed. Instead, suggest thermal repasting, undervolting, cooling pads, or RAM/SSD upgrades.
    2. If 'Desktop PC', check for component compatibility, PSU wattage, and adequate cooling.

    Return STRICTLY in JSON: "status" ("Critical", "Warning", or "Good"), "diagnosis" (Short paragraph), "solutions" (List of 3 actionable steps).
    JSON keys must be English. Content inside "diagnosis" and "solutions" MUST be in {language}.
    """

    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={API_KEY}"
        payload = {"contents":[{"parts": [{"text": prompt}]}], "generationConfig": {"temperature": 0.3}}
        response = requests.post(url, headers={'Content-Type': 'application/json'}, json=payload)
        response_data = response.json()

        if 'error' in response_data:
            result = get_fallback_response(language, device_type)
        else:
            raw_text = response_data['candidates'][0]['content']['parts'][0]['text'].replace('```json', '').replace('```', '').strip()
            result = json.loads(raw_text)

        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('''INSERT INTO scan_history (session_id, device_type, cpu, gpu, ram, storage, mobo, psu, cooling, issue_type, status, diagnosis)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (user_id, device_type, cpu, gpu, ram, storage, mobo, psu, cooling, issue_type, result['status'], result['diagnosis']))
        conn.commit()
        conn.close()
        return jsonify(result)

    except Exception as e:
        print("Backend Error:", str(e))
        return jsonify(get_fallback_response(language, device_type))

@app.route('/history')
def history():
    user_id = session.get('user_id', 'anonymous')
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM scan_history WHERE session_id = ? ORDER BY id DESC", (user_id,))
    records = c.fetchall()
    conn.close()

    html = """
    <!DOCTYPE html>
    <html lang='en'>
    <head>
        <meta charset='UTF-8'>
        <meta name='viewport' content='width=device-width, initial-scale=1.0'>
        <title>RigMaster | My Analytics</title>
        <link href='https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=Space+Grotesk:wght@500;700&display=swap' rel='stylesheet'>
        <link href='https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css' rel='stylesheet'>
        <style>
            body { background-color: #0A0E17; color: #E2E8F0; font-family: 'Inter', sans-serif; padding: 20px; margin: 0; background-image: radial-gradient(circle at 50% 0%, rgba(41, 121, 255, 0.1) 0%, transparent 50%); }
            h1, h2 { font-family: 'Space Grotesk', sans-serif; }
            .header-flex { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 15px; margin-bottom: 30px; }
            .text-gradient { background: linear-gradient(90deg, #00E5FF, #2979FF); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
            .btn-group { display: flex; gap: 10px; flex-wrap: wrap; }
            .btn { padding: 10px 20px; text-decoration: none; border-radius: 8px; font-weight: 600; transition: all 0.3s ease; font-family: 'Inter', sans-serif; font-size: 14px;}
            .btn-back { background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1); color: #fff; }
            .btn-back:hover { background: rgba(255, 255, 255, 0.1); }
            .btn-download { background: linear-gradient(90deg, #00C6FF, #0072FF); color: white; border: none; }
            .btn-download:hover { transform: translateY(-2px); box-shadow: 0 8px 20px rgba(0, 198, 255, 0.4); }
            .table-wrapper { background: rgba(20, 25, 35, 0.6); backdrop-filter: blur(12px); border: 1px solid rgba(0, 229, 255, 0.15); border-radius: 16px; padding: 20px; overflow-x: auto; box-shadow: 0 8px 32px rgba(0,0,0,0.3); }
            table { width: 100%; border-collapse: collapse; min-width: 900px; }
            th, td { padding: 15px; text-align: left; border-bottom: 1px solid rgba(255,255,255,0.05); }
            th { color: #00E5FF; font-family: 'Space Grotesk', sans-serif; font-weight: 600; letter-spacing: 1px; }
            td { font-size: 0.95rem; line-height: 1.6; color: #E2E8F0; }
            .status-Critical { color: #FF4D4D; font-weight: 600; }
            .status-Warning { color: #F59E0B; font-weight: 600; }
            .status-Good { color: #10B981; font-weight: 600; }
        </style>
    </head>
    <body>
        <div class='header-flex'>
            <h2 class='text-gradient' style='margin:0;'><i class='fas fa-chart-line me-2'></i> RigMaster Analytics</h2>
            <div class='btn-group'>
                <a href='/' class='btn btn-back'><i class='fas fa-arrow-left me-2'></i>Scanner</a>
                <a href='/download' class='btn btn-download'><i class='fas fa-download me-2'></i>Export CSV</a>
            </div>
        </div>
        <div class='table-wrapper'>
            <table>
                <tr><th>DEVICE</th><th>CPU</th><th>GPU</th><th>RAM</th><th>STATUS</th><th>DIAGNOSIS</th></tr>
    """
    for r in records:
        status_class = f"status-{r['status']}"
        html += f"<tr><td style='color:#2979FF; font-weight:600;'>{r['device_type']}</td><td>{r['cpu']}</td><td>{r['gpu']}</td><td>{r['ram']}</td><td class='{status_class}'>[{r['status'].upper()}]</td><td>{r['diagnosis']}</td></tr>"
    html += "</table></div></body></html>"
    return html
@app.route('/download')
def download_data():
    user_id = session.get('user_id', 'anonymous')
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT device_type, cpu, gpu, ram, storage, mobo, psu, cooling, issue_type, status, diagnosis FROM scan_history WHERE session_id = ? ORDER BY id DESC", (user_id,))
    records = c.fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Device Type', 'CPU', 'GPU', 'RAM', 'Storage', 'Motherboard', 'PSU', 'Cooling', 'Issue Type', 'Status', 'Diagnosis'])
    for r in records:
        writer.writerow(r)

    output.seek(0)
    return Response(output, mimetype="text/csv", headers={"Content-Disposition": "attachment;filename=My_RigMaster_Scans.csv"})

if __name__ == '__main__':
    app.run(debug=False)