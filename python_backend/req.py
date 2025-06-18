import requests
import time
import os

pdf_path = r"C:\project\satori_xr_report_summarizer\python_backend\data\input_pdfs\1737011904_Snapshot-of-Indias-Oil-and-Gas-Data_WebUpload_December-2024_compressed.pdf"
upload_url = "http://localhost:8000/process-pdf/"
output_dir = r"C:\project\satori_xr_report_summarizer\python_backend\data\output_summaries"

# Upload PDF
with open(pdf_path, "rb") as f:
    files = {"file": (os.path.basename(pdf_path), f, "application/pdf")}
    response = requests.post(upload_url, files=files)

if not response.ok:
    print("❌ Upload failed:", response.status_code, response.text)
    exit(1)

print("✅ Upload successful.")

# Construct expected summary filename and path
filename = os.path.splitext(os.path.basename(pdf_path))[0] + "_summary.txt"
output_path = os.path.join(output_dir, filename)

# Wait for summary file to appear (max wait time 30 seconds)
max_wait = 30
waited = 0
interval = 2

print("⏳ Waiting for summary file to be saved locally...")

while waited < max_wait:
    if os.path.isfile(output_path):
        print(f"✅ Summary saved to: {output_path}")
        break
    time.sleep(interval)
    waited += interval
else:
    print(f"❌ Summary file not found after waiting {max_wait} seconds.")
