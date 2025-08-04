from flask import Flask, render_template, request, redirect, url_for, flash,session
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
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # You can add login logic here
        return "Login successful!"  # Placeholder
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

@app.route("/dashboard", methods=['GET','POST'])
def dashboard():
     if request.method == 'POST':
         doctor=request.form['doctor']
         clinic=request.form['clinic']
         date=request.form['date']
         time=request.form['time']
         sql="INSERT INTO Appointment (ADate,ATime,Doctor,Clinic) VALUES (%s,%s,%s,%s)"
         values=(date,time,doctor,clinic)
         cursor.execute(sql,values)
         conn.commit()

         return f"Appointment booked!"
     return render_template('dashboard.html')


if __name__ == '__main__':
    app.run(debug=True)

print("Host:", os.getenv("DB_HOST"))
print("User:", os.getenv("DB_USER"))
print("Password:", os.getenv("DB_PASSWORD"))
