from flask import Flask, request, jsonify
import pdfplumber
import re

app = Flask(__name__)

@app.route('/', methods=['GET'])
@app.route('/api/analyze', methods=['GET'])
def health_check():
    return jsonify({"status": "Python Backend is ONLINE and ready!"}), 200

@app.route('/', methods=['POST'])
@app.route('/api/analyze', methods=['POST'])
def analyze():
    if 'files' not in request.files:
        return jsonify({"error": "No files provided"}), 400

    files = request.files.getlist('files')
    results = []

    for file in files:
        # Default values are now exactly 0 (No more random fake data)
        extracted_data = {
            "docName": file.filename[:15],
            "month": "Unknown Month",
            "price": 0,
            "consumption": 0,
            "demand": 0
        }

        try:
            with pdfplumber.open(file) as pdf:
                full_text = ""
                for page in pdf.pages:
                    extracted = page.extract_text()
                    if extracted:
                        full_text += extracted + "\n"

            # 1. Extract Month (Hunts for 'November-2025' or 'NOV-2025')
            month_match = re.search(r"([a-zA-Z]+-20\d{2})", full_text)
            if month_match:
                extracted_data["month"] = month_match.group(1)

            # 2. Extract Price (Hunts for 'Net Payable' or 'Amount Payable')
            price_match = re.search(r"(?:Payable|Net Bill Amount|Net Amount).*?₹?\s*([\d,]+(?:\.\d{1,2})?)", full_text, re.IGNORECASE)
            if price_match: 
                extracted_data["price"] = float(price_match.group(1).replace(",", ""))

            # 3. Extract Consumption (Hunts for 'Energy Consumed (KWH)' or just large KWH numbers)
            cons_match = re.search(r"(?:Energy Consumed|KWH|Total Units).*?(?:[:\s])([\d,]+)", full_text, re.IGNORECASE)
            if cons_match: 
                extracted_data["consumption"] = int(cons_match.group(1).replace(",", ""))

            # 4. Extract Peak Demand (Hunts for 'Billing Demand' or 'Cont. Demand')
            demand_match = re.search(r"(?:Billing Demand|Cont\.? Demand|Demand).*?(?:[:\s])([\d,]+)", full_text, re.IGNORECASE)
            if demand_match: 
                extracted_data["demand"] = int(demand_match.group(1).replace(",", ""))

        except Exception as e:
            print(f"Extraction failed for {file.filename}: {str(e)}")

        results.append(extracted_data)

    return jsonify(results)

app.debug = True
