from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
from reportlab.lib.colors import HexColor 
import mysql.connector
from mysql.connector import Error
import re
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from fpdf import FPDF
import io
import os
import csv
from flask import Flask, request, Response, jsonify
import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key' 


def db_connection():
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='Beula@123',
        database='employee_data'
    )


@app.route('/')
def welcome():
    return render_template('welcome.html')


@app.route('/login_page', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            flash("All fields are required.", "error")
            return redirect(url_for('login_page'))

        try:
            conn = db_connection()
            cursor = conn.cursor()
            query = "SELECT * FROM users WHERE username=%s AND password=%s"
            cursor.execute(query, (username, password))
            result = cursor.fetchone()

            if result:
                return render_template('login.html', success=True)  
            else:
                flash("Wrong Credentials", "error")
                return redirect(url_for('login_page')) 
        except Error as e:
            flash(f"Error connecting to database: {e}", "error")
            return redirect(url_for('login_page'))
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()

    return render_template('login.html')


@app.route('/portal_page')
def portal_page():
    return render_template('portal.html')


@app.route('/ems_page')
def ems_page():
    try:
        conn = db_connection()
        cursor = conn.cursor()
        query = "SELECT Employee_Id, Employee_Name, Designation, Contact_No, Date_Of_Joining, Month_Name, CTC, Adhar_No FROM data ORDER BY CAST(SUBSTR(Employee_Id, 4) AS UNSIGNED)"
        cursor.execute(query)
        employees = cursor.fetchall()
        return render_template('ems.html', employees=employees)
    except Error as e:
        flash(f"Error fetching employees: {e}", "error")
        return redirect(url_for('portal_page'))
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()




from datetime import datetime

@app.route('/add_employee', methods=['POST'])
def add_employee():
    if request.method == 'POST':
        form = request.form

        # Validate date format (YYYY-MM-DD)
        try:
            datetime.strptime(form['doj'], '%Y-%m-%d')  # This will raise an error if the format is incorrect
        except ValueError:
            return jsonify({"success": False, "message": "Date_Of_Joining must be in YYYY-MM-DD format."}), 400

        try:
            conn = db_connection()
            if conn is None:
                return jsonify({"success": False, "message": "Database connection error"})

            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO data (Employee_Id, Employee_Name, Designation, Contact_No, Date_Of_Joining, Month_Name, CTC, Adhar_No)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ''', (form['employee_id'], form['employee_name'], form['designation'], form['contact_no'], form['doj'], form['month_name'], form['ctc'], form['adhar_no']))
            conn.commit()

            return jsonify({"success": True, "message": "Employee added successfully"})
        except Error as e:
            return jsonify({"success": False, "message": f"Error adding employee: {e}"})
        finally:
            if conn and conn.is_connected():
                cursor.close()
                conn.close()

    return jsonify({"success": False, "message": "Invalid request method"})

@app.route('/delete_employee', methods=['POST'])
def delete_employee():
    try:
        conn = db_connection()
        cursor = conn.cursor()

        # Use request.json to get the JSON data
        data = request.json
        employee_ids = data.get('ids', [])

        if not employee_ids:
            return jsonify({"success": False, "message": "No employee selected."})

        format_strings = ','.join(['%s'] * len(employee_ids))
        query = f'DELETE FROM data WHERE Employee_Id IN ({format_strings})'
        cursor.execute(query, tuple(employee_ids))
        conn.commit()

        return jsonify({"success": True, "message": "Employees deleted successfully."})
    except Error as e:
        return jsonify({"success": False, "message": f"Error deleting employees: {e}"})
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


from datetime import datetime
@app.route('/search_employees', methods=['GET'])
def search_employees():
    search_key = request.args.get('key')
    search_value = request.args.get('value')
    is_exact = request.args.get('exact', 'false').lower() == 'true'

    valid_columns = ['Employee_Id', 'Employee_Name', 'Designation', 'Contact_No', 'Date_Of_Joining', 'Month_Name', 'CTC', 'Adhar_No']

    # Validate search key
    if search_key not in valid_columns:
        return jsonify({"error": "Invalid search key."}), 400

    try:
        conn = db_connection()
        cursor = conn.cursor()

        # Use '=' for exact match or 'LIKE' for partial match based on is_exact flag
        if is_exact and search_key == 'Employee_Id':
            query = f"SELECT * FROM data WHERE {search_key} = %s"
        else:
            query = f"SELECT * FROM data WHERE {search_key} LIKE %s"

        cursor.execute(query, ('%' + search_value + '%' if not is_exact else search_value,))
        employees = cursor.fetchall()
    except Error as e:
        return jsonify({"error": f"Error searching employees: {e}"})
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

    if not employees:
        return jsonify({"error": "No employees found."})

    employee_list = [
        {
            "Employee_Id": row[0],
            "Employee_Name": row[1],
            "Designation": row[2],
            "Contact_No": row[3],
            "Date_Of_Joining": row[4].strftime("%Y-%m-%d") if isinstance(row[4], datetime) else row[4],
            "Month_Name": row[5],
            "CTC": row[6],
            "Adhar_No": row[7]
        } for row in employees
    ]
    return jsonify(employee_list)



def fetch_employees():
    try:
        conn = db_connection()
        cursor = conn.cursor()
        query = "SELECT Employee_Id, Employee_Name, Designation, Contact_No, Date_Of_Joining, Month_Name, CTC, Adhar_No FROM data ORDER BY CAST(SUBSTR(Employee_Id, 4) AS UNSIGNED)"
        cursor.execute(query)
        result = cursor.fetchall()
        return render_template('ems.html', employees=result)
    except Error as e:
        flash(f"Error fetching employees: {e}", "error")
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()
    return redirect(url_for('ems_page'))



@app.route('/update_employee', methods=['POST'])
def update_employee():
    conn = db_connection()
    cursor = conn.cursor()

    try:
        data = request.json
        print("Received data for update:", data)

        # Get employee details from the request
        employee_id = data.get('Employee_Id')  # Use the exact key used in your JS
        employee_name = data.get('Employee_Name')
        designation = data.get('Designation')
        contact_no = data.get('Contact_No')
        date_of_joining = data.get('Date_Of_Joining')
        month_name = data.get('Month_Name')
        ctc = data.get('CTC')
        adhar_no = data.get('Adhar_No')

        # Validate inputs
        if not all([employee_id, employee_name, designation, contact_no, date_of_joining, month_name, ctc, adhar_no]):
            print("Validation failed: All fields are required.")
            return jsonify({"success": False, "message": "All fields are required."}), 400

        print("Validation passed, updating employee...")

        # Update query
        update_query = '''UPDATE data
                          SET Employee_Name = %s, Designation = %s, Contact_No = %s,
                              Date_Of_Joining = %s, Month_Name = %s, CTC = %s, Adhar_No = %s
                          WHERE Employee_Id = %s'''

        cursor.execute(update_query, (
            employee_name,
            designation,
            contact_no,
            date_of_joining,
            month_name,
            ctc,
            adhar_no,
            employee_id
        ))

        conn.commit()

        print(f"Rows updated: {cursor.rowcount}")
        if cursor.rowcount == 0:
            print(f"No rows updated for Employee ID: {employee_id}. It might not exist.")
            return jsonify({"success": False, "message": "Employee not found or no changes made."}), 404

        return jsonify({"success": True, "message": "Employee updated successfully."}), 200

    except Exception as e:
        print(f"Error updating employee: {str(e)}")
        return jsonify({"success": False, "message": f"Error updating employee: {str(e)}"}), 500

    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None and conn.is_connected():
            conn.close()



@app.route('/show_all_employees', methods=['GET'])
def show_all_employees():
    try:
        conn = db_connection()  # Use your existing `db_connection` function
        cursor = conn.cursor(dictionary=True)  # Fetch as dictionary
        query = "SELECT Employee_Id, Employee_Name, Designation, Contact_No, Date_Of_Joining, Month_Name, CTC, Adhar_No FROM data"
        cursor.execute(query)
        employees = cursor.fetchall()
        return jsonify(employees)
    except Error as e:
        return jsonify({'error': str(e)})
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()  # Ensure this runs


@app.route('/download_report')
def download_report():
    selected_ids = request.args.get('ids', '').strip()

    if not selected_ids:
        return jsonify({"error": "No employee IDs selected"}), 400

    try:
        conn = db_connection()
        cursor = conn.cursor()
        employee_ids = selected_ids.split(',')

        reports = []
        for emp_id in employee_ids:
            query = """
                SELECT Employee_Id, Employee_Name, Designation, Contact_No,
                       Date_Of_Joining, Month_Name, CTC, Adhar_No
                FROM data
                WHERE Employee_Id = %s
            """
            cursor.execute(query, (emp_id,))
            employee = cursor.fetchone()

            if employee:
                reports.append(employee)
            else:
                return jsonify({"error": f"No employee found for ID {emp_id}"}), 404

    except Exception as e:
        return jsonify({"error": f"Error fetching employees: {e}"}), 500
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

   
    file_format = request.args.get('format', 'csv').lower()

    
    file_name = f"{reports[0][1]}_report" if len(reports) == 1 else "employees_report"

   
    company_name = "Coolgen Solution Pvt. Ltd"
    company_address = "S L Nivas, 1st floor Marthandam, Tamil Nadu, IN"
    gmail = "hello@coolgentech.com"
    logo_path = 'D:/Beula-Python/Employee_Portal/Images/CoolgenLogo.png'
    disclaimer = "This document is digital and doesn't require a signature. Contact hello@coolgentech.com for inquiries."

    if file_format == 'csv':
       
        output = io.StringIO()
        csv_writer = csv.writer(output)
        
       
        csv_writer.writerow([company_name])
        csv_writer.writerow([company_address])
        csv_writer.writerow([f"Contact: {gmail}"])
        csv_writer.writerow([])  
        
     
        csv_writer.writerow(["Employee Id", "Employee Name", "Designation", "Contact No",
                             "Date Of Joining", "Month Name", "CTC", "Adhar No"])
        
       
        for employee in reports:
            csv_writer.writerow(employee)
        
        
        csv_writer.writerow([])
        csv_writer.writerow([disclaimer])
        
        output.seek(0)
        
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            as_attachment=True,
            download_name=f"{file_name}.csv",
            mimetype='text/csv'
        )

    elif file_format == 'pdf':
    
     pdf_buffer = io.BytesIO()
    pdf = canvas.Canvas(pdf_buffer, pagesize=letter)
    pdf.setFont("Helvetica", 10)  

   
    logo_x, logo_y = 30, 680
    logo_width, logo_height = 2 * inch, 1 * inch
    pdf.drawImage(logo_path, logo_x, logo_y, width=logo_width, height=logo_height)

    
    company_details_y = logo_y - logo_height - 1
    pdf.drawString(logo_x, company_details_y, company_name)
    pdf.drawString(logo_x, company_details_y - 14, company_address)  
    pdf.drawString(logo_x, company_details_y - 30, f"Contact: {gmail}")

    
    line_y = company_details_y - 40  
    pdf.line(30, line_y, 570, line_y)  

   
    pdf.setFont("Helvetica-Bold", 14)  
    pdf.setFillColor(HexColor('#FF5733'))  
    title_y = line_y - 20  
    pdf.drawCentredString(300, title_y, "Employee Report")

    
    pdf.setFillColor(HexColor('#000000'))  

    
    employee_start_y = title_y - 40  

 
    for employee in reports:
       
        fields = ["Employee Id", "Employee Name", "Designation", "Contact No", 
                  "Date Of Joining", "Month Name", "CTC", "Adhar No"]

       
        for i, field in enumerate(fields):
          
            pdf.setFillColor(HexColor('#4B4B4B')) 
            pdf.setFont("Helvetica-Bold", 10) 
            pdf.drawString(30, employee_start_y, field)  

           
            pdf.setFillColor(HexColor('#4B4B4B'))  
            pdf.setFont("Helvetica", 10)  
            pdf.drawString(200, employee_start_y, str(employee[i]))  
            
            employee_start_y -= 20  

       
        employee_start_y -= 10  
        pdf.line(30, employee_start_y, 570, employee_start_y)
        employee_start_y -= 10  

        
        if employee_start_y < 150:  
            pdf.showPage()
            pdf.setFont("Helvetica", 10)  
            employee_start_y = 750  

    
    pdf.setFont("Helvetica", 8) 
    pdf.setFillColor(HexColor('#000000'))  
    pdf.drawString(100, 100, disclaimer)

    
    pdf.save()
    pdf_buffer.seek(0)

    return send_file(
        pdf_buffer,
        as_attachment=True,
        download_name=f"{file_name}.pdf",
        mimetype='application/pdf'
    )



@app.route('/get_employee_details', methods=['GET'])
def get_employee_details():
    employee_id = request.args.get('employee_id')
    if not employee_id:
        return jsonify({'error': 'Employee ID is required'}), 400

    print(f"Requested Employee ID: {employee_id}") 

    try:
        conn = db_connection()
        cursor = conn.cursor(dictionary=True)
        query = "SELECT Employee_Id, Employee_Name, Designation, Contact_No, DATE_FORMAT(Date_Of_Joining, '%Y-%m-%d') as Date_Of_Joining, Month_Name, CTC, Adhar_No FROM data WHERE Employee_Id = %s"
        cursor.execute(query, (employee_id,))
        employee = cursor.fetchone()

        if employee:
            print(f"Fetched Employee Data: {employee}")  
            return jsonify(employee)
        else:
            return jsonify({'error': 'Employee not found'}), 404

    except Error as e:
        print(f"Database error: {str(e)}") 
        return jsonify({'error': str(e)}), 500

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

@app.route('/delete_all_employees', methods=['POST'])
def delete_all_employees():
    try:
        conn = db_connection()
        cursor = conn.cursor()

       
        cursor.execute("DELETE FROM data")
        conn.commit()

        return jsonify({"success": True, "message": "All employees deleted successfully."})
    except Error as e:
        return jsonify({"success": False, "message": f"Error deleting all employees: {e}"})
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)



