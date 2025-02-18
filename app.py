from flask import Flask, render_template, request, jsonify
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import os

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

THRESHOLDS = {
    "pH": (6.5, 8.5),  # Safe range for drinking water
    "Turbidity": (0, 5),  # NTU (Nephelometric Turbidity Units)
    "Dissolved Oxygen": (5, 14),  # mg/L
    "Nitrate": (0, 10)  # mg/L
}

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "No file part"})
    
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"})

    if not file.filename.endswith(".csv"):
        return jsonify({"error": "Invalid file type. Please upload a CSV file."})

    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)

    try:
        df = pd.read_csv(filepath)
        alerts = []
        
        for column, (min_val, max_val) in THRESHOLDS.items():
            if column in df.columns:
                unsafe_values = df[(df[column] < min_val) | (df[column] > max_val)][column]
                if not unsafe_values.empty:
                    alerts.append(f"Warning! {column} is out of safe range in some readings.")
        
        plot_filepath = os.path.join("static", "water_quality_chart.png")
        plt.figure(figsize=(10, 6))
        sns.set_style("whitegrid")
        
        for column in df.columns[1:]:  # Skip first column (assumed to be time/date)
            sns.lineplot(data=df, x=df.columns[0], y=column, marker="o", linewidth=2, label=column)
            
        plt.title("Water Quality Parameters Over Time", fontsize=14, fontweight="bold")
        plt.xlabel("Time", fontsize=12)
        plt.ylabel("Parameter Values", fontsize=12)
        plt.xticks(rotation=45)
        plt.legend()
        plt.grid(True, linestyle="--", alpha=0.7)
        plt.savefig(plot_filepath, bbox_inches="tight")
        plt.close()

        return render_template("index.html", image_url=plot_filepath, alerts=alerts)

    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == "__main__":
    app.run(debug=True)
