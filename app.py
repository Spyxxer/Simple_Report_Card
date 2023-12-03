from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_mysqldb import MySQL, MySQLdb
import sys
app = Flask(__name__)
app.config["MYSQL_HOST"] = ''
app.config["MYSQL_USER"] = ''
app.config["MYSQL_PASSWORD"] = ''
app.config["MYSQL_DB"] = ''
app.config['SECRET_KEY'] = 'reporthtpp'

mysql = MySQL(app)

# Sample data for students in different classes


def create_table(table_name, q):
    try:
        cursor = mysql.connection.cursor()
        query = f"""CREATE TABLE IF NOT EXISTS {table_name}({q});"""
        cursor.execute(query);
        cursor.close();
    except MySQLdb.ProgrammingError as e:
        print(e)

def insert_into_table(table_name, *cols):
    try:
        connection = mysql.connection
        cursor = connection.cursor()
        if len(cols) % 2 != 0:
          raise ValueError('Even number of arguments expected!')
        else:
            placeholders = ', '.join(['%s']* (len(cols)//2))
            query = f"INSERT INTO {table_name} ({', '.join(cols[:len(cols) // 2])}) VALUES ({placeholders});"
            data = cols[len(cols)//2:]
            cursor.execute(query, data); connection.commit(); cursor.close()
    except MySQLdb.ProgrammingError as e:
        print(e); flash('SQLscript is faulty.., on INSERT', e[1])
    except Exception as e:
        print(e); flash('An Exception occured!, on INSERT', 'error')


def update_table(table_name, where_clause, **cols):
    try:
        connection = mysql.connection; cursor = connection.cursor()
        columns = ", ".join([f"{col} = %s" for col in cols.keys()])
        query = f"UPDATE {table_name} SET {columns} WHERE {where_clause}"
        data = tuple(cols.values())
        cursor.execute(query, data);
        connection.commit(); cursor.close()
    except MySQLdb.ProgrammingError as e:
        print(e); flash(f'SQLscript is faulty, ON update!:{e}', 'error');
    except Exception as e:
        print(e); flash(f'An Exception occured! ON update:{e}', 'error')


def check_if_exists(table_name, id_name, asterisk = False, **cols):
    try:
        connection = mysql.connection
        cursor = connection.cursor()
        where_clause = " AND ".join([f"{col} = %s" for col in cols.keys()])
        query = ""
        if not asterisk:
            query = f"SELECT {id_name} FROM {table_name} WHERE {where_clause}";
        else:
            query = f"SELECT * FROM {table_name} WHERE {where_clause};"
        
        data = tuple(cols.values())
        cursor.execute(query, data);
        exists_id = cursor.fetchone(); cursor.close()
        return True if exists_id else False
    except Exception as e:
        print(e); flash(f'An Exception occured while checking {table_name}.')
        return True

def select_from_table(query, many=False):
    try:
        connection = mysql.connection
        cursor = connection.cursor()
        cursor.execute(query); result = cursor.fetchall() if many else cursor.fetchone(); 
        cursor.close()
        return result
    except Exception as e:
        print(e, sys.exc_info(), "in select")

def delete_from_table(query):
    try:
        connection = mysql.connection; cursor = connection.cursor()
        cursor.execute(query);
        connection.commit(); cursor.close();
    except Exception as e:
        print(e, sys.exc_info(), "in delete")


    
@app.route('/')
def index():
    create_table('students', """
        ID INT PRIMARY KEY AUTO_INCREMENT,
        FIRSTNAME VARCHAR(50),
        LASTNAME VARCHAR(50),
        CLASS VARCHAR(20),
        AGE INT,
        GENDER CHAR""")
    
    create_table('reports', """
        UID INT,
        FOREIGN KEY (UID) REFERENCES students(id),
        SUBJECT VARCHAR(100),
        UNIQUE KEY unique_ID_SUBJECT (UID, SUBJECT),
        TEST INT,
        EXAM INT,
        TOTAL INT,
        GRADE CHAR,
        REMARKS VARCHAR(15)""")
    
    create_table('performance',"""
        PID INT,
        FOREIGN KEY (PID) REFERENCES students(id),
        OVERALL INT,
        PERCENTAGE FLOAT,
        POSITION VARCHAR(5),
        OVERALL_GRADE CHAR,
        ROLL INT,
        PRESENT INT,
        CONDUCT VARCHAR(15),
        NEATNESS INT,
        CLASS_TEACHER VARCHAR(200),
        HEAD_TEACHER VARCHAR(200)
        """)
    session['logged_in'] = False
    return render_template('index.html')

@app.route('/add_student', methods=['GET', 'POST'])
def add_students():
    if request.method == 'POST':
        firstname = request.form.get('firstname').strip().title(); 
        lastname = request.form.get('lastname').strip().title(); class_name = request.form.get('class').strip().title()
        age = request.form.get('age').strip(); gender = request.form.get('gender')[0]

        row_exists = check_if_exists('students', "ID", FIRSTNAME=firstname, LASTNAME=lastname, CLASS=class_name, AGE=age, GENDER=gender);
        if not row_exists:
            insert_into_table('students', 'FIRSTNAME', 'LASTNAME', 'CLASS', 'AGE', 'GENDER', firstname, lastname, class_name, age, gender)
            flash(f'Student has been added successfully...', 'success')
        else:
            flash(f'Student already exists!', 'warning')

    return render_template('add_students.html')


@app.route('/classes')
def view_classes():
    sql_func = select_from_table("SELECT DISTINCT CLASS FROM students", many=True)
    classnames = [each[0] for each in sql_func]
    return render_template('classes.html', classnames=classnames)

# Route to display students for Classes
@app.route('/class/<classname>')
def classes(classname):
    clause = f"CLASS = '{classname}'";
    sql_func = select_from_table(f"SELECT FIRSTNAME, LASTNAME FROM students WHERE {clause}", many=True)
    students = [' '.join(names) for names in sql_func]; students_id = [];
    for each in students:
        fname, lname = each.split(' ');
        query_id = select_from_table(f"SELECT ID FROM students WHERE FIRSTNAME = '{fname}' AND LASTNAME = '{lname}' AND CLASS = '{classname}'");
        students_id.append(query_id[0])
    
    return render_template('students.html', class_name=classname, students=students, students_id=students_id)

#Route to login to edit report card
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json(); session['my_data'] = data;
        student = data.get('id', '')
        if student:
            return jsonify({'message':student, "type":"Edit Report Card", "error":False})
        else:
            return jsonify({'message': "This student doesn't exist", "type":"Edit Report Card", "error":True})


    return render_template('login.html')

#Do not restrict this route only if login has passed..
@app.route('/login_report', methods=['GET', 'POST'])
def edit_report():
    if request.method == 'POST':
        password = request.form.get('password');
        if password.lower() == 'admin':
            try:
                session['logged_in'] = True
                student = session['my_data'].get('id', '')
                if student:
                    return redirect(url_for('show_edit', sid=student))
                else:
                    flash(f'This Student seems not to exist.\n\nIt is advisable to update Student data.')
            except KeyError:
                return redirect(url_for('index'))
        else:
            flash('Wrong password!', 'error')
                
    return redirect(url_for('login'));

@app.route('/edit_report/<int:sid>', methods=['GET', 'POST'])
def show_edit(sid):
    clause = f"ID = '{sid}'"
    cols = ['Firstname', 'Lastname', 'Class', 'Age', 'Gender'];
    sql_query = select_from_table(f"SELECT FIRSTNAME, LASTNAME, CLASS, AGE, GENDER FROM students WHERE {clause}")
    student_dict = {cols[i]:sql_query[i] for i in range(len(sql_query))}; del cols
    
    if session['logged_in'] and request.method == 'GET':
        session['logged_in'] = False
        return render_template('edit_reportcard.html', student=student_dict);
    else:
        return redirect(url_for('login'))

@app.route('/perform_edit', methods=['POST'])
def perform_edit():
    #if request.method == 'POST':
    session['logged_in'] = True
    my_data = request.get_json();
    
    #personal-info
    firstname = my_data.get('fname', ''); lastname = my_data.get('lname', '')
    class_name = my_data.get('classname', '');
    clause = f"FIRSTNAME = '{firstname}' AND LASTNAME = '{lastname}' AND CLASS='{class_name}'"
    sId = select_from_table(f"SELECT ID FROM students WHERE {clause}")
    if sId:
        if my_data.get("type", None):
            #performance-info
            present = my_data.get('present', '')
            conduct = my_data.get('conduct', '').strip().title()
            neatness = my_data.get('neatness', ''); cls_comm = my_data.get('cls_comm', '')
            head_comm = my_data.get('head_comm', '');
            
            find_error = [False]
            find_error = perform_perf(sId[0], int(present), conduct, int(neatness), cls_comm, head_comm)
            
            if find_error[0]:
                return jsonify({"message":find_error[1], "type":"Edit", "error":True}) 
            else:
                return jsonify({"message":sId[0], "type":"Edit", "error":False})
        else:    
            #academic-info
            subject = my_data.get('subject', '').strip(); test = my_data.get('test', '').strip()
            exam = my_data.get('exam', '').strip()
            perform_reports(sId[0], subject, test, exam)
            return jsonify({"message":sId[0], "type":"Submit", "error":False})
    else:
        return jsonify({"message":"Student doesn't exist", "type":"Edit" if data.get("type", None) else "Submit", "error":True})



def perform_reports(id_, subject, test, exam): 
    try:
        total = int(test) + int(exam); grade = 'F';
        print("TOTAL:", total)
        grade_ranges = {(70, 100): 'A', (60, 69): 'B', (50, 59): 'C',
        (40, 49): 'D', (0, 39): 'F'}
        
        for (lower, upper), g in grade_ranges.items():
            if lower <= total <= upper:
                grade = g; break

        print("GRADE:", grade)
        remarks = {'A':"Excellent", 'B':"V.Good", 'C':"Good", 'D':"Pass", 'F':"Fail"}
        remark = remarks[grade]
        print("REMARK", remark)
        row_subject = check_if_exists('reports', "UID", SUBJECT=subject, UID=id_)
        if not row_subject:
            print("New Subject")
            insert_into_table('reports', 'UID', 'SUBJECT', 'TEST', 'EXAM', 'TOTAL', 'GRADE', 'REMARKS', id_, subject, test, exam, total, grade, remark);
            flash("New report details added..")
        else:
            print("Existing subject.")
            update_table("reports", f"UID = '{id_}' AND SUBJECT = '{subject}'", TEST=test, EXAM=exam, GRADE=grade, TOTAL=total, REMARKS=remark);
            flash("Changes made to existing report details..") 
        
        return [False]
    except Exception as e:
        print(e); return [True, str(e)]

def perform_perf(id_, present, conduct, neatness, cls_comm, head_comm):    
    try:
        row_exists = select_from_table(f"SELECT PID FROM performance WHERE PID = '{id_}'");
        if not row_exists:
            insert_into_table('performance', 'PID', 'PRESENT', 'CONDUCT', 'NEATNESS', 'CLASS_TEACHER', 'HEAD_TEACHER', id_, present, conduct, neatness, cls_comm, head_comm);
            flash("Successfully submitted performance..")
        else:
            update_table('performance', f"PID = '{id_}'", PRESENT=present, CONDUCT=conduct, NEATNESS=neatness, CLASS_TEACHER=cls_comm, HEAD_TEACHER=head_comm)
            flash("Making changes to existing performance..")
        return [False]
    except Exception as e:
        print(e, sys.exc_info())
        return [True, str(e)]


def cal_student_pos(id_, pos):
    """The following algorithm is how to calculate the student's position in the class."""
    grade_ranges = {(70, 101): 'A', (60, 70): 'B', (50, 60): 'C',
        (40, 50): 'D', (0, 40): 'F'}
    query_overall = select_from_table(f"SELECT SUM(TOTAL) FROM reports WHERE UID = '{id_}'")

    overall = query_overall[0] if query_overall[0] else 0;
    print("OVERALL:", overall)
    #cal_percentage
    query_percent = select_from_table(f"SELECT COUNT(SUBJECT) FROM reports WHERE UID = '{id_}'")
    subnum = max(1, query_percent[0])
    percent = overall / subnum;
    print("PERCENTAGE:", percent)
    #cal_overallgrade
    over_grade = 'F';
    for (lower, upper), og in grade_ranges.items():
        if lower <= percent < upper:
            over_grade = og; break
        
    print("OVERALL_GRADE:", over_grade)
    #fetch_class
    query_class = select_from_table(f"SELECT CLASS FROM students WHERE ID = '{id_}'")
    class_ = query_class[0];
    #fetch_all_students 
    query_fetchall = select_from_table(f"SELECT ID FROM students WHERE CLASS = '{class_}'", many=True)
    roll = len(query_fetchall)
        
    rexists = check_if_exists("performance", "PID", PID=id_)
    if not rexists:
        insert_into_table('performance', 'PID', 'ROLL', 'OVERALL', 'PERCENTAGE', 'OVERALL_GRADE', id_, roll, overall, percent, over_grade);
    else:
        update_table('performance', f"PID = '{id_}'", ROLL=roll, OVERALL=overall, PERCENTAGE=percent, OVERALL_GRADE=over_grade)
        
    #fetch_class
    query_class = select_from_table(f"SELECT CLASS FROM students WHERE ID = '{id_}'")
    class_ = query_class[0];
    
    #fetch_all_students 
    query_fetchall = select_from_table(f"SELECT ID FROM students WHERE CLASS = '{class_}'", many=True)

    #fetch_all_overall
    overall_arr = [];
    #use loop to iterate over each id
    for each in query_fetchall:
        each_id = each[0];
        query_each_overall = select_from_table(f"SELECT OVERALL FROM performance WHERE PID = {each_id}")
        overall_arr.append(query_each_overall[0] if query_each_overall else 0)
    
    overall_arr.sort() # in ascending order
    print(overall_arr)
    total_in_class = len(overall_arr);
    
    #iterate overall_arr
    X = total_in_class
    for each in overall_arr:
        if each == overall:
            pos = X; break
        X -= 1
        
    query_pos = select_from_table(f"SELECT POSITION FROM performance WHERE PID = '{id_}'")
    if not query_pos:
        insert_into_table('performance', 'POSITION', pos)
    else:
        update_table('performance', f"PID = '{id_}'", POSITION=pos)
        


@app.route('/view_report/<int:sid>', methods=['GET', 'DELETE'])
def view_report(sid):
    clause = f"ID = '{sid}'"; clause_rep = f"UID = '{sid}'"; clause_per = f"PID = '{sid}'"
    sql_query = select_from_table(f"SELECT FIRSTNAME, LASTNAME, CLASS, AGE, GENDER FROM students WHERE {clause}")
    cols = ['NAME', 'CLASS', 'AGE', 'SEX'];
    sql_query = (sql_query[0] +', '+ sql_query[1],) + (sql_query[2],str(sql_query[3])+" years")  + ("Male" if sql_query[-1].lower() == 'm' else 'Female',);
    
    sql_query_report = select_from_table(f"SELECT * FROM reports WHERE {clause_rep}", many=True);
    report_arr = [];
    for each in sql_query_report:
        report_arr.append(each[1:])
    student_dict = {cols[i]:sql_query[i] for i in range(len(sql_query))}; del cols

    query_performance = select_from_table(f"SELECT * FROM performance WHERE {clause_per}")
    query_performance = query_performance[1:] if query_performance else []
    fp = query_performance[:8]; sp = query_performance[8:]
    
    colsfp = ['TOTAL', 'PERCENTAGE', 'POSITION', 'GRADE', 'NO.ON.ROLL', 'PRESENT', 'CONDUCT', 'NEATNESS']; 
    colssp = ["CLASS TEACHER's COMMENT", "HEAD TEACHER's COMMENT"]
    fp_dict = {colsfp[i]:fp[i] for i in range(len(fp))}
    sp_dict = {colssp[i]:sp[i] for i in range(len(sp))}
    
    cal_student_pos(sid, 1)
    if request.method == "DELETE":
        data = request.get_json(); subject = data["subject"];
        delete_from_table(f"DELETE FROM reports WHERE {clause_rep} AND SUBJECT = '{subject}'")

        return jsonify({"message":"Delete row successfully"})
    else:
        return render_template('report_card.html', id_=sid, students=student_dict, reports=report_arr, student_per=fp_dict, general_per=sp_dict);
    



if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5005)