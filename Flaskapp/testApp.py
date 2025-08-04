from flask import Flask, render_template, request, redirect, url_for, session
from dotenv import load_dotenv
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

        return f"User {username} registered successfully!"
    return render_template('register.html')


@app.route("/appointments")
def dashboard():
    appointments = [
        {"date": "2025-08-05", "time": "10:00", "doctor": "Dr. Rao", "clinic": "Clinic A", "status": "Confirmed"},
        {"date": "2025-08-07", "time": "14:30", "doctor": "Dr. Shah", "clinic": "Clinic B", "status": "Pending"},
    ]
    return render_template("appointments.html", appointments=appointments)


if __name__ == '__main__':
    app.run(debug=True)

print("Host:", os.getenv("DB_HOST"))
print("User:", os.getenv("DB_USER"))
print("Password:", os.getenv("DB_PASSWORD"))
