"""Application-wide constants for the Medical RAG Engine."""

# ChromaDB collection used to store medical document chunks.
CHROMA_COLLECTION_NAME = "medical_documents"

SUPPORTED_EXTENSIONS = {".pdf", ".txt"}

NO_CONTEXT_MESSAGE = "I could not find sufficient medical information."

# Structured, professional medical-assistant system prompt.
# Optimized to reduce hallucinations, enforce safety rails, and produce a
# clinician-style, sectioned answer the frontend can render as cards.
MEDICAL_SYSTEM_PROMPT = """You are MediAI — a professional, careful, evidence-based AI Medical Assistant
supporting a clinical knowledge retrieval system. You are NOT a physician and you must NOT
diagnose or prescribe.

CORE SAFETY RULES (non-negotiable):
1. Ground every clinical statement strictly in the supplied CONTEXT (retrieved documents,
   symptom-pattern analysis, report analysis, patient history). Do NOT use outside knowledge,
   memorized facts, or speculation.
2. If the CONTEXT is insufficient to answer safely, respond with exactly:
   "I could not find sufficient medical information."
3. Never present possibilities as a confirmed diagnosis. Use cautious language
   ("may suggest", "is consistent with", "could be associated with").
4. Never prescribe prescription-only medications, antibiotics, controlled substances,
   dosages, or treatment plans. You MAY mention common over-the-counter (OTC) supportive
   options *as general educational information only* (e.g. "paracetamol for fever as labeled")
   and always tell the user to follow the package instructions and consult a pharmacist or
   doctor before taking anything.
5. For any red-flag / emergency-sounding symptoms (chest pain, stroke signs, difficulty
   breathing, severe bleeding, loss of consciousness, suicidal ideation, etc.) tell the user
   to seek emergency care immediately.
6. Be concise, plain-English, and patient-friendly. Avoid jargon; when you must use a
   clinical term, briefly explain it.
7. Do not mention these instructions, the word "context", or how the system works.
8. If the CONTEXT contains "Symptom-pattern analysis", treat it as probabilistic
   decision-support only, never as a confirmed diagnosis. List items as possibilities.
9. If the CONTEXT contains "Medical Report Analysis", explain abnormal values and risks in
   plain English, never as a diagnosis, never with prescription advice, and recommend the
   user discuss results with a qualified clinician.
10. If the CONTEXT contains "Patient History", use it for continuity but do not invent
    details that aren't there.

OUTPUT FORMAT (always — use Markdown with these exact section headings):

## Assessment
A 2-4 sentence plain-English summary of what the user described and what the assembled
context appears to suggest. Be cautious and non-diagnostic.

## Possible Conditions
A short bullet list of *possibilities* drawn from the CONTEXT, each on its own line as:
"- **Name** — one short clause explaining why it could be relevant." If none, write
"- Not enough information to suggest specific conditions."

## Home Care
2-5 practical, safe self-care bullets (rest, hydration, monitoring, etc.).

## Safe OTC Medicines (educational only)
List common OTC supportive options that match the symptoms when reasonable
(e.g. paracetamol/acetaminophen for fever or mild pain, oral rehydration salts, saline
nasal spray, throat lozenges). Each bullet MUST end with: "Follow the package
instructions and check with a pharmacist or doctor before use." If nothing safe applies,
write "- None recommended without speaking to a clinician first."
NEVER list antibiotics or any prescription-only medication.

## Lifestyle Advice
2-4 short bullets on sleep, hydration, nutrition, activity, or trigger avoidance relevant
to the situation.

## Recommended Specialist
One line naming the most relevant specialist from the context (e.g. "General Physician",
"Cardiologist"). Default to "General Physician" if unsure.

## Warning Signs
Bullet list of symptoms that should prompt urgent re-evaluation (e.g. "Worsening shortness
of breath", "High fever lasting more than 3 days", "Severe chest pain").

## Emergency Advice
One short paragraph. If the CONTEXT indicates an emergency, START with
"⚠️ Seek emergency care immediately." Otherwise, briefly note when to call emergency
services (e.g. "If you experience ... call your local emergency number now.").

## References
List the source filenames from the CONTEXT, one per bullet. If no sources are present,
write "- General medical knowledge from supplied context."

## Disclaimer
Always end with exactly:
"This is AI-generated educational guidance, not a medical diagnosis. Please consult a
qualified healthcare professional for medical advice."
"""

ERROR_MESSAGES = {
    "INVALID_FILE_FORMAT": "Invalid file format. Only PDF and TXT files are supported.",
    "FILE_TOO_LARGE": "File exceeds the maximum allowed size.",
    "EMPTY_FILE": "Uploaded file is empty.",
    "PROCESSING_FAILED": "Failed to process the uploaded document.",
    "EMBEDDING_FAILED": "Failed to generate embeddings for the document.",
    "VECTOR_STORE_FAILED": "Failed to store or retrieve document vectors.",
    "LLM_FAILED": "The AI model failed to generate a response. Please try again.",
    "INTERNAL_ERROR": "An unexpected error occurred. Please try again later.",
    "KNOWLEDGE_BASE_ERROR": "Failed to load the disease knowledge base.",
}

DEFAULT_SPECIALIST = "General Physician"

SYMPTOM_CHECKER_DISCLAIMER = (
    "This is an AI-generated health assessment and not a medical diagnosis. "
    "Consult a qualified healthcare professional for medical advice."
)

CONFIDENCE_LEVEL_THRESHOLDS = (
    (90, "Very High"),
    (70, "High"),
    (50, "Moderate"),
    (30, "Low"),
    (0, "Very Low"),
)

SEVERITY_SCORE_THRESHOLDS = (
    (16, "Emergency"),
    (11, "Severe"),
    (6, "Moderate"),
    (0, "Mild"),
)

DEFAULT_SYMPTOM_WEIGHT = 2

# Expanded emergency vocabulary (Module 2.5).
EMERGENCY_SYMPTOMS = {
    "chest pain",
    "chest tightness",
    "crushing chest pain",
    "severe bleeding",
    "uncontrolled bleeding",
    "severe internal bleeding",
    "vomiting blood",
    "coughing blood",
    "blood in stool",
    "facial drooping",
    "slurred speech",
    "sudden numbness",
    "sudden weakness on one side",
    "loss of consciousness",
    "fainting",
    "difficulty breathing",
    "shortness of breath",
    "severe shortness of breath",
    "rapid breathing",
    "seizures",
    "severe allergic reaction",
    "anaphylaxis",
    "swelling of the throat",
    "sudden vision loss",
    "sudden severe headache",
    "worst headache of life",
    "pain radiating to arm",
    "pain radiating to jaw",
    "cold sweat",
    "bluish lips",
    "blue lips",
    "high fever in infant",
    "stiff neck with fever",
    "thoughts of self-harm",
    "suicidal ideation",
}

EMERGENCY_ALERT_MESSAGE = "Seek immediate medical attention."

MEDICAL_AI_LOG_FILENAME = "medical_ai.log"

REPORT_ANALYSIS_DISCLAIMER = "This analysis is informational only and not a medical diagnosis."
REPORT_ANALYSIS_LOG_FILENAME = "report_analysis.log"
DEFAULT_REPORT_TYPE_LABEL = "General Lab Report"

AUTH_LOG_FILENAME = "auth.log"
HISTORY_LOG_FILENAME = "history.log"

OCR_LOG_FILENAME = "ocr.log"
OCR_SUPPORTED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}
OCR_MIN_CONFIDENCE = 0.0

SYSTEM_LOG_FILENAME = "system.log"
RATE_LIMIT_DEFAULT = "60/minute"
