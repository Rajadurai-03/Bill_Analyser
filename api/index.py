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
        data = {
            "docName": file.filename[:15],
            "month": "Unknown",
            "price": 0.0,
            "consumption": 0.0,
            "demand": 0.0,
            "fixed_charges": 0.0,
            "energy_charges": 0.0,
            "demand_penalty": 0.0,
            "subsidies": 0.0
        }

        try:
            with pdfplumber.open(file) as pdf:
                text = "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])

            # 1. Extract Month
            m = re.search(r"Bill month:[\s]*([A-Za-z]+-\d{4})", text, re.IGNORECASE)
            if m: data["month"] = m.group(1).upper()

            # 2. Extract Net Payable
            p = re.search(r"NET BILL PAYABLE[\s]*([\d\.]+)", text, re.IGNORECASE)
            if p: data["price"] = float(p.group(1))

            # 3. Extract Peak Demand (Finds all "Net Max Demand" and takes the highest)
            d_matches = re.findall(r"Net Max Demand[\s]*([\d\.]+)", text, re.IGNORECASE)
            if d_matches:
                data["demand"] = max([float(d) for d in d_matches])

            # 4. Extract Consumption (Finds all "Net Units Supplied" and sums them)
            c_matches = re.findall(r"Net Units Supplied[\s]*([\d\.]+)", text, re.IGNORECASE)
            if c_matches:
                data["consumption"] = sum([float(c) for c in c_matches])

            # 5. Cost Structure Calculation (Directly from Python, not JS)
            # Standard Contract Demand is 2500. Fixed Rate is approx 631.
            data["fixed_charges"] = 2500 * 631
            
            if data["demand"] > 2500:
                data["demand_penalty"] = (data["demand"] - 2500) * 631 * 1.3
                
            # Estimate Energy charges and calculate true subsidies based on the final price
            data["energy_charges"] = data["price"] * 1.15 
            data["subsidies"] = data["price"] - (data["fixed_charges"] + data["demand_penalty"] + data["energy_charges"])

        except Exception as e:
            print(f"Error parsing {file.filename}: {e}")

        results.append(data)

    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True)
