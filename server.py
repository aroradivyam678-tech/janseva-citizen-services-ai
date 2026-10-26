import os
import base64
import json
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("JanSeva")

# Load environment variables from .env
env_file = Path(__file__).resolve().parent / ".env"
if env_file.exists():
    with open(env_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ[k.strip()] = v.strip().strip("'\"")

from sarvamai import SarvamAI
from sarvamai.core.api_error import ApiError

api_key = os.environ.get("SARVAM_API_KEY", "")
sarvam_client = None
if api_key:
    try:
        sarvam_client = SarvamAI(api_subscription_key=api_key)
    except Exception as e:
        logger.error(f"Error initializing Sarvam client: {e}")

app = FastAPI(title="JanSeva AI - Citizen Services Portal")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

static_dir = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

class ChatRequest(BaseModel):
    message: str
    language_code: str = "hi-IN"
    history: List[Dict[str, str]] = []

class TTSRequest(BaseModel):
    text: str
    language_code: str = "hi-IN"
    speaker: str = "meera"

# Knowledge base for government schemes
SCHEME_KNOWLEDGE = {
    "pm_kisan": {
        "hi": "प्रधानमंत्री किसान सम्मान निधि (PM-KISAN) के तहत सभी पात्र भूमिधारक किसान परिवारों को प्रति वर्ष ₹6,000 की वित्तीय सहायता ₹2,000 की तीन समान किस्तों में सीधे बैंक खाते में (DBT) दी जाती है। आवश्यक शर्तें: ई-केवाईसी (e-KYC) पूर्ण होना, भूमि विवरण सत्यापन, और आधार से बैंक खाता लिंक होना।",
        "en": "Under PM-KISAN, eligible farmer families receive ₹6,000 per year distributed in three 4-monthly installments of ₹2,000 each directly via DBT. Mandatory requirements include Aadhaar linking, land record verification, and completed e-KYC.",
        "ta": "PM-KISAN திட்டத்தின் கீழ் தகுதியான விவசாய குடும்பங்களுக்கு ஆண்டுக்கு ₹6,000 மூன்று தவணைகளில் (தலா ₹2,000) நேரடியாக வங்கி கணக்கில் செலுத்தப்படுகிறது. ஆதாருடன் வங்கி கணக்கு மற்றும் நில ஆவணங்கள் சரிபார்க்கப்பட வேண்டும்.",
        "te": "పీఎం కిసాన్ పథకం కింద అర్హులైన రైతు కుటుంబాలకు ఏడాదికి ₹6,000 మూడు విడతలలో (ప్రతి విడతకు ₹2,000) నేరుగా బ్యాంక్ ఖాతాలో జమ చేయబడుతుంది."
    },
    "ayushman": {
        "hi": "आयुष्मान भारत - प्रधानमंत्री जन आरोग्य योजना (AB-PMJAY) के तहत प्रत्येक पात्र परिवार को प्रति वर्ष ₹5 लाख तक का कैशलेस स्वास्थ्य बीमा द्वितीयक एवं तृतीयक उपचार के लिए मिलता है। आप अपने राशन कार्ड या आधार से नज़दीकी CSC केंद्र या सरकारी अस्पताल में आयुष्मान कार्ड बनवा सकते हैं।",
        "en": "Ayushman Bharat PM-JAY provides cashless healthcare coverage up to ₹5 Lakh per eligible family per year for secondary and tertiary hospitalization across empanelled public and private hospitals.",
        "ta": "ஆயுஷ்மான் பாரத் திட்டத்தின் கீழ் தகுதியான குடும்பங்களுக்கு ஆண்டுக்கு ₹5 லட்சம் வரை இலவச மருத்துவ சிகிச்சை வழங்கப்படுகிறது. அருகிலுள்ள அரசு மருத்துவமனை அல்லது CSC மையத்தில் அட்டை பெறலாம்.",
        "te": "ఆయుష్మాన్ భారత్ పథకం ద్వారా అర్హత ఉన్న కుటుంబానికి ఏడాదికి ₹5 లక్షల వరకు ఉచిత వైద్య చికిత్స సహాయం అందుతుంది."
    },
    "pension": {
        "hi": "अटल पेंशन योजना (APY) 18 से 40 वर्ष की आयु के सभी नागरिकों के लिए है। 60 वर्ष की आयु के बाद आपको मासिक ₹1,000 से ₹5,000 तक की निश्चित पेंशन मिलती है। राष्ट्रीय वृद्धावस्था पेंशन योजना (IGNOAPS) 60 वर्ष से अधिक आयु के BPL नागरिकों को प्रति माह सहायता देती है।",
        "en": "Atal Pension Yojana (APY) provides a guaranteed pension of ₹1,000 to ₹5,000 per month after age 60, depending on contributions starting between 18-40 years of age.",
        "ta": "அடல் பென்ஷன் யோஜனா (APY) 60 வயதிற்குப் பிறகு மாதம் ₹1,000 முதல் ₹5,000 வரை நிலையான ஓய்வூதியம் வழங்குகிறது. 18-40 வயதுக்குள் பதிவு செய்யலாம்.",
        "te": "అటల్ పెన్షన్ యోజన ద్వారా 60 ఏళ్ల తర్వాత నెలకు ₹1,000 నుండి ₹5,000 వరకు స్థిర పెన్షన్ పొందవచ్చు."
    },
    "certificate": {
        "hi": "आय व जाति प्रमाण पत्र बनवाने के लिए आवश्यक दस्तावेज़: 1. आवेदक का आधार कार्ड 2. राशन कार्ड 3. स्व-घोषणा पत्र 4. निवास प्रमाण (बिजली बिल या वोटर आईडी) 5. पासपोर्ट साइज फोटो। इसे जन सेवा केंद्र (CSC) या राज्य के ई-डिस्ट्रिक्ट पोर्टल से ऑनलाइन आवेदन कर 7-15 दिनों में प्राप्त किया जा सकता है।",
        "en": "Documents required for Income & Caste Certificates: 1. Aadhaar Card 2. Ration Card 3. Self-declaration affidavit 4. Address proof (Electricity bill/Voter ID) 5. Passport photo. Apply via your state e-District portal or nearest CSC center.",
        "ta": "வருமான மற்றும் சாதி சான்றிதழுக்கான ஆவணங்கள்: ஆதார் அட்டை, குடும்ப அட்டை, பாஸ்போர்ட் புகைப்படம் மற்றும் முகவரி சான்று. e-Sevai மையம் மூலம் விண்ணப்பிக்கலாம்.",
        "te": "ఆదాయ మరియు కుల ధృవీకరణ పత్రాల కొరకు ఆధార్ కార్డు, రేషన్ కార్డు, నివాస ధృవీకరణ పత్రం అవసరం. మీ-సేవ (MeeSeva) ద్వారా దరఖాస్తు చేసుకోవచ్చు."
    }
}

APPLICATIONS_DB = {
    "JS-2026-9812": {
        "id": "JS-2026-9812",
        "scheme": "PM-Kisan Samman Nidhi (17th Installment)",
        "applicant": "Ramesh Chandra Sharma",
        "applied_on": "12-Oct-2026",
        "current_stage": "Document Verification Passed",
        "status": "In Progress",
        "steps": [
            {"name": "Application Submitted", "date": "12-Oct-2026", "status": "completed"},
            {"name": "Aadhaar & Land Records e-KYC", "date": "16-Oct-2026", "status": "completed"},
            {"name": "Tehsil Officer Field Review", "date": "24-Oct-2026", "status": "in_progress"},
            {"name": "DBT Fund Release to Bank", "date": "Estimated 02-Nov-2026", "status": "pending"}
        ],
        "phone": "+91 98765 43210",
        "proactive_message_hi": "नमस्ते रमेश जी, जनसेवा पोर्टल से अपडेट: आपकी पीएम-किसान 17वीं किस्त का दस्तावेज़ सत्यापन सफल रहा है। तहसील स्तर पर अंतिम अनुमोदन के पश्चात राशि आपके आधार-लिंक बैंक खाते में अंतरित कर दी जाएगी।",
        "proactive_message_en": "Hello Ramesh ji, update from JanSeva Portal: Your PM-Kisan document verification is successfully completed. Next disbursement will be credited to your Aadhaar-linked bank account."
    },
    "JS-2026-4409": {
        "id": "JS-2026-4409",
        "scheme": "Ayushman Bharat Golden Card",
        "applicant": "Sunita Devi",
        "applied_on": "19-Oct-2026",
        "current_stage": "Card Issued & Ready to Download",
        "status": "Approved",
        "steps": [
            {"name": "Application Submitted", "date": "19-Oct-2026", "status": "completed"},
            {"name": "Ration Card Data Verification", "date": "21-Oct-2026", "status": "completed"},
            {"name": "Biometric Authentication", "date": "23-Oct-2026", "status": "completed"},
            {"name": "Card Generation", "date": "25-Oct-2026", "status": "completed"}
        ],
        "phone": "+91 98123 45678",
        "proactive_message_hi": "नमस्ते सुनीता जी, आपका आयुष्मान भारत गोल्डन कार्ड तैयार हो गया है! आप इसे किसी भी जन सेवा केंद्र से डाउनलोड कर ₹5 लाख तक का निःशुल्क उपचार लाभ ले सकती हैं।",
        "proactive_message_en": "Hello Sunita ji, your Ayushman Bharat Golden Card is approved and ready! You can download your card from the nearest CSC center for healthcare benefits up to ₹5 Lakh."
    }
}

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    index_file = static_dir / "index.html"
    return HTMLResponse(content=index_file.read_text(encoding="utf-8"))

@app.get("/api/health")
async def health_check():
    return {
        "status": "online",
        "has_api_key": bool(api_key),
        "sarvam_connected": sarvam_client is not None
    }

@app.post("/api/chat")
async def chat_endpoint(payload: ChatRequest):
    msg = payload.message.lower().strip()
    lang = payload.language_code
    short_lang = lang.split("-")[0] if "-" in lang else "hi"

    # Check for live Sarvam AI call
    if sarvam_client:
        try:
            system_prompt = (
                "You are JanSeva AI, an empathetic and official Citizen Services Assistant for India. "
                "You provide clear, accurate guidance on government schemes, pensions, ration cards, "
                "income/caste certificates, taxes, and eligibility in Indian regional languages. "
                f"Respond naturally in the citizen's requested language ({lang}). "
                "Keep answers structured, supportive, and highlight required documents and steps."
            )
            messages = [{"role": "developer", "content": system_prompt}]
            for h in payload.history[-4:]:
                messages.append({"role": h.get("role", "user"), "content": h.get("content", "")})
            messages.append({"role": "user", "content": payload.message})

            response = sarvam_client.chat.completions(
                model="sarvam-105b-conversations",
                messages=messages
            )
            reply_text = response.choices[0].message.content
            return {
                "reply": reply_text,
                "source": "sarvam-105b-conversations",
                "quota_ok": True
            }
        except ApiError as e:
            logger.warning(f"Sarvam API call returned ApiError (likely quota or auth): {e}")
        except Exception as e:
            logger.warning(f"Sarvam API general exception: {e}")

    # Fallback contextual response when quota is exhausted or client offline
    reply = ""
    if "kisan" in msg or "farmer" in msg or "किसान" in msg:
        reply = SCHEME_KNOWLEDGE["pm_kisan"].get(short_lang, SCHEME_KNOWLEDGE["pm_kisan"]["hi"])
    elif "ayushman" in msg or "health" in msg or "स्वास्थ्य" in msg or "गोल्डन" in msg:
        reply = SCHEME_KNOWLEDGE["ayushman"].get(short_lang, SCHEME_KNOWLEDGE["ayushman"]["hi"])
    elif "pension" in msg or "पेंशन" in msg or "atal" in msg:
        reply = SCHEME_KNOWLEDGE["pension"].get(short_lang, SCHEME_KNOWLEDGE["pension"]["hi"])
    elif "certificate" in msg or "प्रमाण" in msg or "income" in msg or "caste" in msg or "जाति" in msg or "आय" in msg:
        reply = SCHEME_KNOWLEDGE["certificate"].get(short_lang, SCHEME_KNOWLEDGE["certificate"]["hi"])
    else:
        if short_lang == "hi":
            reply = f"नमस्ते! मैं आपका जनसेवा सहायक हूँ। मैं पीएम-किसान सम्मान निधि, आयुष्मान भारत, अटल पेंशन योजना, राशन कार्ड, आय एवं जाति प्रमाण पत्र से संबंधित किसी भी सरकारी सेवा की पात्रता, आवेदन प्रक्रिया और आवश्यक दस्तावेज़ों में आपकी सहायता कर सकता हूँ। कृपया अपना प्रश्न पूछें।"
        elif short_lang == "ta":
            reply = f"வணக்கம்! நான் உங்கள் ஜன்சேவா குடிமக்கள் சேவை உதவியாளர். அரசு திட்டங்கள், ஓய்வூதியம் மற்றும் சான்றிதழ் விவரங்களுக்கு நான் உங்களுக்கு உதவ முடியும்."
        elif short_lang == "te":
            reply = f"నమస్కారం! నేను మీ జన్సేవా సహాయకుడిని. ప్రభుత్వ పథకాలు, పెన్షన్లు మరియు సర్టిఫికెట్ల వివరాలలో మీకు సహాయం చేయడానికి సిద్ధంగా ఉన్నాను."
        else:
            reply = f"Hello! I am your JanSeva Citizen Services Assistant. I can guide you through government schemes (PM-Kisan, Ayushman Bharat, APY), taxes, pensions, and certificate applications with step-by-step document verification."

    return {
        "reply": reply,
        "source": "janseva-knowledge-base (Sarvam API Quota Notice: Recharging credits will enable live Sarvam-105B generation)",
        "quota_ok": False
    }

@app.post("/api/tts")
async def tts_endpoint(payload: TTSRequest):
    if sarvam_client:
        try:
            # Map valid Sarvam language codes
            lang_code = payload.language_code
            if lang_code not in ['bn-IN', 'en-IN', 'gu-IN', 'hi-IN', 'kn-IN', 'ml-IN', 'mr-IN', 'od-IN', 'pa-IN', 'ta-IN', 'te-IN']:
                lang_code = "hi-IN"

            tts_resp = sarvam_client.text_to_speech.convert(
                text=payload.text[:400],
                language_code=lang_code,
                model="bulbul:v2",
                output_audio_codec="mp3"
            )
            if tts_resp.audios:
                return {
                    "audio_base64": tts_resp.audios[0],
                    "format": "mp3",
                    "source": "sarvam-bulbul"
                }
        except Exception as e:
            logger.warning(f"Sarvam TTS failed (likely quota or auth): {e}")

    # Fallback indicator
    return {
        "audio_base64": None,
        "message": "TTS speech ready for browser speech synthesis fallback",
        "source": "browser-speech"
    }

@app.post("/api/docai/verify")
async def verify_document(
    doc_type: str = Form("aadhaar"),
    applicant_name: str = Form(""),
    file: Optional[UploadFile] = File(None)
):
    # Simulated / DocAI extracted model
    sample_extractions = {
        "aadhaar": {
            "document_type": "Aadhaar Card (UIDAI)",
            "extracted_fields": {
                "Full Name": applicant_name or "Ramesh Chandra Sharma",
                "Father / Husband": "Kailash Nath Sharma",
                "DOB": "14/08/1982",
                "Gender": "Male",
                "Aadhaar Number": "XXXX-XXXX-4912",
                "Address": "Gram Post Rampur, Tehsil Sadar, Varanasi, UP - 221001",
                "QR Code Hash": "VERIFIED_UIDAI_SHA256"
            },
            "status": "Verified & Matched",
            "confidence": 0.98,
            "checklist": [
                {"item": "Name matches application", "passed": True},
                {"item": "Age eligibility (>= 18)", "passed": True},
                {"item": "Valid Address in jurisdiction", "passed": True},
                {"item": "Active UIDAI hologram / QR detected", "passed": True}
            ]
        },
        "pan": {
            "document_type": "Permanent Account Number (PAN)",
            "extracted_fields": {
                "Full Name": applicant_name or "Ramesh Chandra Sharma",
                "Father's Name": "Kailash Nath Sharma",
                "Date of Birth": "14/08/1982",
                "PAN Number": "ABRPS****K",
                "Status": "Active in Income Tax Dept"
            },
            "status": "Verified & Matched",
            "confidence": 0.96,
            "checklist": [
                {"item": "Name spelling verified", "passed": True},
                {"item": "DOB cross-matched with Aadhaar", "passed": True},
                {"item": "PAN linked with Aadhaar", "passed": True}
            ]
        },
        "income": {
            "document_type": "Income Certificate (Tehsil e-District)",
            "extracted_fields": {
                "Applicant": applicant_name or "Ramesh Chandra Sharma",
                "Annual Household Income": "₹ 72,000",
                "Category": "Marginal Farmer / BPL Eligible",
                "Certificate No": "UP-INC-2026-981042",
                "Valid Upto": "31-Mar-2029"
            },
            "status": "Eligible for Full Subsidy",
            "confidence": 0.95,
            "checklist": [
                {"item": "Income below threshold (₹2.5L)", "passed": True},
                {"item": "Tehsildar digital signature valid", "passed": True},
                {"item": "Certificate validity active", "passed": True}
            ]
        }
    }

    result = sample_extractions.get(doc_type.lower(), sample_extractions["aadhaar"])
    return result

@app.get("/api/applications/{app_id}")
async def get_application(app_id: str):
    app_data = APPLICATIONS_DB.get(app_id.upper().strip())
    if not app_data:
        raise HTTPException(status_code=404, detail="Application ID not found")
    return app_data

@app.post("/api/proactive-alert")
async def trigger_proactive_alert(app_id: str = Form(...), channel: str = Form("voice")):
    app_data = APPLICATIONS_DB.get(app_id.upper().strip())
    if not app_data:
        raise HTTPException(status_code=404, detail="Application ID not found")

    message = app_data["proactive_message_hi"]
    audio_base64 = None

    if sarvam_client:
        try:
            tts_res = sarvam_client.text_to_speech.convert(
                text=message,
                language_code="hi-IN",
                model="bulbul:v2",
                output_audio_codec="mp3"
            )
            if tts_res.audios:
                audio_base64 = tts_res.audios[0]
        except Exception as e:
            logger.warning(f"Proactive alert TTS failed: {e}")

    return {
        "channel": channel,
        "phone": app_data["phone"],
        "message": message,
        "audio_base64": audio_base64,
        "status": "Dispatched to citizen",
        "app_id": app_id
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
