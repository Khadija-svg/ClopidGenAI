import gradio as gr
import requests

# API settings
API_KEY = "sk-or-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"  
API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL_NAME = "mistralai/magistral-medium-2506"  

def analyze_patient(age, gender, ethnicity, genotype, smoker, history, height_cm, weight_kg, bmi):
    genotype = genotype.lower().replace(" ", "")
    if "*2/*2" in genotype or "*2/*3" in genotype or "*3/*3" in genotype:
        metabolizer = "Poor metabolizer"
        drug_suitability = "Clopidogrel may be less effective; consider alternatives."
    elif "*1/*2" in genotype or "*1/*3" in genotype:
        metabolizer = "Intermediate metabolizer"
        drug_suitability = "Effectiveness may be reduced; monitor closely."
    elif "*1/*1" in genotype:
        metabolizer = "Extensive metabolizer"
        drug_suitability = "Clopidogrel likely effective."
    else:
        metabolizer = "Unknown metabolizer status"
        risk_factors = []
        if smoker.lower() == "yes":
            risk_factors.append("smoking")
        if age > 65:
            risk_factors.append("advanced age")
        if "diabetes" in history.lower():
            risk_factors.append("diabetes")
        if "heart disease" in history.lower():
            risk_factors.append("heart disease")

        if risk_factors:
            drug_suitability = (
                f"Genotype unknown; risk factors present ({', '.join(risk_factors)}), use cautiously."
            )
        else:
            drug_suitability = "Genotype unknown; standard treatment may be considered."

    alerts = []
    if smoker.lower() == "yes":
        alerts.append("Patient is a smoker.")
    if age > 65:
        alerts.append("Patient is older than 65.")
    if "diabetes" in history.lower():
        alerts.append("Patient has diabetes.")
    if "heart disease" in history.lower():
        alerts.append("Patient has heart disease.")

    report = f"""Patient metabolizer status: {metabolizer}
Clopidogrel suitability: {drug_suitability}

Alerts:"""
    if alerts:
        for alert in alerts:
            report += f"\n- {alert}"
    else:
        report += "\n- None"

    report += f"\n\nPatient metrics: Height {height_cm} cm, Weight {weight_kg} kg, BMI {bmi:.1f}"
    report += "\n\n⚠️ This assessment is not a substitute for medical tests or professional consultation."

    return report.strip()


def query_model(age, gender, ethnicity, genotype, smoker, history, height_cm, weight_kg, bmi):
    local_report = analyze_patient(age, gender, ethnicity, genotype, smoker, history, height_cm, weight_kg, bmi)

    prompt = f"""
Given the following patient information:
- Age: {age}
- Gender: {gender}
- Ethnicity: {ethnicity}
- Genotype: {genotype}
- Smoker: {smoker}
- Medical History: {history}
- Height: {height_cm} cm
- Weight: {weight_kg} kg
- BMI: {bmi:.1f}

Please provide a concise and clear clinical summary on the likelihood of Clopidogrel effectiveness. 
Focus on key points only, such as genotype impact, risk factors, and recommendations, 
using bullet points suitable for a healthcare professional.
Only output clean English text without any strange or non-English characters.
"""

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": MODEL_NAME,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 300
    }

    try:
        response = requests.post(API_URL, json=payload, headers=headers, timeout=15)
        if response.status_code == 200:
            ai_response = response.json()["choices"][0]["message"]["content"]
        else:
            ai_response = f"❌ API Error: {response.status_code}\n{response.text}"
    except Exception as e:
        ai_response = f"❌ Exception: {e}"

    final_report = f"{local_report}\n\n[AI Model Explanation]\n{ai_response}"
    return final_report



with gr.Blocks(title="Clopidogrel AI Predictor") as demo:
    gr.Markdown("## 💊 Clopidogrel Effectiveness Predictor (for Healthcare Use Only)")

    with gr.Row():
        age = gr.Number(label="Age", value=45)
        gender = gr.Dropdown(["Male", "Female", "Other"], label="Gender")
        ethnicity = gr.Textbox(label="Ethnicity", placeholder="e.g., Caucasian, Asian...")
    
    with gr.Row():
        height_cm = gr.Number(label="Height (cm)", value=170)
        weight_kg = gr.Number(label="Weight (kg)", value=70)
        bmi = gr.Number(label="BMI", value=24.2, interactive=False)

    with gr.Row():
        genotype = gr.Textbox(label="Genotype", placeholder="e.g., CYP2C19*2/*2")
        smoker = gr.Radio(["Yes", "No"], label="Smoker?")
        history = gr.Textbox(label="Medical History", lines=3, placeholder="Short summary...")

    submit = gr.Button("🧠 Analyze")

    output = gr.Textbox(label="Model's Response", lines=15)

    def calculate_bmi(height, weight):
        try:
            h_m = height / 100
            bmi_val = weight / (h_m * h_m)
            return round(bmi_val, 1)
        except:
            return 0

    height_cm.change(fn=lambda h, w: calculate_bmi(h, weight_kg.value), inputs=[height_cm, weight_kg], outputs=bmi)
    weight_kg.change(fn=lambda h, w: calculate_bmi(height_cm.value, w), inputs=[height_cm, weight_kg], outputs=bmi)

    submit.click(
        query_model,
        inputs=[age, gender, ethnicity, genotype, smoker, history, height_cm, weight_kg, bmi],
        outputs=output
    )

demo.launch(share=True)

