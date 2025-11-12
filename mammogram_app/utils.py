import os
import numpy as np
from tensorflow.keras.models import load_model
from PIL import Image
from fpdf import FPDF
import datetime
import tempfile
import threading

# ✅ Resolve model path relative to the project base directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "mammogram_model.keras")

# ✅ Thread-safe lazy model loading
_model = None
_model_lock = threading.Lock()

def get_model():
    """Load and cache the model lazily to avoid memory overload on startup."""
    global _model
    with _model_lock:
        if _model is None:
            print("📦 Loading model for the first time...")
            _model = load_model(MODEL_PATH)
    return _model


# ------------------- Prediction Function -------------------
def preprocess_and_predict(image_path):
    """Preprocess uploaded mammogram image and predict cancer likelihood."""
    image = Image.open(image_path).convert("L")  # convert to grayscale
    image = image.resize((256, 256))
    img_array = np.array(image) / 255.0
    img_array = img_array.reshape(1, 256, 256, 1)

    model = get_model()  # ✅ Load only when needed
    prediction = model.predict(img_array)[0][0]
    label = "Malignant (Cancerous)" if prediction > 0.5 else "Benign (Non-cancerous)"
    confidence = prediction if prediction > 0.5 else 1 - prediction
    return label, f"{confidence:.2%}"


# ------------------- PDF Report Generator -------------------
def generate_pdf(label, confidence):
    """Generate a PDF report with prediction result and confidence."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=14)
    pdf.cell(200, 10, txt="Mammogram Cancer Prediction Report", ln=1, align="C")
    pdf.ln(10)
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Prediction Result: {label}", ln=1)
    pdf.cell(200, 10, txt=f"Confidence Score: {confidence}", ln=2)
    pdf.cell(
        200, 10,
        txt=f"Date Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        ln=3
    )

    temp_dir = tempfile.gettempdir()
    pdf_path = os.path.join(temp_dir, "prediction_report.pdf")
    pdf.output(pdf_path)
    return pdf_path
