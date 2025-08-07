from flask import Flask, render_template, request, redirect, url_for, flash,session
from dotenv import load_dotenv
from datetime import date
import os
import mysql.connector
import smtplib
import secrets
from email.message import EmailMessage

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
    selected_clinic = None
    selected_doctor = None
    selected_date = today
    clinics = []
    doctors = []
    booked_slots = []

    # Get list of all available clinics
    cursor.execute("SELECT DISTINCT Clinic FROM Doctors")
    clinics = [row[0] for row in cursor.fetchall()]

    if request.method == 'POST':
        selected_clinic = request.form.get('clinic')
        selected_doctor = request.form.get('doctor')
        selected_date = request.form.get('date')
        time = request.form.get('time')

        # Get list of doctors for selected clinic
        if selected_clinic:
            cursor.execute("SELECT Doctor FROM Doctors WHERE Clinic = %s", (selected_clinic,))
            doctors = [row[0] for row in cursor.fetchall()]

        # Only insert if all fields are filled
        if selected_clinic and selected_doctor and selected_date and time:
            # Check if the slot already exists in DB
            cursor.execute("""
                SELECT 1 FROM Appointment 
                WHERE ADate = %s AND ATime = %s AND Clinic = %s AND Doctor = %s
            """, (selected_date, time, selected_clinic, selected_doctor))

            if cursor.fetchone():
                flash("Appointment already booked", "error")
            else:
                cursor.execute("""
                    INSERT INTO Appointment (ADate, ATime, Doctor, Clinic)
                    VALUES (%s, %s, %s, %s)
                """, (selected_date, time, selected_doctor, selected_clinic))
                conn.commit()
                flash("Appointment booked successfully!", "success")

    # Always refresh booked slots to show red immediately
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

@app.route('/prescriptions')
def prescriptions():
    if 'username' not in session:
        flash("Please log in to view prescriptions.", "error")
        return redirect(url_for('login'))

    username = session['username']
    cursor.execute("SELECT filename FROM Prescriptions WHERE username = %s", (username,))
    prescriptions = cursor.fetchall()

    return render_template('prescriptions.html', prescriptions=prescriptions)

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

        flash('If the email exists, a reset link has been sent.', 'info')
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
        return "Password updated successfully!"

    return render_template('reset_password.html')

# users_db = {
#     "user@example.com": {
#         "password": "hashedpassword123",
#         "reset_token": None
#     }
# }


# @app.route('/forgot-password', methods=['GET', 'POST'])
# def forgot_password():
#     if request.method == 'POST':
#         email = request.form['email']
#         user = users_db.get(email)

#         if user:
#             # Generate token and "save" it
#             token = secrets.token_urlsafe(16)
#             user['reset_token'] = token

#             # Build reset URL
#             reset_url = url_for('reset_password', token=token, _external=True)

#             # Send email
#             send_reset_email(email, reset_url)

#         # Show message whether or not email exists (to prevent info leak)
#         flash('If the email exists, a reset link has been sent.', 'info')
#         return redirect(url_for('login'))  # Redirect to login


# def send_reset_email(to_email, reset_link):
#     sender_email = "clinikart.ss@gmail.com"
#     sender_password = "scrypt:32768:8:1$DAZn6QfcTQcwBk53$87071f1ea1580f937d71402a55cdd61b705ae2aa11e47ae971a868ad81fd217167643566df8cce553213aa6bd4b382ef22c396db13fb11bcf7a737034ab7ea57"

#     subject = "Password Reset Link"
#     body = f"Click the link to reset your password: {reset_link}"
#     email_text = f"Subject: {subject}\n\n{body}"

#     try:
#         with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
#             server.login(sender_email, sender_password)
#             server.sendmail(sender_email, to_email, email_text)
#     except Exception as e:
#         print("Email sending failed:", e)

# @app.route('/reset-password/<token>', methods=['GET', 'POST'])
# def reset_password(token):
#     # Find user with this token
#     email = None
#     for u_email, u_data in users_db.items():
#         if u_data['reset_token'] == token:
#             email = u_email
#             break

#     if not email:
#         return "Invalid or expired token.", 400

#     if request.method == 'POST':
#         new_password = request.form['new_password']
#         # Save new password (you should hash it in real apps)
#         users_db[email]['password'] = new_password
#         users_db[email]['reset_token'] = None
#         return "Password updated successfully!"

#     return render_template('reset_password.html')

if __name__ == '__main__':
    app.run(debug=True)

print("Host:", os.getenv("DB_HOST"))
print("User:", os.getenv("DB_USER"))
print("Password:", os.getenv("DB_PASSWORD"))