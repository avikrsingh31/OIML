# import os
# import qrcode
# from fpdf import FPDF
# from flask import Flask, render_template, request, jsonify, send_file
# from sqlalchemy.engine import URL

# from database import db
# from models import Instrument, Inspection

# app = Flask(__name__)

# # Ensure folder exists for generated certificates
# CERT_DIR = os.path.join(os.getcwd(), 'certificates')
# os.makedirs(CERT_DIR, exist_ok=True)

# # MySQL configuration
# USER = "root"
# PASSWORD = "avinash17"
# HOST = "localhost"
# DATABASE = "nawi_database"

# connection_url = URL.create(
#     "mysql+pymysql",
#     username=USER,
#     password=PASSWORD,
#     host=HOST,
#     database=DATABASE
# )

# app.config["SQLALCHEMY_DATABASE_URI"] = connection_url
# app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# # Initialize database and create tables
# db.init_app(app)
# with app.app_context():
#     db.create_all()


# # --- WEB & CALCULATION ROUTES ---

# @app.route("/")
# def home():
#     return render_template("index.html")


# @app.route("/calculate", methods=["POST"])
# def check_weight():
#     data = request.get_json() or {}
#     shop_name = data.get("shop_name", "Unknown Shop")
#     standard = float(data.get("standard", 0))
#     reading = float(data.get("reading", 0))

#     error = round(abs(standard - reading), 3)
#     allowed_error = 2.0

#     if error <= allowed_error:
#         status = "PASS"
#         color = "#28a745"

#         # Generate QR Code
#         qr_data = f"Verified: {shop_name} | Error: {error}g | Status: PASS"
#         qr_path = os.path.join(CERT_DIR, "qr.png")
#         qrcode.make(qr_data).save(qr_path)

#         # Generate Official PDF
#         pdf = FPDF()
#         pdf.add_page()
#         pdf.set_font("Arial", "B", 16)
#         pdf.cell(200, 10, txt="GOVERNMENT OF INDIA - LEGAL METROLOGY", ln=True, align="C")
#         pdf.set_font("Arial", size=12)
#         pdf.cell(200, 10, txt="Verification Certificate (OIML R-76)", ln=True, align="C")
#         pdf.line(10, 30, 200, 30)

#         pdf.ln(10)
#         pdf.cell(200, 10, txt=f"Shop/Entity Name: {shop_name}", ln=True)
#         pdf.cell(200, 10, txt=f"Standard Weight Applied: {standard} g", ln=True)
#         pdf.cell(200, 10, txt=f"Machine Reading: {reading} g", ln=True)
#         pdf.cell(200, 10, txt=f"Detected Error: {error} g", ln=True)
#         pdf.cell(200, 10, txt="Result: APPROVED & STAMPED", ln=True)
#         pdf.image(qr_path, x=150, y=50, w=30)

#         safe_filename = "".join(c for c in shop_name if c.isalnum() or c in (" ", "_", "-")).strip()
#         pdf_filename = f"{safe_filename}_Certificate.pdf"
#         pdf.output(os.path.join(CERT_DIR, pdf_filename))

#         pdf_url = f"/download/{pdf_filename}"
#     else:
#         status = "FAIL - Seized under Sec 25"
#         color = "#dc3545"
#         pdf_url = None

#     # Save search/inspection record to MySQL
#     try:
#         record = Inspection(
#             shop_name=shop_name,
#             standard_weight=standard,
#             reading_weight=reading,
#             error=error,
#             status=status
#         )
#         db.session.add(record)
#         db.session.commit()
#     except Exception as e:
#         db.session.rollback()
#         print(f"Database save error: {e}")

#     return jsonify({
#         "status": status,
#         "error": error,
#         "color": color,
#         "pdf_url": pdf_url
#     })


# @app.route("/download/<path:filename>")
# def download_file(filename):
#     return send_file(os.path.join(CERT_DIR, filename), as_attachment=True)


# # --- REST API ROUTES ---

# @app.route("/api/test")
# def test_api():
#     return jsonify({
#         "status": "success",
#         "message": "Flask API is working"
#     })


# @app.route("/api/inspections", methods=["GET"])
# def get_inspections():
#     inspections = Inspection.query.order_by(Inspection.id.desc()).all()
#     return jsonify([{
#         "id": insp.id,
#         "shop_name": insp.shop_name,
#         "standard_weight": insp.standard_weight,
#         "reading_weight": insp.reading_weight,
#         "error": insp.error,
#         "status": insp.status,
#         "created_at": insp.created_at.strftime("%Y-%m-%d %H:%M:%S") if insp.created_at else None
#     } for insp in inspections])


# @app.route("/api/instruments", methods=["GET"])
# def get_instruments():
#     instruments = Instrument.query.all()
#     return jsonify([{
#         "id": inst.id,
#         "manufacturer": inst.manufacturer,
#         "model": inst.model,
#         "serial_number": inst.serial_number,
#         "max_capacity": inst.max_capacity,
#         "min_capacity": inst.min_capacity,
#         "scale_interval": inst.scale_interval,
#         "accuracy_class": inst.accuracy_class
#     } for inst in instruments])


# @app.route("/api/instruments", methods=["POST"])
# def add_instrument():
#     data = request.get_json() or {}
#     try:
#         instrument = Instrument(
#             manufacturer=data["manufacturer"],
#             model=data["model"],
#             serial_number=data["serial_number"],
#             max_capacity=data.get("max_capacity"),
#             min_capacity=data.get("min_capacity"),
#             scale_interval=data.get("scale_interval"),
#             accuracy_class=data.get("accuracy_class")
#         )
#         db.session.add(instrument)
#         db.session.commit()
#         return jsonify({
#             "status": "success",
#             "message": "Instrument added successfully",
#             "instrument_id": instrument.id
#         }), 201
#     except Exception as e:
#         db.session.rollback()
#         return jsonify({
#             "status": "error",
#             "message": str(e)
#         }), 400


# @app.route("/api/instruments/<int:id>", methods=["GET"])
# def get_instrument(id):
#     instrument = Instrument.query.get(id)
#     if instrument is None:
#         return jsonify({"status": "error", "message": "Instrument not found"}), 404
#     return jsonify({
#         "id": instrument.id,
#         "manufacturer": instrument.manufacturer,
#         "model": instrument.model,
#         "serial_number": instrument.serial_number,
#         "max_capacity": instrument.max_capacity,
#         "min_capacity": instrument.min_capacity,
#         "scale_interval": instrument.scale_interval,
#         "accuracy_class": instrument.accuracy_class
#     })


# @app.route("/api/instruments/<int:id>", methods=["DELETE"])
# def delete_instrument(id):
#     instrument = Instrument.query.get(id)
#     if instrument is None:
#         return jsonify({"status": "error", "message": "Instrument not found"}), 404
#     try:
#         db.session.delete(instrument)
#         db.session.commit()
#         return jsonify({"status": "success", "message": "Instrument deleted successfully"})
#     except Exception as e:
#         db.session.rollback()
#         return jsonify({"status": "error", "message": str(e)}), 400


# if __name__ == "__main__":
#     app.run(debug=True, port=5000)

# import os
# import qrcode
# from fpdf import FPDF
# from flask import Flask, render_template, request, jsonify, send_file, session
# from sqlalchemy.engine import URL

# from database import db
# from models import Instrument, Inspection

# app = Flask(__name__)

# # Session track karne ke liye secret key
# app.secret_key = "nawi_super_secure_secret_key"

# # Inspector credentials (ID aur PIN)
# VALID_INSPECTORS = {
#     "LMO-101": "1234",
#     "ADMIN": "admin123"
# }

# # Certificates save karne ka folder
# CERT_DIR = os.path.join(os.getcwd(), 'certificates')
# os.makedirs(CERT_DIR, exist_ok=True)

# # MySQL configuration
# USER = "root"
# PASSWORD = "avinash17"
# HOST = "localhost"
# DATABASE = "nawi_database"

# # Safe database URL
# connection_url = URL.create(
#     "mysql+pymysql",
#     username=USER,
#     password=PASSWORD,
#     host=HOST,
#     database=DATABASE
# )

# app.config["SQLALCHEMY_DATABASE_URI"] = connection_url
# app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# # Database connect aur tables create karna
# db.init_app(app)
# with app.app_context():
#     db.create_all()


# # --- AUTHENTICATION ROUTES ---

# @app.route("/api/login", methods=["POST"])
# def inspector_login():
#     data = request.get_json() or {}
#     inspector_id = data.get("inspector_id")
#     pin = data.get("pin")

#     if inspector_id in VALID_INSPECTORS and VALID_INSPECTORS[inspector_id] == pin:
#         session["inspector"] = inspector_id
#         return jsonify({"status": "success", "message": "Authenticated"})

#     return jsonify({"status": "error", "message": "Invalid Inspector ID or PIN"}), 401


# @app.route("/api/auth/status", methods=["GET"])
# def auth_status():
#     if "inspector" in session:
#         return jsonify({"logged_in": True, "inspector_id": session["inspector"]})
#     return jsonify({"logged_in": False})


# @app.route("/api/logout", methods=["POST"])
# def inspector_logout():
#     session.pop("inspector", None)
#     return jsonify({"status": "success"})


# # --- WEB & CALCULATION ROUTES ---

# @app.route("/")
# def home():
#     return render_template("index.html")


# @app.route("/calculate", methods=["POST"])
# def check_weight():
#     # Login verification check
#     if "inspector" not in session:
#         return jsonify({"status": "error", "message": "Unauthorized. Please log in."}), 401

#     data = request.get_json() or {}
#     shop_name = data.get("shop_name", "Unknown Shop")
#     standard = float(data.get("standard", 0))
#     reading = float(data.get("reading", 0))

#     error = round(abs(standard - reading), 3)
#     allowed_error = 2.0

#     if error <= allowed_error:
#         status = "PASS"
#         color = "#28a745"

#         # Generate QR Code
#         qr_data = f"Verified: {shop_name} | Error: {error}g | Status: PASS"
#         qr_path = os.path.join(CERT_DIR, "qr.png")
#         qrcode.make(qr_data).save(qr_path)

#         # Generate Official PDF
#         pdf = FPDF()
#         pdf.add_page()
#         pdf.set_font("Arial", "B", 16)
#         pdf.cell(200, 10, txt="GOVERNMENT OF INDIA - LEGAL METROLOGY", ln=True, align="C")
#         pdf.set_font("Arial", size=12)
#         pdf.cell(200, 10, txt="Verification Certificate (OIML R-76)", ln=True, align="C")
#         pdf.line(10, 30, 200, 30)

#         pdf.ln(10)
#         pdf.cell(200, 10, txt=f"Inspector ID: {session.get('inspector')}", ln=True)
#         pdf.cell(200, 10, txt=f"Shop/Entity Name: {shop_name}", ln=True)
#         pdf.cell(200, 10, txt=f"Standard Weight Applied: {standard} g", ln=True)
#         pdf.cell(200, 10, txt=f"Machine Reading: {reading} g", ln=True)
#         pdf.cell(200, 10, txt=f"Detected Error: {error} g", ln=True)
#         pdf.cell(200, 10, txt="Result: APPROVED & STAMPED", ln=True)
#         pdf.image(qr_path, x=150, y=50, w=30)

#         safe_filename = "".join(c for c in shop_name if c.isalnum() or c in (" ", "_", "-")).strip()
#         pdf_filename = f"{safe_filename}_Certificate.pdf"
#         pdf.output(os.path.join(CERT_DIR, pdf_filename))

#         pdf_url = f"/download/{pdf_filename}"
#     else:
#         status = "FAIL - Seized under Sec 25"
#         color = "#dc3545"
#         pdf_url = None

#     # Search / Verification data MySQL database me save karna
#     try:
#         record = Inspection(
#             shop_name=shop_name,
#             standard_weight=standard,
#             reading_weight=reading,
#             error=error,
#             status=status
#         )
#         db.session.add(record)
#         db.session.commit()
#     except Exception as e:
#         db.session.rollback()
#         print(f"Database save error: {e}")

#     return jsonify({
#         "status": status,
#         "error": error,
#         "color": color,
#         "pdf_url": pdf_url
#     })


# @app.route("/download/<path:filename>")
# def download_file(filename):
#     return send_file(os.path.join(CERT_DIR, filename), as_attachment=True)


# # --- REST API ROUTES ---

# @app.route("/api/test")
# def test_api():
#     return jsonify({
#         "status": "success",
#         "message": "Flask API is working"
#     })


# @app.route("/api/inspections", methods=["GET"])
# def get_inspections():
#     inspections = Inspection.query.order_by(Inspection.id.desc()).all()
#     return jsonify([{
#         "id": insp.id,
#         "shop_name": insp.shop_name,
#         "standard_weight": insp.standard_weight,
#         "reading_weight": insp.reading_weight,
#         "error": insp.error,
#         "status": insp.status,
#         "created_at": insp.created_at.strftime("%Y-%m-%d %H:%M:%S") if insp.created_at else None
#     } for insp in inspections])


# @app.route("/api/instruments", methods=["GET"])
# def get_instruments():
#     instruments = Instrument.query.all()
#     return jsonify([{
#         "id": inst.id,
#         "manufacturer": inst.manufacturer,
#         "model": inst.model,
#         "serial_number": inst.serial_number,
#         "max_capacity": inst.max_capacity,
#         "min_capacity": inst.min_capacity,
#         "scale_interval": inst.scale_interval,
#         "accuracy_class": inst.accuracy_class
#     } for inst in instruments])


# @app.route("/api/instruments", methods=["POST"])
# def add_instrument():
#     data = request.get_json() or {}
#     try:
#         instrument = Instrument(
#             manufacturer=data["manufacturer"],
#             model=data["model"],
#             serial_number=data["serial_number"],
#             max_capacity=data.get("max_capacity"),
#             min_capacity=data.get("min_capacity"),
#             scale_interval=data.get("scale_interval"),
#             accuracy_class=data.get("accuracy_class")
#         )
#         db.session.add(instrument)
#         db.session.commit()
#         return jsonify({
#             "status": "success",
#             "message": "Instrument added successfully",
#             "instrument_id": instrument.id
#         }), 201
#     except Exception as e:
#         db.session.rollback()
#         return jsonify({
#             "status": "error",
#             "message": str(e)
#         }), 400


# @app.route("/api/instruments/<int:id>", methods=["GET"])
# def get_instrument(id):
#     instrument = Instrument.query.get(id)
#     if instrument is None:
#         return jsonify({"status": "error", "message": "Instrument not found"}), 404
#     return jsonify({
#         "id": instrument.id,
#         "manufacturer": instrument.manufacturer,
#         "model": instrument.model,
#         "serial_number": instrument.serial_number,
#         "max_capacity": instrument.max_capacity,
#         "min_capacity": instrument.min_capacity,
#         "scale_interval": instrument.scale_interval,
#         "accuracy_class": instrument.accuracy_class
#     })


# @app.route("/api/instruments/<int:id>", methods=["DELETE"])
# def delete_instrument(id):
#     instrument = Instrument.query.get(id)
#     if instrument is None:
#         return jsonify({"status": "error", "message": "Instrument not found"}), 404
#     try:
#         db.session.delete(instrument)
#         db.session.commit()
#         return jsonify({"status": "success", "message": "Instrument deleted successfully"})
#     except Exception as e:
#         db.session.rollback()
#         return jsonify({"status": "error", "message": str(e)}), 400


# if __name__ == "__main__":
#     app.run(debug=True, port=5000)

# import os
# import base64
# import re
# import cv2
# import numpy as np
# import pytesseract
# import qrcode
# from fpdf import FPDF
# from flask import Flask, render_template, request, jsonify, send_file, session
# from sqlalchemy.engine import URL

# from database import db
# from models import Instrument, Inspection

# app = Flask(__name__)

# # Session track karne ke liye secret key
# app.secret_key = "nawi_super_secure_secret_key"

# # Windows Tesseract-OCR default executable path check
# tesseract_default = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
# if os.path.exists(tesseract_default):
#     pytesseract.pytesseract.tesseract_cmd = tesseract_default

# # Inspector credentials (ID aur PIN)
# VALID_INSPECTORS = {
#     "LMO-101": "1234",
#     "ADMIN": "admin123"
# }

# # Certificates save karne ka folder
# CERT_DIR = os.path.join(os.getcwd(), 'certificates')
# os.makedirs(CERT_DIR, exist_ok=True)

# # MySQL configuration
# USER = "root"
# PASSWORD = "avinash17"
# HOST = "localhost"
# DATABASE = "nawi_database"

# # Safe database URL
# connection_url = URL.create(
#     "mysql+pymysql",
#     username=USER,
#     password=PASSWORD,
#     host=HOST,
#     database=DATABASE
# )

# app.config["SQLALCHEMY_DATABASE_URI"] = connection_url
# app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# # Database connect aur tables create karna
# db.init_app(app)
# with app.app_context():
#     db.create_all()


# # --- AUTHENTICATION ROUTES ---

# @app.route("/api/login", methods=["POST"])
# def inspector_login():
#     data = request.get_json() or {}
#     inspector_id = data.get("inspector_id")
#     pin = data.get("pin")

#     if inspector_id in VALID_INSPECTORS and VALID_INSPECTORS[inspector_id] == pin:
#         session["inspector"] = inspector_id
#         return jsonify({"status": "success", "message": "Authenticated"})

#     return jsonify({"status": "error", "message": "Invalid Inspector ID or PIN"}), 401


# @app.route("/api/auth/status", methods=["GET"])
# def auth_status():
#     if "inspector" in session:
#         return jsonify({"logged_in": True, "inspector_id": session["inspector"]})
#     return jsonify({"logged_in": False})


# @app.route("/api/logout", methods=["POST"])
# def inspector_logout():
#     session.pop("inspector", None)
#     return jsonify({"status": "success"})


# # --- CAMERA SCAN (OCR) ROUTE ---

# @app.route("/api/ocr-scan", methods=["POST"])
# def ocr_scan():
#     if "inspector" not in session:
#         return jsonify({"status": "error", "message": "Unauthorized. Please log in."}), 401

#     data = request.get_json() or {}
#     image_data = data.get("image")

#     if not image_data:
#         return jsonify({"status": "error", "message": "No image provided"}), 400

#     try:
#         # Base64 string decode
#         header, encoded = image_data.split(",", 1) if "," in image_data else ("", image_data)
#         img_bytes = base64.b64decode(encoded)
#         img_np = np.frombuffer(img_bytes, np.uint8)
#         img = cv2.imdecode(img_np, cv2.IMREAD_COLOR)

#         # Image preprocessing for LCD/7-segment displays
#         gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
#         gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
#         thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)

#         # Digits and decimals whitelist
#         config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789.'
#         text = pytesseract.image_to_string(thresh, config=config)

#         # Extract numeric weight reading
#         matches = re.findall(r"\d+(?:\.\d+)?", text)
#         if matches:
#             detected_number = matches[0]
#             return jsonify({"status": "success", "detected_value": detected_number})
#         else:
#             return jsonify({"status": "error", "message": "Digits not detected clearly. Try adjusting lighting or distance."}), 422

#     except Exception as e:
#         return jsonify({"status": "error", "message": str(e)}), 500


# # --- WEB & CALCULATION ROUTES ---

# @app.route("/")
# def home():
#     return render_template("index.html")


# @app.route("/calculate", methods=["POST"])
# def check_weight():
#     # Login verification check
#     if "inspector" not in session:
#         return jsonify({"status": "error", "message": "Unauthorized. Please log in."}), 401

#     data = request.get_json() or {}
#     shop_name = data.get("shop_name", "Unknown Shop")
#     standard = float(data.get("standard", 0))
#     reading = float(data.get("reading", 0))

#     error = round(abs(standard - reading), 3)
#     allowed_error = 2.0

#     if error <= allowed_error:
#         status = "PASS"
#         color = "#28a745"

#         # Generate QR Code
#         qr_data = f"Verified: {shop_name} | Error: {error}g | Status: PASS"
#         qr_path = os.path.join(CERT_DIR, "qr.png")
#         qrcode.make(qr_data).save(qr_path)

#         # Generate Official PDF
#         pdf = FPDF()
#         pdf.add_page()
#         pdf.set_font("Arial", "B", 16)
#         pdf.cell(200, 10, txt="GOVERNMENT OF INDIA - LEGAL METROLOGY", ln=True, align="C")
#         pdf.set_font("Arial", size=12)
#         pdf.cell(200, 10, txt="Verification Certificate (OIML R-76)", ln=True, align="C")
#         pdf.line(10, 30, 200, 30)

#         pdf.ln(10)
#         pdf.cell(200, 10, txt=f"Inspector ID: {session.get('inspector')}", ln=True)
#         pdf.cell(200, 10, txt=f"Shop/Entity Name: {shop_name}", ln=True)
#         pdf.cell(200, 10, txt=f"Standard Weight Applied: {standard} g", ln=True)
#         pdf.cell(200, 10, txt=f"Machine Reading: {reading} g", ln=True)
#         pdf.cell(200, 10, txt=f"Detected Error: {error} g", ln=True)
#         pdf.cell(200, 10, txt="Result: APPROVED & STAMPED", ln=True)
#         pdf.image(qr_path, x=150, y=50, w=30)

#         safe_filename = "".join(c for c in shop_name if c.isalnum() or c in (" ", "_", "-")).strip()
#         pdf_filename = f"{safe_filename}_Certificate.pdf"
#         pdf.output(os.path.join(CERT_DIR, pdf_filename))

#         pdf_url = f"/download/{pdf_filename}"
#     else:
#         status = "FAIL - Seized under Sec 25"
#         color = "#dc3545"
#         pdf_url = None

#     # Search / Verification data MySQL database me save karna
#     try:
#         record = Inspection(
#             shop_name=shop_name,
#             standard_weight=standard,
#             reading_weight=reading,
#             error=error,
#             status=status
#         )
#         db.session.add(record)
#         db.session.commit()
#     except Exception as e:
#         db.session.rollback()
#         print(f"Database save error: {e}")

#     return jsonify({
#         "status": status,
#         "error": error,
#         "color": color,
#         "pdf_url": pdf_url
#     })


# @app.route("/download/<path:filename>")
# def download_file(filename):
#     return send_file(os.path.join(CERT_DIR, filename), as_attachment=True)


# # --- REST API ROUTES ---

# @app.route("/api/test")
# def test_api():
#     return jsonify({
#         "status": "success",
#         "message": "Flask API is working"
#     })


# @app.route("/api/inspections", methods=["GET"])
# def get_inspections():
#     inspections = Inspection.query.order_by(Inspection.id.desc()).all()
#     return jsonify([{
#         "id": insp.id,
#         "shop_name": insp.shop_name,
#         "standard_weight": insp.standard_weight,
#         "reading_weight": insp.reading_weight,
#         "error": insp.error,
#         "status": insp.status,
#         "created_at": insp.created_at.strftime("%Y-%m-%d %H:%M:%S") if insp.created_at else None
#     } for insp in inspections])


# @app.route("/api/instruments", methods=["GET"])
# def get_instruments():
#     instruments = Instrument.query.all()
#     return jsonify([{
#         "id": inst.id,
#         "manufacturer": inst.manufacturer,
#         "model": inst.model,
#         "serial_number": inst.serial_number,
#         "max_capacity": inst.max_capacity,
#         "min_capacity": inst.min_capacity,
#         "scale_interval": inst.scale_interval,
#         "accuracy_class": inst.accuracy_class
#     } for inst in instruments])


# @app.route("/api/instruments", methods=["POST"])
# def add_instrument():
#     data = request.get_json() or {}
#     try:
#         instrument = Instrument(
#             manufacturer=data["manufacturer"],
#             model=data["model"],
#             serial_number=data["serial_number"],
#             max_capacity=data.get("max_capacity"),
#             min_capacity=data.get("min_capacity"),
#             scale_interval=data.get("scale_interval"),
#             accuracy_class=data.get("accuracy_class")
#         )
#         db.session.add(instrument)
#         db.session.commit()
#         return jsonify({
#             "status": "success",
#             "message": "Instrument added successfully",
#             "instrument_id": instrument.id
#         }), 201
#     except Exception as e:
#         db.session.rollback()
#         return jsonify({
#             "status": "error",
#             "message": str(e)
#         }), 400


# @app.route("/api/instruments/<int:id>", methods=["GET"])
# def get_instrument(id):
#     instrument = Instrument.query.get(id)
#     if instrument is None:
#         return jsonify({"status": "error", "message": "Instrument not found"}), 404
#     return jsonify({
#         "id": instrument.id,
#         "manufacturer": instrument.manufacturer,
#         "model": instrument.model,
#         "serial_number": instrument.serial_number,
#         "max_capacity": instrument.max_capacity,
#         "min_capacity": instrument.min_capacity,
#         "scale_interval": instrument.scale_interval,
#         "accuracy_class": instrument.accuracy_class
#     })


# @app.route("/api/instruments/<int:id>", methods=["DELETE"])
# def delete_instrument(id):
#     instrument = Instrument.query.get(id)
#     if instrument is None:
#         return jsonify({"status": "error", "message": "Instrument not found"}), 404
#     try:
#         db.session.delete(instrument)
#         db.session.commit()
#         return jsonify({"status": "success", "message": "Instrument deleted successfully"})
#     except Exception as e:
#         db.session.rollback()
#         return jsonify({"status": "error", "message": str(e)}), 400


# if __name__ == "__main__":
#     app.run(debug=True, port=5000)

# import os
# import base64
# import re
# import cv2
# import numpy as np
# import pytesseract
# import qrcode
# from fpdf import FPDF
# from flask import Flask, render_template, request, jsonify, send_file, session
# from sqlalchemy.engine import URL

# from database import db
# from models import Instrument, Inspection

# app = Flask(__name__)

# # Session track karne ke liye secret key
# app.secret_key = "nawi_super_secure_secret_key"

# # Windows Tesseract-OCR default executable path check
# tesseract_default = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
# if os.path.exists(tesseract_default):
#     pytesseract.pytesseract.tesseract_cmd = tesseract_default

# # Inspector credentials (ID aur PIN)
# VALID_INSPECTORS = {
#     "LMO-101": "1234",
#     "ADMIN": "admin123"
# }

# # Certificates save karne ka folder
# CERT_DIR = os.path.join(os.getcwd(), 'certificates')
# os.makedirs(CERT_DIR, exist_ok=True)

# # MySQL configuration
# USER = "root"
# PASSWORD = "avinash17"
# HOST = "localhost"
# DATABASE = "nawi_database"

# # Safe database URL
# connection_url = URL.create(
#     "mysql+pymysql",
#     username=USER,
#     password=PASSWORD,
#     host=HOST,
#     database=DATABASE
# )

# app.config["SQLALCHEMY_DATABASE_URI"] = connection_url
# app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# # Database connect aur tables create karna
# db.init_app(app)
# with app.app_context():
#     db.create_all()


# # --- AUTHENTICATION ROUTES ---

# @app.route("/api/login", methods=["POST"])
# def inspector_login():
#     data = request.get_json() or {}
#     inspector_id = data.get("inspector_id")
#     pin = data.get("pin")

#     if inspector_id in VALID_INSPECTORS and VALID_INSPECTORS[inspector_id] == pin:
#         session["inspector"] = inspector_id
#         return jsonify({"status": "success", "message": "Authenticated"})

#     return jsonify({"status": "error", "message": "Invalid Inspector ID or PIN"}), 401


# @app.route("/api/auth/status", methods=["GET"])
# def auth_status():
#     if "inspector" in session:
#         return jsonify({"logged_in": True, "inspector_id": session["inspector"]})
#     return jsonify({"logged_in": False})


# @app.route("/api/logout", methods=["POST"])
# def inspector_logout():
#     session.pop("inspector", None)
#     return jsonify({"status": "success"})


# # --- CAMERA SCAN (OCR) ROUTE ---

# @app.route("/api/ocr-scan", methods=["POST"])
# def ocr_scan():
#     if "inspector" not in session:
#         return jsonify({"status": "error", "message": "Unauthorized. Please log in."}), 401

#     data = request.get_json() or {}
#     image_data = data.get("image")

#     if not image_data:
#         return jsonify({"status": "error", "message": "No image provided"}), 400

#     try:
#         # Base64 decode
#         header, encoded = image_data.split(",", 1) if "," in image_data else ("", image_data)
#         img_bytes = base64.b64decode(encoded)
#         img_np = np.frombuffer(img_bytes, np.uint8)
#         img = cv2.imdecode(img_np, cv2.IMREAD_COLOR)

#         # Preprocessing LCD/Seven-segment displays ke liye
#         gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
#         gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
#         thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)

#         # Whitelist digits and decimal
#         config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789.'
#         text = pytesseract.image_to_string(thresh, config=config)

#         # Numbers search karein
#         matches = re.findall(r"\d+(?:\.\d+)?", text)
#         if matches:
#             detected_number = matches[0]
#             return jsonify({"status": "success", "detected_value": detected_number})
#         else:
#             return jsonify({"status": "error", "message": "Digits not clear. Please hold steady."}), 422

#     except Exception as e:
#         return jsonify({"status": "error", "message": str(e)}), 500


# # --- WEB & CALCULATION ROUTES ---

# @app.route("/")
# def home():
#     return render_template("index.html")


# @app.route("/calculate", methods=["POST"])
# def check_weight():
#     if "inspector" not in session:
#         return jsonify({"status": "error", "message": "Unauthorized. Please log in."}), 401

#     data = request.get_json() or {}
#     shop_name = data.get("shop_name", "Unknown Shop")
#     standard = float(data.get("standard", 0))
#     reading = float(data.get("reading", 0))

#     error = round(abs(standard - reading), 3)
#     allowed_error = 2.0

#     if error <= allowed_error:
#         status = "PASS"
#         color = "#28a745"

#         # Generate QR Code
#         qr_data = f"Verified: {shop_name} | Error: {error}g | Status: PASS"
#         qr_path = os.path.join(CERT_DIR, "qr.png")
#         qrcode.make(qr_data).save(qr_path)

#         # Generate Official PDF (fpdf2 syntax updated)
#         pdf = FPDF()
#         pdf.add_page()
#         pdf.set_font("helvetica", "B", 16)
#         pdf.cell(w=190, h=10, text="GOVERNMENT OF INDIA - LEGAL METROLOGY", new_x="LMARGIN", new_y="NEXT", align="C")
#         pdf.set_font("helvetica", size=12)
#         pdf.cell(w=190, h=10, text="Verification Certificate (OIML R-76)", new_x="LMARGIN", new_y="NEXT", align="C")
#         pdf.line(10, 30, 200, 30)

#         pdf.ln(10)
#         pdf.cell(w=190, h=8, text=f"Inspector ID: {session.get('inspector')}", new_x="LMARGIN", new_y="NEXT")
#         pdf.cell(w=190, h=8, text=f"Shop/Entity Name: {shop_name}", new_x="LMARGIN", new_y="NEXT")
#         pdf.cell(w=190, h=8, text=f"Standard Weight Applied: {standard} g", new_x="LMARGIN", new_y="NEXT")
#         pdf.cell(w=190, h=8, text=f"Machine Reading: {reading} g", new_x="LMARGIN", new_y="NEXT")
#         pdf.cell(w=190, h=8, text=f"Detected Error: {error} g", new_x="LMARGIN", new_y="NEXT")
#         pdf.cell(w=190, h=8, text="Result: APPROVED & STAMPED", new_x="LMARGIN", new_y="NEXT")
#         pdf.image(qr_path, x=150, y=50, w=30)

#         safe_filename = "".join(c for c in shop_name if c.isalnum() or c in (" ", "_", "-")).strip()
#         pdf_filename = f"{safe_filename}_Certificate.pdf"
#         pdf.output(os.path.join(CERT_DIR, pdf_filename))

#         pdf_url = f"/download/{pdf_filename}"
#     else:
#         status = "FAIL - Seized under Sec 25"
#         color = "#dc3545"
#         pdf_url = None

#     # Save to Database
#     try:
#         record = Inspection(
#             shop_name=shop_name,
#             standard_weight=standard,
#             reading_weight=reading,
#             error=error,
#             status=status
#         )
#         db.session.add(record)
#         db.session.commit()
#     except Exception as e:
#         db.session.rollback()
#         print(f"Database save error: {e}")

#     return jsonify({
#         "status": status,
#         "error": error,
#         "color": color,
#         "pdf_url": pdf_url
#     })


# @app.route("/download/<path:filename>")
# def download_file(filename):
#     return send_file(os.path.join(CERT_DIR, filename), as_attachment=True)


# if __name__ == "__main__":
#     app.run(debug=True, port=5000)

import os
import base64
import re
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

# Tesseract OCR path configuration
tesseract_default = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
if os.path.exists(tesseract_default):
    pytesseract.pytesseract.tesseract_cmd = tesseract_default

# Authorized inspector accounts
VALID_INSPECTORS = {
    "LMO-101": "1234",
    "ADMIN": "admin123"
}

CERT_DIR = os.path.join(os.getcwd(), 'certificates')
os.makedirs(CERT_DIR, exist_ok=True)

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

db.init_app(app)
with app.app_context():
    db.create_all()


# --- AUTHENTICATION ---

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


# --- CAMERA SCAN (OCR) ---

@app.route("/api/ocr-scan", methods=["POST"])
def ocr_scan():
    if "inspector" not in session:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    data = request.get_json() or {}
    image_data = data.get("image")
    if not image_data:
        return jsonify({"status": "error", "message": "No image provided"}), 400

    try:
        header, encoded = image_data.split(",", 1) if "," in image_data else ("", image_data)
        img_bytes = base64.b64decode(encoded)
        img_np = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(img_np, cv2.IMREAD_COLOR)

        # Image processing for digital / 7-segment displays
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
        thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)

        config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789.'
        text = pytesseract.image_to_string(thresh, config=config)

        # Extract numeric values detected in the frame
        matches = re.findall(r"\d+(?:\.\d+)?", text)
        if matches:
            reading = matches[0]
            standard = matches[1] if len(matches) > 1 else None
            return jsonify({
                "status": "success",
                "detected_reading": reading,
                "detected_standard": standard
            })

        return jsonify({"status": "error", "message": "Digits not clearly visible. Please adjust camera distance."}), 422

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# --- CALCULATION & REPORT GENERATION ---

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/calculate", methods=["POST"])
def check_weight():
    if "inspector" not in session:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    data = request.get_json() or {}
    shop_name = data.get("shop_name", "Unknown Shop")
    standard = float(data.get("standard", 0))
    reading = float(data.get("reading", 0))

    error = round(abs(standard - reading), 3)
    allowed_error = 2.0

    if error <= allowed_error:
        status = "PASS"
        color = "#28a745"

        # Generate QR Code
        qr_data = f"Verified: {shop_name} | Error: {error}g | Status: PASS"
        qr_path = os.path.join(CERT_DIR, "qr.png")
        qrcode.make(qr_data).save(qr_path)

        # Generate Official PDF Certificate
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("helvetica", "B", 16)
        pdf.cell(w=190, h=10, text="GOVERNMENT OF INDIA - LEGAL METROLOGY", new_x="LMARGIN", new_y="NEXT", align="C")
        pdf.set_font("helvetica", size=12)
        pdf.cell(w=190, h=10, text="Verification Certificate (OIML R-76)", new_x="LMARGIN", new_y="NEXT", align="C")
        pdf.line(10, 30, 200, 30)

        pdf.ln(10)
        pdf.cell(w=190, h=8, text=f"Inspector ID: {session.get('inspector')}", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(w=190, h=8, text=f"Shop/Entity Name: {shop_name}", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(w=190, h=8, text=f"Standard Weight Applied: {standard} g", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(w=190, h=8, text=f"Machine Reading: {reading} g", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(w=190, h=8, text=f"Detected Error: {error} g", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(w=190, h=8, text="Result: APPROVED & STAMPED", new_x="LMARGIN", new_y="NEXT")
        pdf.image(qr_path, x=150, y=50, w=30)

        safe_filename = "".join(c for c in shop_name if c.isalnum() or c in (" ", "_", "-")).strip()
        pdf_filename = f"{safe_filename}_Certificate.pdf"
        pdf.output(os.path.join(CERT_DIR, pdf_filename))

        pdf_url = f"/download/{pdf_filename}"
    else:
        status = "FAIL - Seized under Sec 25"
        color = "#dc3545"
        pdf_url = None

    # Save to MySQL Database
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

    return jsonify({"status": status, "error": error, "color": color, "pdf_url": pdf_url})


@app.route("/download/<path:filename>")
def download_file(filename):
    return send_file(os.path.join(CERT_DIR, filename), as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True, port=5000)