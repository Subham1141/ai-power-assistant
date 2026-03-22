import os
import json
from flask import Flask, render_template, request, jsonify
from google import genai

app = Flask(__name__)

# Initialize the Gemini Client. 
# Ensure you have your API key set in the environment before running.

def analyze_electrical_state(voltage, current, load):
    """
    Apply engineering logic to detect electrical faults and calculate efficiency.
    Returns: fault_type, context, power, efficiency_tip
    """
    try:
        vi = float(voltage)
        ci = float(current)
    except ValueError:
        return "Invalid Input", "Voltage and current must be valid numbers.", 0, ""

    # Calculate core power draw (W)
    power = vi * ci

    # Smart Efficiency Logic
    if power > 2000:
        eff_tip = "High consumption. Optimize usage to reduce thermal stress and energy costs."
    elif power < 500:
        eff_tip = "Efficient operation. Minimal thermal and energy losses detected."
    else:
        eff_tip = "Moderate usage. Sustaining acceptable energy efficiency."

    # Fault Detection Logic
    if vi > 250:
        return "Overvoltage", f"Voltage ({vi}V) exceeds the maximum safe limit of 250V.", power, eff_tip
    elif vi < 180:
        return "Undervoltage", f"Voltage ({vi}V) is below the minimum required 180V.", power, eff_tip
    elif load.lower() == 'high' and ci > 8:
        return "Overload", f"Current ({ci}A) on High load exceeds the safe capacity of 8A.", power, eff_tip
    else:
        return "Normal Operation", "System limits and load are within safe parameters.", power, eff_tip

def generate_ai_insights(voltage, current, load, fault_type, context, power):
    """
    Call Google Gemini API using the latest google-genai SDK 
    to generate EEE context and practical recommendations in structured JSON format.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        # Fallback simulated response if no API key is provided
        return json.dumps({
            "explanation": "API Key Missing: Please set the GEMINI_API_KEY environment variable.",
            "reasoning": "Without an API key, the system cannot contact the generative model.",
            "recommendation": "Configure your environment variable and restart the server.",
            "efficiency": "N/A",
            "safety": "Ensure proper API configuration before relying on AI insights."
        })

    try:
        # Using the latest SDK structure
        client = genai.Client(api_key=api_key)
        
        prompt = f"""
You are an expert Electrical and Electronics Engineer (EEE) assistant in a hackathon project called 'AI Power Assistant'.
Analyze the following electrical system reading:
- Voltage: {voltage} V
- Current: {current} A
- Power Draw: {power} W
- Load Profile: {load}

System Diagnostic: {fault_type}
Details: {context}

Provide your response STRICTLY as a valid JSON object without markdown formatting blocks or backticks, containing exactly these keys:
"explanation": "Brief explanation of what this state means in simple terms."
"reasoning": "The technical engineering 'why' behind this state or fault."
"recommendation": "A practical, real-world solution or operational fix."
"efficiency": "A specific efficiency suggestion based on this power draw."
"safety": "Specific safety advice related to this situation."
"""
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        text = response.text.strip()
        if text.startswith('```json'): text = text[7:]
        if text.startswith('```'): text = text[3:]
        if text.endswith('```'): text = text[:-3]
        return text.strip()
    except Exception as e:
        return json.dumps({
            "explanation": "AI Analysis Error",
            "reasoning": str(e),
            "recommendation": "Backend failed to process API request.",
            "efficiency": "Check network stability.",
            "safety": "Please verify your Gemini API key and network connection."
        })

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.json
    voltage = data.get('voltage')
    current = data.get('current')
    load = data.get('load')

    if voltage is None or current is None or not load:
        return jsonify({'error': 'Please provide all required inputs: voltage, current, and load.'}), 400

    fault_type, context, power, eff_tip = analyze_electrical_state(voltage, current, load)
    
    if fault_type == "Invalid Input":
        return jsonify({'error': context}), 400

    ai_insights = generate_ai_insights(voltage, current, load, fault_type, context, power)

    return jsonify({
        'fault_type': fault_type,
        'context': context,
        'power': power,
        'efficiency_tip': eff_tip,
        'ai_insights': ai_insights
    })

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)