# 🧠 String Analyzer API

A RESTful API built with **Flask** that analyzes strings and computes their properties — including length, palindrome detection, unique characters, word count, SHA-256 hash, and character frequency.  

Developed by **Ay Adefioye** as part of a backend development practice and portfolio project.

---

## 🚀 Features

- 🔤 Analyze any string and get detailed properties  
- 🔁 Detect **palindromes** (case-insensitive)  
- 🔣 Count **unique characters** and **word count**  
- 🧮 Generate **character frequency maps**  
- 🔐 Create unique **SHA-256 hashes** for identification  
- 🧠 Filter results using **query parameters** or **natural language queries**  
- 💾 Built with a clean modular structure using Flask **Blueprints**  
- 🧪 Includes unit tests for routes and utilities  

---

## 📁 Project Structure

string_analyzer/
├── app.py
├── requirements.txt
├── Procfile
└── README.md

yaml
Copy code

---

## ⚙️ Installation & Setup

### 1️⃣ Clone the repository
```bash
git clone https://github.com/AyAdefioye/string-analyzer.git
cd string-analyzer
2️⃣ Create and activate a virtual environment
bash
Copy code
python -m venv venv
source venv/bin/activate   # macOS/Linux
venv\Scripts\activate      # Windows
3️⃣ Install dependencies
bash
Copy code
pip install -r requirements.txt
4️⃣ Run the application
bash
Copy code
python app.py
Access the app at 👉 http://127.0.0.1:5000

🔍 API Endpoints
1️⃣ Create/Analyze String
POST /strings

Body:

json
Copy code
{
  "value": "madam"
}
Response (201 Created):

json
Copy code
{
  "id": "sha256_hash_here",
  "value": "madam",
  "properties": {
    "length": 5,
    "is_palindrome": true,
    "unique_characters": 3,
    "word_count": 1,
    "sha256_hash": "hash_here",
    "character_frequency_map": {
      "m": 2,
      "a": 2,
      "d": 1
    }
  },
  "created_at": "2025-10-22T18:00:00Z"
}
2️⃣ Get Specific String
GET /strings/{string_value}

Returns analysis for a previously stored string.

3️⃣ Get All Strings with Filtering
GET /strings?is_palindrome=true&min_length=3

Supports query parameters:

is_palindrome

min_length

max_length

word_count

contains_character

4️⃣ Natural Language Filtering
GET /strings/filter-by-natural-language?query=all%20single%20word%20palindromic%20strings

Response:

json
Copy code
{
  "data": [
    {
      "id": "hash",
      "value": "madam",
      "properties": { /* ... */ },
      "created_at": "2025-10-22T18:00:00Z"
    }
  ],
  "count": 1,
  "interpreted_query": {
    "original": "all single word palindromic strings",
    "parsed_filters": {
      "word_count": 1,
      "is_palindrome": true
    }
  }
}
5️⃣ Delete String
DELETE /strings/{string_value}

Response:
204 No Content — if successful.

🧪 Running Tests
📁 Folder Layout
bash
Copy code
tests/
├── __init__.py
├── test_utils.py      # tests helper functions (palindrome, hash, etc.)
├── test_routes.py     # tests API endpoints
▶ Run all tests
bash
Copy code
pytest -v
✅ Example Output
bash
Copy code
==================== test session starts ====================
collected 8 items
tests/test_utils.py .....                                     [62%]
tests/test_routes.py ....                                     [100%]
==================== 9 passed in 0.89s ======================
🧱 Tech Stack
Tool	Purpose
Python 3.10+	Programming language
Flask	Web framework
SQLite 3	Data storage
Pytest	Unit testing
Gunicorn	Production server
Railway / Render	Deployment

🚀 Deployment
🟣 Deploy on Railway
Push your code to GitHub

Go to Railway.app

“New Project” → “Deploy from GitHub”

Add a Procfile:

makefile
Copy code
web: gunicorn app:app
Deploy 🚀

🟢 Deploy on Render
Visit Render.com

Create a “New Web Service”

Connect your GitHub repo

Set:

Runtime: Python

Start Command: gunicorn app:app

Deploy 🚀

🧰 Example Requests
POST

bash
Copy code
curl -X POST -H "Content-Type: application/json" \
-d '{"value": "madam"}' \
http://127.0.0.1:5000/strings
GET

bash
Copy code
curl http://127.0.0.1:5000/strings/madam
🧩 Future Improvements
Add database persistence with SQLAlchemy

Implement JWT authentication

Support batch string uploads

Add sentiment analysis and language detection

Expand natural language query interpretation

🎯 Backend Stack (Python & Flask)

🏁 License
Released under the MIT License — free for personal and commercial use.
