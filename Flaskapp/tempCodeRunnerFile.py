from flask import Flask, render_template, request, redirect, url_for, flash,session
from dotenv import load_dotenv
from datetime import date
import os
import mysql.connector
import smtplib
import secrets
import os

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

@app.route('/appointment', methods=['GET','POST'])
def appointment():
     today = date.today().isoformat()
     selected_clinic = None
     selected_doctor = None
     selected_date = None
     clinics = []
     doctors = []
     booked_slots = []
     cursor.execute("SELECT DISTINCT Clinic FROM Doctors")
     clinics = [row[0] for row in cursor.fetchall()]
     if request.method == 'POST':
        selected_date = request.form['date']
        selected_clinic = request.form['clinic']
        time = request.form['time']
        selected_doctor = request.form['doctor']
        if selected_clinic and selected_doctor:
            cursor.execute("SELECT Doctor FROM Doctors WHERE clinic = %s", (selected_clinic,))
            doctors = [row[0] for row in cursor.fetchall()]
            cursor.execute("SELECT ATime FROM Appointment WHERE ADate = %s AND Clinic = %s", (selected_date, selected_clinic))
            booked_slots = [row[0] for row in cursor.fetchall()]
            return render_template('appointment.html', current_date=today, clinics=clinics, selected_clinic=selected_clinic, doctors=doctors, selected_date=selected_date, booked_slots=booked_slots)
        if selected_clinic and selected_doctor and time:
            sql="INSERT INTO Appointment (ADate,ATime,Doctor,Clinic) VALUES (%s,%s,%s,%s)"
            values=(selected_date,time,selected_doctor, selected_clinic)
            cursor.execute(sql,values)
            conn.commit()
            flash("Appointment booked!")
     cursor.execute("SELECT ATime FROM Appointment WHERE ADate = %s", (today,))
     if selected_date and selected_clinic and selected_doctor:
        cursor.execute("SELECT ATime FROM Appointment WHERE ADate = %s AND Clinic = %s AND Doctor = %s",(selected_date, selected_clinic, selected_doctor))
        booked_slots = [row[0] for row in cursor.fetchall()]
     return render_template('appointment.html', current_date=today, booked_slots=booked_slots, clinics=clinics, selected_clinic=selected_clinic, doctors=doctors,  selected_date=selected_date)

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query')
    print(f"Search query: {query}")  # Check if this prints in terminal

    conn = mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )
    cursor = conn.cursor()
    sql = "SELECT * FROM doc_info WHERE DName LIKE %s OR DClinic LIKE %s"
    val = ('%' + query + '%', '%' + query + '%')
    cursor.execute(sql, val)
    results = cursor.fetchall()

    print(f"Results: {results}") 

    return render_template('search_results.html', query=query, results=results)

users_db = {
    "user@example.com": {
        "password": "hashedpassword123",
        "reset_token": None
    }
}

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        user = users_db.get(email)

        if user:
            # Generate token and "save" it
            token = secrets.token_urlsafe(16)
            user['reset_token'] = token

            # Build reset URL
            reset_url = url_for('reset_password', token=token, _external=True)

            # Send email
            send_reset_email(email, reset_url)

        # Show message whether or not email exists (to prevent info leak)
        flash('If the email exists, a reset link has been sent.', 'info')
        return redirect(url_for('login'))  # Redirect to login


def send_reset_email(to_email, reset_link):
    sender_email = "youremail@example.com"
    sender_password = "your-email-password"

    subject = "Password Reset Link"
    body = f"Click the link to reset your password: {reset_link}"
    email_text = f"Subject: {subject}\n\n{body}"

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, to_email, email_text)
    except Exception as e:
        print("Email sending failed:", e)

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    # Find user with this token
    email = None
    for u_email, u_data in users_db.items():
        if u_data['reset_token'] == token:
            email = u_email
            break

    if not email:
        return "Invalid or expired token.", 400

    if request.method == 'POST':
        new_password = request.form['new_password']
        # Save new password (you should hash it in real apps)
        users_db[email]['password'] = new_password
        users_db[email]['reset_token'] = None
        return "Password updated successfully!"

    return render_template('reset_password.html')


if __name__ == '__main__':
    app.run(debug=True)

print("Host:", os.getenv("DB_HOST"))
print("User:", os.getenv("DB_USER"))
print("Password:", os.getenv("DB_PASSWORD"))
