# 🇮🇳 JanSeva AI — Sovereign Citizen Services Agent

> **AI-powered citizen helpline and services platform for government schemes, document verification, and proactive multilingual status updates.** Built natively on **[Sarvam AI](https://docs.sarvam.ai)**.

---

## 🌟 Overview

**JanSeva AI** bridges the gap between citizens and government welfare schemes by providing an intelligent, multilingual, and voice-enabled assistant.

- 💬 **Scheme & Tax Advisory**: Conversational guidance on PM-Kisan, Ayushman Bharat, APY pensions, ration cards, and tax policies in Indic regional languages (*Hindi, Tamil, Telugu, Bengali, Kannada, Marathi, Gujarati, English*).
- 📑 **Application & Document Verification (DocAI)**: Scans, digitizes, and cross-verifies citizen IDs (*Aadhaar, PAN, Income/Caste Certificates*) to eliminate application rejection.
- 🔔 **Proactive Outreach & Voice Updates**: Dispatches automated regional voice calls (*Bulbul TTS*) and WhatsApp notifications to keep beneficiaries informed in their mother tongue.

---

## 🧠 Sarvam AI APIs Integrated

| Module | Sarvam AI API / Model | Purpose |
| :--- | :--- | :--- |
| **Chat & Reasoning** | `sarvam-105b-conversations` | Multilingual policy reasoning, eligibility determination, and scheme guidance. |
| **Speech-to-Text** | `saaras:v3` | High-accuracy voice input transcription across Indian accents & code-mixed languages. |
| **Text-to-Speech** | `bulbul:v2` | Expressive natural regional voice synthesis for citizen voice calls and audio readouts. |
| **Document AI** | `doc_ai.digitise` & `extract` | Automated OCR & entity extraction from scanned IDs and welfare certificates. |
| **Translation** | `mayura:v1` / `sarvam-translate` | Cross-lingual translation between English portals and regional languages. |

---

## 🚀 Quickstart

### 1. Clone the repository
```bash
git clone https://github.com/aroradivyam678-tech/janseva-citizen-services-ai.git
cd janseva-citizen-services-ai
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure API Key
Create a `.env` file in the root folder:
```env
SARVAM_API_KEY=your_sarvam_api_key_here
```
*(Get your key from [dashboard.sarvam.ai](https://dashboard.sarvam.ai))*

### 4. Run the Web Application
```bash
python server.py
```
Open your browser and navigate to:
```
http://127.0.0.1:8000
```

---

## 📁 Project Structure

```
sarvam-ai/
├── server.py              # FastAPI backend integrating Sarvam AI client
├── main.py                # Standalone script for one-shot chat completion test
├── requirements.txt       # Project dependencies
├── .gitignore             # Ignores .env and cache
├── static/
│   └── index.html         # Modern responsive Citizen Services web portal
└── README.md              # Project documentation
```

---

## 🛡️ Privacy & Sovereign AI
All credentials are stored strictly in local environment variables (`.env`) and are never tracked in version control or transmitted outside of authorized Sarvam AI endpoints.
