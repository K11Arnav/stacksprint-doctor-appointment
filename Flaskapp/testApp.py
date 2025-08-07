from flask import Flask, render_template, request, redirect, url_for, flash,session
from dotenv import load_dotenv
from datetime import date
import os
import mysql.connector

load_dotenv()

conn = mysql.connector.connect(
    host=os.getenv("DB_HOST"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    database=os.getenv("DB_NAME")
)
cursor=conn.cursor()

app=Flask(__name__)
app.secret_key = 'your_secret_key'
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME")
        )
        cursor = conn.cursor()
        query = "SELECT * FROM test_info_users WHERE username=%s AND password=%s"
        cursor.execute(query, (username, password))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        if user:
            session['username'] = user[0]  
            flash("User login successful!")
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid username or password")
    return render_template('login.html')
    

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        username=request.form['username']
        emailID=request.form['email_id']
        mobileNum=request.form['mobile_number']
        password=request.form['password']

        sql="INSERT INTO test_info_users (username,email_id,mobile_number,password) VALUES (%s,%s,%s,%s)"
        values=(username,emailID,mobileNum,password)
        cursor.execute(sql,values)
        conn.commit()

        return redirect(url_for('login', msg="User registered successfully"))
    return render_template('register.html')

@app.route('/appointment', methods=['GET', 'POST'])
def appointment():
    today = date.today().isoformat()

    if request.method == 'POST':
        doctor = request.form['doctor']
        clinic = request.form['clinic']
        adate = request.form['date']
        time = request.form['time']

        sql = "INSERT INTO Appointment (ADate, ATime, Doctor, Clinic) VALUES (%s, %s, %s, %s)"
        values = (adate, time, doctor, clinic)
        cursor.execute(sql, values)
        conn.commit()
        flash("Appointment booked!")

    # --- booked slots for today ---
    cursor.execute("SELECT ATime FROM Appointment WHERE ADate = %s", (today,))
    result = cursor.fetchall()
    # mysql.connector returns tuples by default; adapt if you use dict cursor
    booked_slots = [row[0] for row in result]

    # --- fetch doctors with ratings ---
    cursor.execute("SELECT DName, rating, review_count FROM doctor")
    doctors = cursor.fetchall()   # list of tuples like [(DName, rating, review_count), ...]
    # If your cursor returns dicts, adapt indexes to keys.

    # Build doctor dropdown HTML (no Jinja loop needed)
    doctor_options_html = '<option value="">-- Select Doctor --</option>'
    for d in doctors:
        name = d[0]
        rating = d[1] or 0
        rc = d[2] or 0
        doctor_options_html += f'<option value="{name}">{name} - {rating:.1f}★ ({rc} reviews)</option>'

    # --- fetch upcoming appointments (example shows all patients; if you filter by session add WHERE patient_id=...) ---
    cursor.execute("""
        SELECT ADate, ATime, Doctor, Clinic, status
        FROM Appointment
        WHERE ADate >= %s
        ORDER BY ADate, ATime
    """, (today,))
    appts = cursor.fetchall()   # list of tuples

    # Build a quick lookup dict for doctor ratings to show alongside appointments
    doctor_rating_map = { d[0]: (d[1] or 0, d[2] or 0) for d in doctors }

    # Build HTML rows for the appointments table (so template doesn't have to loop)
    appointments_rows_html = ""
    for a in appts:
        # adapt indices if your cursor returns dicts: a['ADate'] etc.
        a_date = a[0]
        a_time = a[1]
        a_doc = a[2]
        a_clinic = a[3]
        a_status = a[4]
        rating, rc = doctor_rating_map.get(a_doc, (None, 0))
        if rating is None or rating == 0:
            rating_html = '<span class="small">No rating</span>'
        else:
            rating_html = f'<strong style="color:#e74c3c">{rating:.1f}</strong> ★ <span class="small">({rc})</span>'

        appointments_rows_html += (
            "<tr>"
            f"<td>{a_date}</td>"
            f"<td>{a_time}</td>"
            f"<td>{a_doc}</td>"
            f"<td>{a_clinic}</td>"
            f"<td>{rating_html}</td>"
            f"<td>{a_status}</td>"
            "</tr>"
        )

    return render_template(
        'appointment.html',
        current_date=today,
        booked_slots=booked_slots,
        doctor_options=doctor_options_html,
        appointments_rows=appointments_rows_html
    )

@app.route('/dashboard')
def dashboard():
    appointments = [
        {"date": "2025-08-05", "time": "10:00", "doctor": "Dr. Rao", "clinic": "Clinic A", "status": "Confirmed"},
        {"date": "2025-08-07", "time": "14:30", "doctor": "Dr. Shah", "clinic": "Clinic B", "status": "Pending"},
    ]
    return render_template("dashboard.html", appointments=appointments)


if __name__ == '__main__':
    app.run(debug=True)

print("Host:", os.getenv("DB_HOST"))
print("User:", os.getenv("DB_USER"))
print("Password:", os.getenv("DB_PASSWORD"))
