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
        firstName=request.form['first_name']
        lastName=request.form['last_name']
        emailID=request.form['email_id']
        mobileNum=request.form['mobile_number']
        password=request.form['password']

        sql="INSERT INTO user_info (first_name,last_name,email_id,mobile_number,password) VALUES (%s,%s,%s,%s,%s)"
        values=(firstName,lastName,emailID,mobileNum,password)
        cursor.execute(sql,values)
        conn.commit()

        return f"User {firstName} registered successfully!"
    return render_template('register.html')

if __name__ == '__main__':
    app.run(debug=True)

print("Host:", os.getenv("DB_HOST"))
print("User:", os.getenv("DB_USER"))
print("Password:", os.getenv("DB_PASSWORD"))
