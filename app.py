import os
import base64
import re
from datetime import datetime

import cv2
import numpy as np
import pytesseract
import qrcode
from fpdf import FPDF
from flask import Flask, render_template, request, jsonify, send_file, session
from sqlalchemy.engine import URL

from database import db
from models import Instrument, Inspection

app = Flask(__name__)
app.secret_key = "nawi_super_secure_secret_key"

# Windows Tesseract-OCR default binary path
tesseract_default = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
if os.path.exists(tesseract_default):
    pytesseract.pytesseract.tesseract_cmd = tesseract_default

# Authorized Inspector Credentials
VALID_INSPECTORS = {
    "LMO-101": "1234",
    "ADMIN": "admin123"
}

# Directories configuration
CERT_DIR = os.path.join(os.getcwd(), 'certificates')
STATIC_DIR = os.path.join(os.getcwd(), 'static')
os.makedirs(CERT_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)

# MySQL configuration
USER = "root"
PASSWORD = "avinash17"
HOST = "localhost"
DATABASE = "nawi_database"

connection_url = URL.create(
    "mysql+pymysql",
    username=USER,
    password=PASSWORD,
    host=HOST,
    database=DATABASE
)

app.config["SQLALCHEMY_DATABASE_URI"] = connection_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Database connect aur tables create karna
db.init_app(app)
with app.app_context():
    db.create_all()


# --- AUTHENTICATION ROUTES ---

@app.route("/api/login", methods=["POST"])
def inspector_login():
    data = request.get_json() or {}
    inspector_id = data.get("inspector_id")
    pin = data.get("pin")

    if inspector_id in VALID_INSPECTORS and VALID_INSPECTORS[inspector_id] == pin:
        session["inspector"] = inspector_id
        return jsonify({"status": "success", "message": "Authenticated"})

    return jsonify({"status": "error", "message": "Invalid Inspector ID or Password"}), 401


@app.route("/api/auth/status", methods=["GET"])
def auth_status():
    if "inspector" in session:
        return jsonify({"logged_in": True, "inspector_id": session["inspector"]})
    return jsonify({"logged_in": False})


@app.route("/api/logout", methods=["POST"])
def inspector_logout():
    session.pop("inspector", None)
    return jsonify({"status": "success"})


# --- MULTI-PASS LCD/7-SEGMENT AI-OCR ROUTE ---

@app.route("/api/ocr-scan", methods=["POST"])
def ocr_scan():
    if "inspector" not in session:
        return jsonify({"status": "error", "message": "Unauthorized. Please log in."}), 401

    data = request.get_json() or {}
    image_data = data.get("image")

    if not image_data:
        return jsonify({"status": "error", "message": "No image provided"}), 400

    try:
        # Base64 string decode
        header, encoded = image_data.split(",", 1) if "," in image_data else ("", image_data)
        img_bytes = base64.b64decode(encoded)
        img_np = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(img_np, cv2.IMREAD_COLOR)

        # 1. Grayscale & Upscaling
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        gray = cv2.resize(gray, None, fx=2.5, fy=2.5, interpolation=cv2.INTER_CUBIC)

        # 2. Contrast Enhancement (CLAHE handles display glare & low contrast)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)

        # 3. Gaussian Blur to bridge 7-segment digital gaps
        blurred = cv2.GaussianBlur(enhanced, (5, 5), 0)

        # 4. Dual Thresholding (Standard Otsu + Inverted)
        _, thresh1 = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        thresh2 = cv2.bitwise_not(thresh1)

        # Target PSMs for sparse/single line instrument displays
        configs = [
            r'--oem 3 --psm 11 -c tessedit_char_whitelist=0123456789.',
            r'--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789.',
            r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789.'
        ]

        extracted_numbers = []

        # Multi-pass execution
        for processed_img in [thresh1, thresh2]:
            for cfg in configs:
                text = pytesseract.image_to_string(processed_img, config=cfg)
                matches = re.findall(r"\b\d+(?:\.\d+)?\b", text)
                if matches:
                    extracted_numbers.extend(matches)
                    break
            if extracted_numbers:
                break

        if extracted_numbers:
            reading = extracted_numbers[0]
            standard = extracted_numbers[1] if len(extracted_numbers) > 1 else None
            return jsonify({
                "status": "success",
                "detected_reading": reading,
                "detected_standard": standard
            })

        return jsonify({
            "status": "error",
            "message": "Digits not clear. Please hold camera closer and steady."
        }), 422

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# --- WEB & VERIFICATION REPORT GENERATION ---

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/calculate", methods=["POST"])
def check_weight():
    if "inspector" not in session:
        return jsonify({"status": "error", "message": "Unauthorized. Please log in."}), 401

    data = request.get_json() or {}
    shop_name = data.get("shop_name", "Unknown Shop").strip()
    standard = float(data.get("standard", 0))
    reading = float(data.get("reading", 0))

    error = round(abs(standard - reading), 3)
    allowed_error = 2.0
    issue_date = datetime.now().strftime("%d-%b-%Y %H:%M")
    cert_no = f"LM-GOI-{datetime.now().strftime('%Y%m')}-{os.urandom(2).hex().upper()}"

    if error <= allowed_error:
        status = "PASS"
        color = "#28a745"

        # 1. Generate QR Code
        qr_data = (
            f"Govt of India | Legal Metrology\n"
            f"Cert No: {cert_no}\n"
            f"Entity: {shop_name}\n"
            f"Standard: {standard}g | Reading: {reading}g\n"
            f"Status: APPROVED\n"
            f"Date: {issue_date}"
        )
        qr_path = os.path.join(CERT_DIR, "qr.png")
        qrcode.make(qr_data).save(qr_path)

        # 2. Build High-Quality Official Government PDF
        pdf = FPDF(orientation="P", unit="mm", format="A4")
        pdf.add_page()

        # Double Decorative Borders
        pdf.set_line_width(0.8)
        pdf.rect(x=8, y=8, w=194, h=281)
        pdf.set_line_width(0.3)
        pdf.rect(x=10, y=10, w=190, h=277)

        # Emblem Logo (falls back gracefully if image absent)
        emblem_path = os.path.join(STATIC_DIR, 'emblem.png')
        if os.path.exists(emblem_path):
            pdf.image(emblem_path, x=95, y=13, w=20)
            pdf.ln(25)
        else:
            pdf.ln(10)

        # Header Titles
        pdf.set_font("helvetica", "B", 15)
        pdf.set_text_color(0, 51, 102)
        pdf.cell(w=190, h=7, text="GOVERNMENT OF INDIA", new_x="LMARGIN", new_y="NEXT", align="C")

        pdf.set_font("helvetica", "B", 11)
        pdf.set_text_color(40, 40, 40)
        pdf.cell(w=190, h=6, text="DEPARTMENT OF CONSUMER AFFAIRS - LEGAL METROLOGY DIVISION", new_x="LMARGIN", new_y="NEXT", align="C")

        pdf.set_font("helvetica", "", 9)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(w=190, h=5, text="Verification Certificate under Standards of Weights & Measures (OIML R-76)", new_x="LMARGIN", new_y="NEXT", align="C")

        # Blue Divider Line
        pdf.set_draw_color(0, 51, 102)
        pdf.set_line_width(0.5)
        pdf.line(20, 56, 190, 56)

        # Metadata Row
        pdf.ln(8)
        pdf.set_text_color(50, 50, 50)
        pdf.set_font("helvetica", "B", 9)
        pdf.cell(w=95, h=6, text=f"Certificate ID: {cert_no}", new_x="RIGHT")
        pdf.cell(w=95, h=6, text=f"Date & Time: {issue_date}", new_x="LMARGIN", new_y="NEXT", align="R")

        # Table Header
        pdf.ln(5)
        pdf.set_fill_color(0, 51, 102)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("helvetica", "B", 10)
        pdf.cell(w=170, h=8, text="  INSPECTION & CALIBRATION RECORD", new_x="LMARGIN", new_y="NEXT", fill=True)

        def add_table_row(field, value, is_even=False):
            pdf.set_fill_color(245, 247, 250) if is_even else pdf.set_fill_color(255, 255, 255)
            pdf.set_text_color(50, 50, 50)
            pdf.set_font("helvetica", "B", 9)
            pdf.cell(w=75, h=8, text=f"  {field}", border=1, new_x="RIGHT", fill=is_even)
            pdf.set_font("helvetica", "", 9)
            pdf.cell(w=95, h=8, text=f"  {value}", border=1, new_x="LMARGIN", new_y="NEXT", fill=is_even)

        add_table_row("Entity / Establishment Name", shop_name, is_even=False)
        add_table_row("Inspecting Officer ID", str(session.get('inspector')), is_even=True)
        add_table_row("Standard Working Mass Applied", f"{standard} g", is_even=False)
        add_table_row("Instrument Reading Output", f"{reading} g", is_even=True)
        add_table_row("Calculated Error (E)", f"{error} g", is_even=False)
        add_table_row("Max Permissible Error (MPE)", "+/- 2.0 g", is_even=True)
        add_table_row("Verification Verdict", "PASSED & DIGITALLY STAMPED", is_even=False)

        # Seal Box with QR Code
        pdf.ln(10)
        pdf.set_draw_color(200, 200, 200)
        pdf.rect(x=20, y=140, w=170, h=52)

        pdf.image(qr_path, x=24, y=144, w=44)

        pdf.set_xy(72, 145)
        pdf.set_font("helvetica", "B", 11)
        pdf.set_text_color(0, 100, 0)
        pdf.cell(w=110, h=6, text="DIGITALLY VERIFIED AND SEALED", new_x="LMARGIN", new_y="NEXT")

        pdf.set_xy(72, 153)
        pdf.set_font("helvetica", "", 8)
        pdf.set_text_color(80, 80, 80)
        pdf.multi_cell(w=110, h=4, text="This equipment complies with statutory provisions of Legal Metrology Act, 2009. The non-automatic weighing instrument is certified for commercial trade usage.\nScan the QR code to authenticate verification records on the national portal.")

        # Officer Signature Area
        pdf.set_xy(110, 215)
        pdf.set_font("helvetica", "B", 9)
        pdf.set_text_color(30, 30, 30)
        pdf.cell(w=75, h=5, text="Authorised Legal Metrology Officer", new_x="LMARGIN", new_y="NEXT", align="C")
        pdf.set_xy(110, 220)
        pdf.set_font("helvetica", "", 8)
        pdf.cell(w=75, h=4, text="Govt. of India, Inspection Directorate", new_x="LMARGIN", new_y="NEXT", align="C")

        # Footer Notice
        pdf.set_xy(10, 270)
        pdf.set_font("helvetica", "I", 7)
        pdf.set_text_color(130, 130, 130)
        pdf.cell(w=190, h=4, text="System generated certificate under Rule 11. No physical signature required if digitally sealed.", align="C")

        safe_filename = "".join(c for c in shop_name if c.isalnum() or c in (" ", "_", "-")).strip()
        pdf_filename = f"{safe_filename}_Certificate.pdf"
        pdf.output(os.path.join(CERT_DIR, pdf_filename))

        pdf_url = f"/download/{pdf_filename}"
    else:
        status = "FAIL - Seized under Sec 25"
        color = "#dc3545"
        pdf_url = None

    # Save Inspection to Database
    try:
        record = Inspection(
            shop_name=shop_name,
            standard_weight=standard,
            reading_weight=reading,
            error=error,
            status=status
        )
        db.session.add(record)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Database save error: {e}")

    return jsonify({
        "status": status,
        "error": error,
        "color": color,
        "pdf_url": pdf_url
    })


@app.route("/download/<path:filename>")
def download_file(filename):
    return send_file(os.path.join(CERT_DIR, filename), as_attachment=True)


# --- REST API ROUTES ---

@app.route("/api/test")
def test_api():
    return jsonify({
        "status": "success",
        "message": "Flask API is working"
    })


@app.route("/api/inspections", methods=["GET"])
def get_inspections():
    inspections = Inspection.query.order_by(Inspection.id.desc()).all()
    return jsonify([{
        "id": insp.id,
        "shop_name": insp.shop_name,
        "standard_weight": insp.standard_weight,
        "reading_weight": insp.reading_weight,
        "error": insp.error,
        "status": insp.status,
        "created_at": insp.created_at.strftime("%Y-%m-%d %H:%M:%S") if insp.created_at else None
    } for insp in inspections])


@app.route("/api/instruments", methods=["GET"])
def get_instruments():
    instruments = Instrument.query.all()
    return jsonify([{
        "id": inst.id,
        "manufacturer": inst.manufacturer,
        "model": inst.model,
        "serial_number": inst.serial_number,
        "max_capacity": inst.max_capacity,
        "min_capacity": inst.min_capacity,
        "scale_interval": inst.scale_interval,
        "accuracy_class": inst.accuracy_class
    } for inst in instruments])


@app.route("/api/instruments", methods=["POST"])
def add_instrument():
    data = request.get_json() or {}
    try:
        instrument = Instrument(
            manufacturer=data["manufacturer"],
            model=data["model"],
            serial_number=data["serial_number"],
            max_capacity=data.get("max_capacity"),
            min_capacity=data.get("min_capacity"),
            scale_interval=data.get("scale_interval"),
            accuracy_class=data.get("accuracy_class")
        )
        db.session.add(instrument)
        db.session.commit()
        return jsonify({
            "status": "success",
            "message": "Instrument added successfully",
            "instrument_id": instrument.id
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400


@app.route("/api/instruments/<int:id>", methods=["GET"])
def get_instrument(id):
    instrument = Instrument.query.get(id)
    if instrument is None:
        return jsonify({"status": "error", "message": "Instrument not found"}), 404
    return jsonify({
        "id": instrument.id,
        "manufacturer": instrument.manufacturer,
        "model": instrument.model,
        "serial_number": instrument.serial_number,
        "max_capacity": instrument.max_capacity,
        "min_capacity": instrument.min_capacity,
        "scale_interval": instrument.scale_interval,
        "accuracy_class": instrument.accuracy_class
    })


@app.route("/api/instruments/<int:id>", methods=["DELETE"])
def delete_instrument(id):
    instrument = Instrument.query.get(id)
    if instrument is None:
        return jsonify({"status": "error", "message": "Instrument not found"}), 404
    try:
        db.session.delete(instrument)
        db.session.commit()
        return jsonify({"status": "success", "message": "Instrument deleted successfully"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 400


if __name__ == "__main__":
    app.run(debug=True, port=5000)