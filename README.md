# 🖥️ RigMaster AI - Hardware Telemetry & Diagnostics

## 🚀 Overview

RigMaster AI is an intelligent hardware diagnostic tool designed to prevent system bottlenecking, thermal throttling, and hardware incompatibilities. By leveraging a custom WSGI-routed Flask backend and the Google Gemini AI Engine, it processes user hardware telemetry (CPU, GPU, RAM, Cooling, PSU) and provides real-time, actionable diagnostics in multiple languages.

## 🛠️ Tech Stack & Architecture

- **Frontend:** HTML5, CSS3 (Glassmorphism UI), Bootstrap 5, Vanilla JavaScript.
- **Backend:** Python 3.14, Flask (WSGI Framework).
- **Database:** SQLite3 (Local Session & Scan History Tracking).
- **AI Engine:** Google Gemini 2.5 Flash API (via direct HTTP requests).
- **Security:** `python-dotenv` for strict environment variable management.

## ⚙️ Core Architecture Flow

1. **Client Interface:** User inputs hardware specs and system symptoms via a secure web form.
2. **Backend Parsing:** Flask processes the incoming JSON request (`/analyze` route) and constructs a strictly controlled prompt.
3. **AI Processing:** The server makes an asynchronous HTTP call to the Gemini API, forcing a structured JSON output.
4. **Data Persistence:** Results are logged securely into the local SQLite database for session history.
5. **Client Render:** The frontend parses the JSON response and displays the threat level, diagnosis, and action plan.

## 🔒 Security Implementations

- **Hidden Secrets:** API keys and Flask Secret Keys are strictly managed via a `.env` file and excluded from version control.
- **Session Management:** Cryptographically signed cookies prevent local session tampering.
- **Fallback Mechanisms:** Built-in heuristic offline mode in case of AI engine failure or rate-limiting.

## 💻 How to Run Locally

**1. Clone the repository:**

```bash
git clone https://github.com/YOUR_USERNAME/RigMaster-AI.git
cd RigMaster-AI
```

**2. Create a Virtual Environment:**

```bash
python -m venv venv
```

**3. Activate the Virtual Environment:**

- Windows: `venv\Scripts\activate`
- Mac/Linux: `source venv/bin/activate`

**4. Install Dependencies:**

```bash
pip install -r requirements.txt
```

**5. Setup Environment Variables:**
Create a `.env` file in the root directory and add the following:

```env
GEMINI_API_KEY=your_gemini_api_key_here
APP_SECRET_KEY=your_random_flask_secret_key
```

**6. Run the Server:**

```bash
python flask_app.py
```

**Access the app at http://127.0.0.1:5000**
