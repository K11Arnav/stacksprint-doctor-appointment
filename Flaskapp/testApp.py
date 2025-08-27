from flask import Flask, render_template, request, redirect
from datetime import datetime, timedelta
from dotenv import load_dotenv
import mysql.connector
import os

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

if __name__ == '__main__':
    app.run(debug=True)
