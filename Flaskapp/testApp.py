from flask import Flask, render_template, request, redirect
from datetime import datetime, timedelta
from dotenv import load_dotenv
import mysql.connector
import os
import smtplib
import secrets
from email.message import EmailMessage
from datetime import datetime
import calendar
from collections import defaultdict


# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Use environment variables for DB config
conn = mysql.connector.connect(
    host=os.getenv("DB_HOST"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    database=os.getenv("DB_NAME")     
)
cursor = conn.cursor(dictionary=True)

@app.route('/', methods=['GET', 'POST'])
def calendar():
    if request.method == 'POST':
        clinic_id = request.form['clinic']
    else:
        clinic_id = 1  # default clinic
app=Flask(__name__)
app.secret_key = 'your_secret_key'
UPLOAD_DIR = r"C:\Users\vajra\Repositories\stacksprint-doctor-appointment\Flaskapp\static\prescriptions"
os.makedirs(UPLOAD_DIR, exist_ok=True)
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    return render_template('login.html')

@app.route('/patient_login', methods=['GET', 'POST'])
def patient_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        query = "SELECT * FROM test_info_users WHERE username=%s AND password=%s"
        cursor.execute(query, (username, password))
        user = cursor.fetchone()

        if user:
            session['username'] = user[0]
            print("Session after login:", session) 
            return redirect(url_for('dashboard'))

    return render_template('patient_login.html')

@app.route('/doctor_login', methods=['GET', 'POST'])
def doctor_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cursor.execute("SELECT * FROM Doctors WHERE username=%s AND password=%s", (username, password))
        doctor = cursor.fetchone()

        if doctor:
            session['doctor_logged_in'] = True
            session['doctor_username'] = username
            return redirect(url_for('doctor_dashboard'))
        else:
            return redirect(url_for('doctor_login', msg="Invalid Password or Username"))

    return render_template('doctor_login.html')


    today = datetime.today()
    start_date = today.replace(day=1)
    end_date = (start_date + timedelta(days=32)).replace(day=1) - timedelta(days=1)

    cursor.execute("SELECT * FROM clinics")
    clinics = cursor.fetchall()

    cursor.execute("""
        SELECT * FROM appointments 
        WHERE clinic_id = %s AND date BETWEEN %s AND %s
    """, (clinic_id, start_date.date(), end_date.date()))
    appointments = cursor.fetchall()

    calendar_data = {}
    for appt in appointments:
        date_str = appt['date'].strftime('%Y-%m-%d')
        if date_str not in calendar_data:
            calendar_data[date_str] = []
        calendar_data[date_str].append(appt)

    return render_template('calendar.html', clinics=clinics, calendar_data=calendar_data, current_clinic=clinic_id, start_date=start_date)

@app.route('/book', methods=['POST'])
def book():
    patient_name = request.form['patient_name']
    date = request.form['date']
    time = request.form['time']
    clinic_id = request.form['clinic_id']

    cursor.execute("""
        INSERT INTO appointments (clinic_id, patient_name, date, time)
        VALUES (%s, %s, %s, %s)
    """, (clinic_id, patient_name, date, time))
    conn.commit()
    return redirect('/')
@app.route('/appointment', methods=['GET', 'POST'])
def appointment():
    today = date.today().isoformat()
    selected_clinic = None
    selected_doctor = None
    selected_date = today
    clinics = []
    doctors = []
    booked_slots = []

    
    username = session.get('username')
    if not username:
        return redirect(url_for('login')) 
    cursor.execute("SELECT DISTINCT Clinic FROM Doctors")
    clinics = [row[0] for row in cursor.fetchall()]

    if request.method == 'POST':
        selected_clinic = request.form.get('clinic')
        selected_doctor = request.form.get('doctor')
        selected_date = request.form.get('date')
        time = request.form.get('time')
        if selected_clinic:
            cursor.execute("SELECT Doctor FROM Doctors WHERE Clinic = %s", (selected_clinic,))
            doctors = [row[0] for row in cursor.fetchall()]

        if selected_clinic and selected_doctor and selected_date and time:
            cursor.execute("SELECT username FROM Doctors WHERE Doctor = %s AND Clinic = %s", 
                           (selected_doctor, selected_clinic))
            doctor_user_row = cursor.fetchone()
            if doctor_user_row:
                doctor_username = doctor_user_row[0]
            else:
                doctor_username = None
                return render_template('appointment.html',
                                       current_date=today,
                                       clinics=clinics,
                                       doctors=doctors,
                                       selected_clinic=selected_clinic,
                                       selected_doctor=selected_doctor,
                                       selected_date=selected_date,
                                       booked_slots=booked_slots)
            cursor.execute("""
                SELECT 1 FROM Appointment 
                WHERE ADate = %s AND ATime = %s AND Clinic = %s AND Doctor = %s
            """, (selected_date, time, selected_clinic, selected_doctor))
            if cursor.fetchone():
                flash("Appointment already booked", "error")
            else:
                cursor.execute("""
                    INSERT INTO Appointment (ADate, ATime, Doctor, Clinic, username, duser)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (selected_date, time, selected_doctor, selected_clinic, username, doctor_username))
                conn.commit()
                flash("Appointment booked successfully!", "success")
    if selected_clinic and selected_doctor and selected_date:
        cursor.execute("""
            SELECT ATime FROM Appointment 
            WHERE ADate = %s AND Clinic = %s AND Doctor = %s
        """, (selected_date, selected_clinic, selected_doctor))
        booked_slots = [row[0] for row in cursor.fetchall()]

    return render_template('appointment.html',
                           current_date=today,
                           clinics=clinics,
                           doctors=doctors,
                           selected_clinic=selected_clinic,
                           selected_doctor=selected_doctor,
                           selected_date=selected_date,
                           booked_slots=booked_slots)


@app.route("/appointments_calendar")
def appointments_calendar():
    username = session.get("username")
    if not username:
        return redirect(url_for("login"))
    year = request.args.get("year", type=int) or datetime.now().year
    month = request.args.get("month", type=int) or datetime.now().month
    start_date = date(year, month, 1)
    last_day = calendar.monthrange(year, month)[1]
    end_date = date(year, month, last_day)

    cursor.execute("""
        SELECT ADate, ATime, Doctor, Clinic
        FROM Appointment
        WHERE username = %s AND ADate BETWEEN %s AND %s
        ORDER BY ADate, ATime
    """, (username, start_date, end_date))
    appointments = cursor.fetchall()
    appts_by_day = defaultdict(list)
    for appt_date, appt_time, doctor, clinic in appointments:
        if hasattr(appt_time, 'strftime'):
            time_str = appt_time.strftime("%H:%M")
        else:
            time_str = str(appt_time)

        appts_by_day[appt_date.day].append({
            "time": time_str,
            "doctor": doctor,
            "clinic": clinic,
        })
    cal = calendar.Calendar()
    month_days = list(cal.itermonthdays(year, month))  
    weeks = [month_days[i:i+7] for i in range(0, len(month_days), 7)]
    return render_template(
        "appointments_calendar.html",
        year=year,
        month=month,
        weeks=weeks,
        appts_by_day=appts_by_day,
        month_name=calendar.month_name[month]
    )

@app.route("/doctor_appointments_calendar")
def doctor_appointments_calendar():
    doctor_username = session.get("doctor_username")
    if not doctor_username:
        return redirect(url_for("doctor_login"))

    year = request.args.get("year", type=int) or datetime.now().year
    month = request.args.get("month", type=int) or datetime.now().month

    start_date = date(year, month, 1)
    last_day = calendar.monthrange(year, month)[1]
    end_date = date(year, month, last_day)

    cursor.execute("""
        SELECT ADate, ATime, username, Clinic
        FROM Appointment
        WHERE  duser = %s AND ADate BETWEEN %s AND %s
        ORDER BY ADate, ATime
    """, (doctor_username, start_date, end_date))

    appointments = cursor.fetchall()

    appts_by_day = defaultdict(list)

    for appt_date, appt_time, username, clinic in appointments:
        if isinstance(appt_date, str):
            appt_date = datetime.strptime(appt_date, "%Y-%m-%d").date()

        time_str = appt_time.strftime("%H:%M") if hasattr(appt_time, 'strftime') else str(appt_time)

        appts_by_day[appt_date.day].append({
            "time": time_str,
            "patient": username,
            "clinic": clinic
        })

    cal = calendar.Calendar(firstweekday=0)  
    month_days = list(cal.itermonthdays(year, month))
    weeks = [month_days[i:i+7] for i in range(0, len(month_days), 7)]

    return render_template(
        "doctor_appointments_calendar.html",
        year=year,
        month=month,
        weeks=weeks,
        appts_by_day=appts_by_day,
        month_name=calendar.month_name[month]
    )

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/doctor_dashboard')
def doctor_dashboard():
    return render_template('doctor_dashboard.html')


@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query')

    conn = mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )
    cursor = conn.cursor(dictionary=True)

    results = []
    cursor.execute("SELECT * FROM doc_info WHERE DName LIKE %s", (f"%{query}%",))
    results += cursor.fetchall()
    cursor.execute("SELECT * FROM doc_info WHERE Dspeciality LIKE %s", (f"%{query}%",))
    results += cursor.fetchall()
    cursor.execute("SELECT ClinicID, ClinicName FROM clinic_info WHERE ClinicName LIKE %s", (f"%{query}%",))
    clinics = cursor.fetchall()
    for clinic in clinics:
        clinic_id = clinic['ClinicID']
        cursor.execute("SELECT * FROM doc_info WHERE ClinicID = %s", (clinic_id,))
        clinic_doctors = cursor.fetchall()
        for doc in clinic_doctors:
            doc['ClinicName'] = clinic['ClinicName']
            results.append(doc)

    conn.close()

    return render_template("search_results.html", results=results)


@app.route('/doctor_profile/<int:doctor_id>')
def doctor_profile(doctor_id):
    conn = mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM doc_info WHERE DocID = %s", (doctor_id,))
    doctor = cursor.fetchone()
    conn.close()

    if doctor is None:
        return "Doctor not found", 404

    return render_template("doctor_profile.html", doctor=doctor)


@app.route('/prescriptions')
def prescriptions():
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session['username']
    cursor.execute("SELECT filename FROM Prescriptions WHERE username = %s", (username,))
    prescriptions = cursor.fetchall()
    prescription_urls = [
        url_for('static', filename=f'prescriptions/{row[0]}') for row in prescriptions
    ]

    return render_template('prescriptions.html', prescriptions=prescription_urls)


def send_reset_email(to_email, reset_link):
    sender_email = "clinikart.ss@gmail.com"
    sender_password = "pezsatwkkxlmidue"

    subject = "Password Reset Link"
    body = f"Click the link to reset your password:\n\n{reset_link}"
    email_text = f"Subject: {subject}\n\n{body}"

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, to_email, email_text)
    except Exception as e:
        print("Email sending failed:", e)

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        cursor.execute("SELECT * FROM test_info_users WHERE email_id = %s", (email,))
        user = cursor.fetchone()

        if user:
            token = secrets.token_urlsafe(16)
            cursor.execute("UPDATE test_info_users SET reset_token = %s WHERE email_id = %s", (token, email))
            conn.commit()

            reset_url = url_for('reset_password', token=token, _external=True)
            send_reset_email(email, reset_url)

        return redirect(url_for('login'))

    return render_template('forgot_password.html')

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    cursor.execute("SELECT * FROM test_info_users WHERE reset_token = %s", (token,))
    user = cursor.fetchone()

    if not user:
        return "Invalid or expired token.", 400

    if request.method == 'POST':
        new_password = request.form['new_password']
        cursor.execute("UPDATE test_info_users SET password = %s, reset_token = NULL WHERE reset_token = %s",
                       (new_password, token))
        conn.commit()
        return redirect(url_for("login"))

    return render_template('reset_password.html')

@app.route("/upload_prescription", methods=["GET", "POST"])
def upload_prescription():
    if not session.get("doctor_logged_in"):
        return redirect(url_for("doctor_login"))

    if request.method == "POST":
        patient_name = (request.form.get("patient_name") or "").strip()
        file = request.files.get("prescription")

        if not patient_name:
            return redirect(request.url)

        if not file or file.filename == "":
            return redirect(request.url)

        original_filename = os.path.basename(file.filename)
        final_path = os.path.join(UPLOAD_DIR, original_filename)

        try:
            file.save(final_path)

            cursor.execute(
                "INSERT INTO Prescriptions (doctorname, username, filename, uploadtime) VALUES (%s, %s, %s, %s)",
                (session.get("doctor_username"), patient_name, original_filename, datetime.now())
            )
            conn.commit()
            return redirect(url_for("doctor_dashboard"))

        except Exception as e:
            return redirect(request.url)

    return render_template("upload_prescription.html")

if __name__ == '__main__':
    app.run(debug=True)
