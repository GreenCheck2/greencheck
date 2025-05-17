from flask import Flask, render_template, request, send_file, make_response, redirect, url_for, Response, session, flash
from datetime import datetime, timedelta
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import io
import os
import time
import json
import smtplib
from email.message import EmailMessage

from functools import wraps

app = Flask(__name__)

app.secret_key = 'greencheck_super_secret_key'  # Required for session management

# ✅ LOGIN REQUIRED DECORATOR
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            flash("Please log in to access GreenCheck.")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# ✅ EMAIL CONFIG
EMAIL_ADDRESS = "greencheckreports@gmail.com"
EMAIL_PASSWORD = "hdgd xpgs seyk konx"

from compliance_rules import check_compliance

def generate_pdf(product):
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)

    logo_path = os.path.join("static", "greencheck_logo.png")
    if os.path.exists(logo_path):
        logo = ImageReader(logo_path)
        pdf.drawImage(logo, 230, 655, width=150, height=150, mask='auto')

    y = 650
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawCentredString(300, y, "GreenCheck™ Compliance Report")
    y -= 20
    pdf.setFont("Helvetica", 10)
    pdf.drawCentredString(300, y, f"Verified Product Analysis – Generated {time.strftime('%Y-%m-%d %H:%M:%S')}")
    y -= 40

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(40, y, "Product Details")
    y -= 20
    pdf.setFont("Helvetica", 11)

    def write_line(label, value):
        nonlocal y
        pdf.drawString(50, y, f"{label}: {value}")
        y -= 18

    write_line("Product Name", product['name'])
    write_line("State", product['state'])
    write_line("Type", product['product_type'])
    write_line("THC %", product['thc'])
    write_line("THC per Serving (mg)", product['thc_per_serving'])
    write_line("CBD %", product['cbd'])
    write_line("CBN %", product['cbn'])
    write_line("Net Weight (grams)", product['weight_grams'])
    write_line("Packaged Date", product['packaged_date'])
    write_line("Batch ID", product['batch_id'])
    write_line("Includes Warning Label", "Yes" if product['warning_label'] else "No")

    y -= 15
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(40, y, "Compliance Results:")
    y -= 20
    pdf.setFont("Helvetica", 11)

    for line in product['results']:
        pdf.drawString(60, y, line)
        y -= 15
        if y < 60:
            pdf.showPage()
            y = 750

    pdf.save()
    buffer.seek(0)
    return buffer

# ✅ EMAIL FUNCTION
def send_report_email(to_email, product, pdf_data):
    msg = EmailMessage()
    msg['Subject'] = f"GreenCheck Report – {product['name']}"
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = to_email

    msg.set_content(f"Hi,\n\nAttached is your GreenCheck compliance report for {product['name']}.\n\nThanks,\nGreenCheck Team")

    pdf_filename = f"{product['name'].replace(' ', '_')}_GreenCheck_Report.pdf"
    msg.add_attachment(pdf_data.read(), maintype='application', subtype='pdf', filename=pdf_filename)

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(msg)

@app.route('/send_report/<filename>', methods=['POST'])
@login_required
def send_report(filename):
    to_email = request.form.get('email')
    if not to_email:
        flash("❌ Missing recipient email.")
        return redirect(url_for('history'))

    report_path = os.path.join("static", "history", filename)
    if not os.path.exists(report_path):
        flash("❌ Report not found.")
        return redirect(url_for('history'))

    with open(report_path, 'r') as f:
        product = json.load(f)
    product['results'] = check_compliance(product)
    pdf = generate_pdf(product)

    try:
        send_report_email(to_email, product, pdf)
        flash("✅ Email sent successfully.")
        return redirect(url_for('history'))
    except Exception as e:
        flash(f"❌ Error sending email: {e}")
        return redirect(url_for('history'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == 'admin' and password == 'GreenCheck2025':
            session['logged_in'] = True
            return redirect(url_for('index'))
        else:
            flash('Invalid credentials. Try again.')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/', methods=['GET', 'POST'])
@login_required
def index():
    if request.method == 'POST':
        try:
            product = {
                'name': request.form.get('name'),
                'state': request.form.get('state'),
                'product_type': request.form.get('product_type'),
                'thc': float(request.form.get('thc', 0)),
                'thc_per_serving': float(request.form.get('thc_per_serving', 0)),
                'packaged_date': request.form.get('packaged_date'),
                'batch_id': request.form.get('batch_id'),
                'cbd': float(request.form.get('cbd', 0)),
                'cbn': float(request.form.get('cbn', 0)),
                'weight_grams': float(request.form.get('weight_grams', 0)),
                'warning_label': 'warning_label' in request.form
            }

            product['results'] = check_compliance(product)

            # ✅ Save to /static/history with date_created
            history_dir = os.path.join("static", "history")
            os.makedirs(history_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            filename = f"{product['name'].replace(' ', '_')}_{timestamp}.json"
            filepath = os.path.join(history_dir, filename)

            product['date_created'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            with open(filepath, "w") as f:
                json.dump(product, f, indent=2)

            return redirect(url_for('view_report', filename=filename))

        except Exception as e:
            return render_template('index.html', result=[f"❌ Error: {str(e)}"])

    return render_template('index.html')

@app.route('/download', methods=['POST'])
@login_required
def download():
    product = {
        'name': request.form.get('name'),
        'state': request.form.get('state'),
        'product_type': request.form.get('product_type'),
        'thc': float(request.form.get('thc', 0)),
        'thc_per_serving': float(request.form.get('thc_per_serving', 0)),
        'packaged_date': request.form.get('packaged_date'),
        'batch_id': request.form.get('batch_id'),
        'cbd': float(request.form.get('cbd', 0)),
        'cbn': float(request.form.get('cbn', 0)),
        'weight_grams': float(request.form.get('weight_grams', 0)),
        'warning_label': 'warning_label' in request.form
    }

    results = check_compliance(product)
    product['results'] = results

    # Save JSON file
    history_dir = os.path.join("static", "history")
    os.makedirs(history_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"{product['name'].replace(' ', '_')}_{timestamp}.json"
    filepath = os.path.join(history_dir, filename)
    with open(filepath, "w") as f:
        json.dump(product, f, indent=2)

    # Generate and return PDF
    buffer = generate_pdf(product)
    response = make_response(buffer.read())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename={product["name"].replace(" ", "_")}_GreenCheck_Report.pdf'
    return response

@app.route('/history')
@login_required
def history():
    history_dir = os.path.join("static", "history")
    report_files = [f for f in os.listdir(history_dir) if f.endswith(".json")]
    report_data = []

    for filename in sorted(report_files, reverse=True):
        path = os.path.join(history_dir, filename)
        with open(path, "r") as f:
            data = json.load(f)
            report_data.append({
                "filename": filename,
                "name": data.get("name", "Unknown"),
                "state": data.get("state", "N/A"),
                "type": data.get("product_type", "N/A"),
                "packaged_date": data.get("packaged_date", "Unknown"),
                "date_created": data.get("date_created", "Unknown"),
                "results": data.get("results", [])
            })

    return render_template("history.html", reports=report_data)

@app.route('/delete/<filename>', methods=['POST'])
@login_required
def delete_report(filename):
    password = request.form.get('password')
    if password != "GreenCheck2025":
        return "Unauthorized. Incorrect password.", 403

    try:
        file_path = os.path.join("static", "history", filename)
        if os.path.exists(file_path):
            os.remove(file_path)
        return redirect('/history')
    except Exception as e:
        return f"Error deleting file: {e}", 500
@app.route('/view_report/<filename>')
@login_required
def view_report(filename):
    try:
        path = os.path.join("static", "history", filename)
        with open(path, "r") as f:
            report = json.load(f)
        report['filename'] = filename  # ✅ Add this line
        return render_template("view_report.html", report=report)
    except Exception as e:
        return f"Error loading report: {str(e)}", 500

@app.route('/preview_report/<filename>')
@login_required
def preview_report(filename):
    path = os.path.join("static", "history", filename)
    if not os.path.exists(path):
        return "Report not found.", 404

    with open(path, "r") as f:
        product = json.load(f)
        product['results'] = check_compliance(product)

    buffer = generate_pdf(product)
    return Response(
        buffer.read(),
        mimetype='application/pdf',
        headers={
            "Content-Disposition": "inline; filename=preview.pdf"
        }
    )

@app.route('/download_report/<filename>')
@login_required
def download_report(filename):
    path = os.path.join("static", "history", filename)
    if not os.path.exists(path):
        return "Report not found.", 404

    with open(path, "r") as f:
        product = json.load(f)
        product['results'] = check_compliance(product)

    buffer = generate_pdf(product)
    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"{product['name'].replace(' ', '_')}_GreenCheck_Report.pdf",
        mimetype='application/pdf'
    )

if __name__ == '__main__':
    app.run(debug=True)