# 💸 AI Expense Tracker with Google Sheets Integration

An AI-powered expense tracker that lets users **chat with an assistant** to add, retrieve, and analyze expenses. The assistant interacts directly with **Google Sheets** to store and manage your data — just like a smart accountant.

## 🧠 Features

- 💬 **Chat-based interface** for managing expenses
- 🧾 **Add and retrieve transactions** using natural language
- 📊 **Analyze spending patterns**
- 🗂️ Organized storage in **Google Sheets**
- 🎨 Beautiful and responsive **React + Tailwind CSS** frontend
- 🚀 Fast and scalable **Flask** backend API

---

## 🏗️ Tech Stack

| Tech         | Usage                        |
|--------------|------------------------------|
| React        | Frontend UI                  |
| Tailwind CSS | Styling                      |
| Flask        | Backend API                  |
| OpenRouter   | AI Assistant (e.g., Deepseek API) |
| Google Sheets API | Expense data storage     |
| GitHub       | Version Control              |

---

## 📂 Folder Structure

```bash
AI-Gsheet-Integration/
│
├── backend/                 # Flask backend API
│   ├── app.py               # Main backend file
│   └── utils/               # Utility functions (e.g., Google Sheets, AI)
│
├── Expense-tracker/        # React frontend
│   ├── public/
│   └── src/
│       ├── components/
│       ├── App.jsx
│       └── index.js
│
├── .gitignore
├── README.md
└── requirements.txt
```
## 🛠️ Setup Instructions
### ✅ Prerequisites
* Python 3.8+
* Node.js (v18+)
* npm or yarn
* Google Sheets API credentials
* OpenRouter API key

### 📦 Backend Setup (/backend)
1. Navigate to the backend directory:
cd backend

2. Create a virtual environment:
```
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```
3. Install dependencies:
```
pip install -r requirements.txt
```
4. Add your .env file with:

```
OPENROUTER_API_KEY=your_openrouter_key
GOOGLE_SHEET_ID=your_google_sheet_id
```
5. Start the Flask server:
```
python app.py
```
### 🧑‍🎨 Frontend Setup (/Expense-tracker)
1. Navigate to the frontend directory:
```
cd expense-tracker
```
3. Create a virtual environment:
```
npm install
```
3. Start Dev Server:
```
npm run dev
```
## 🌐 Environment Variables
### Backend (backend/.env)
```
OPENROUTER_API_KEY=your_openrouter_key
GOOGLE_SHEET_ID=your_google_sheet_id
```

## Screenshots
![image](https://github.com/user-attachments/assets/cfcec590-e1d1-4317-a52b-fac18f527d0f)

![image](https://github.com/user-attachments/assets/9c36d7ee-82f5-4310-ae50-966789715485)

## 🧪 Example Prompts
- “Add ₹500 spent on groceries today.”

- “How much did I spend on food this month?”

- “Show my last 5 expenses.”

## 📌 TODO
 Add expenses via AI

 - Retrieve expenses by category/date

 - Monthly expense summary with charts

 - Authentication for multiple users

## 🙌 Author
Made with ❤️ by Hasnain Kherani

Contributions and feedback are welcome!

## 📄 License
This project is licensed under the MIT License.

## Support
if any problem occurs while setting up the project, feel free to mail me at hasnainkherani1@gmail.com, I'll surely assist you on setting up the project perfectly.
