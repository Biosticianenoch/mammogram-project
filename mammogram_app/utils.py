import os
import numpy as np
import threading
from PIL import Image
from fpdf import FPDF
import datetime
import tempfile
import tflite_runtime.interpreter as tflite

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "mammogram_model.tflite")

_interpreter = None
_model_lock = threading.Lock()

def get_interpreter():
    """Load TFLite model lazily to save memory."""
    global _interpreter
    with _model_lock:
        if _interpreter is None:
            print("📦 Loading TFLite model...")
            _interpreter = tflite.Interpreter(model_path=MODEL_PATH)
            _interpreter.allocate_tensors()
    return _interpreter

def preprocess_and_predict(image_path):
    """Preprocess image and predict using TFLite model."""
    image = Image.open(image_path).convert("L").resize((256, 256))
    img_array = np.array(image, dtype=np.float32).reshape(1, 256, 256, 1) / 255.0

    interpreter = get_interpreter()
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()

    interpreter.set_tensor(input_details[0]['index'], img_array)
    interpreter.invoke()
    prediction = interpreter.get_tensor(output_details[0]['index'])[0][0]

    label = "Malignant (Cancerous)" if prediction > 0.5 else "Benign (Non-cancerous)"
    confidence = prediction if prediction > 0.5 else 1 - prediction
    return label, f"{confidence:.2%}"

def generate_pdf(label, confidence):
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
