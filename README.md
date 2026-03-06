# 🚀 BS1 Project

BS1 is a Python-based backend service built with FastAPI.
This project follows a clean architecture structure to allow scalability and maintainability.

---

## 📦 Project Structure
bs1/
├── app/
│ ├── main.py
│ ├── core/
│ ├── domain/
│ ├── application/
│ ├── infrastructure/
│ └── interfaces/
├── tests/
├── scripts/
├── .env.example
├── pyproject.toml
└── README.md


---

## 🐍 Python Setup (Using venv)

### 1️⃣ Check Python Version

Make sure you have Python 3.11+ installed.

```bash
python3 --version


2️⃣ Create Virtual Environment
python3 -m venv .venv

3️⃣ Activate Virtual Environment

Mac / Linux
source .venv/bin/activate

Windows
.venv\Scripts\activate

4️⃣ Upgrade pip
pip install --upgrade pip

5️⃣ Install Dependencies
pip install fastapi "uvicorn[standard]" pytest

▶️ Run the Application
uvicorn app.main:app --reload

Open browser:

http://127.0.0.1:8000/health

Expected response:

{
  "ok": true,
  "project": "bs1"
}
🧪 Run Tests
pytest
🧹 Deactivate Virtual Environment
deactivate
📝 Notes

Always activate .venv before running the project

Do not commit .venv folder

Use .env for environment variables


