# 🩺 MediAI – AI Powered Medical Assistant

MediAI is a full-stack AI-powered healthcare application that provides intelligent medical assistance through Retrieval-Augmented Generation (RAG), symptom analysis, OCR-based medical report interpretation, and patient history management.

It combines modern AI technologies with a secure healthcare workflow to help users better understand their symptoms and medical reports.

---

##  Features

-  AI Medical Chat (Gemini AI + RAG)
-  Symptom Checker with Severity Detection
-  Medical Report Analyzer (PDF, DOCX & Images)
-  OCR Support using EasyOCR + Tesseract
-  Retrieval-Augmented Generation (RAG)
-  Patient Dashboard
-  Medical History Tracking
-  JWT Authentication
-  Role-Based Access Control
-  PostgreSQL Database
-  ChromaDB Vector Database
-  System Health Monitoring
-  Responsive User Interface

---

## 🛠 Tech Stack

### Frontend
- React
- TypeScript
- Vite
- Tailwind CSS
- Axios

### Backend
- FastAPI
- Python
- SQLAlchemy
- JWT Authentication
- Alembic

### AI & ML
- Google Gemini 2.5 Flash
- Retrieval-Augmented Generation (RAG)
- ChromaDB
- Sentence Transformers
- EasyOCR
- Tesseract OCR

### Database
- PostgreSQL
- ChromaDB

---

## 📸 Screenshots

### Landing Page
<img width="1137" height="912" alt="Screenshot 2026-07-04 155817" src="https://github.com/user-attachments/assets/daad6945-9a06-4cb0-9a5d-b490c4892199" />

---

---

### AI Medical Chat
<img width="1918" height="912" alt="Screenshot 2026-07-04 155707" src="https://github.com/user-attachments/assets/a506e660-df2e-417f-a5d8-e92f66de2924" />


---

### Symptom Checker

<img width="1897" height="908" alt="Screenshot 2026-07-04 155234" src="https://github.com/user-attachments/assets/217cd658-38fd-4fd8-9fc3-59f6b8051d45" />


---

### Medical Report Analyzer

<img width="1901" height="913" alt="Screenshot 2026-07-04 155340" src="https://github.com/user-attachments/assets/51dcaca8-a804-481d-9945-b187224a601b" />

---


## 📂 Project Structure

```
MediaAI
│
├── mediai-frontend
├── mediai-backend
├── uploads
├── logs
└── README.md
```

---

## ⚙️ Installation

### Clone Repository

```bash
git clone https://github.com/yourusername/mediai.git
cd mediai
```

### Backend

```bash
cd mediai-backend

pip install -r requirements.txt

uvicorn main:app --reload
```

### Frontend

```bash
cd mediai-frontend

npm install

npm run dev
```

---

## 🔑 Environment Variables

Create a `.env` file inside the backend.

```env
GEMINI_API_KEY=your_api_key

DATABASE_URL=your_database_url

JWT_SECRET_KEY=your_secret_key

CORS_ORIGINS=http://localhost:5173

OCR_ENABLED=true
```

---

## 📌 Main Modules

- Authentication
- AI Medical Chat
- Symptom Checker
- Medical Report Analyzer
- OCR Processing
- Patient Dashboard
- Medical History
- System Health Monitoring

---

## 📈 Future Improvements

- Voice-based consultation
- Doctor Portal
- Appointment Booking
- Medical Image Analysis
- Mobile Application
- Wearable Device Integration

---

## 👨‍💻 Author

**Rithwik Kandakatla**

Computer Science Engineering Student

GitHub: https://github.com/KandakatlaRithwik

LinkedIn: https://www.linkedin.com/in/rithwik-kandakatla/

---

## ⭐ Support

If you like this project, consider giving it a ⭐ on GitHub.
