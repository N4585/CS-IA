import sqlite3

conn = sqlite3.connect("school.db")
cursor = conn.cursor()

cursor.execute("PRAGMA foreign_keys = ON")

cursor.execute("""
CREATE TABLE IF NOT EXISTS Students (
    StudentID   TEXT PRIMARY KEY,
    Fname       TEXT,
    Lname       TEXT,
    GradeLevel  INTEGER
);
""")


# 3. Create Courses table
cursor.execute("""
CREATE TABLE IF NOT EXISTS Courses (
    CourseID    INTEGER PRIMARY KEY,
    CourseName  TEXT,
    TeacherName TEXT
);
""")


# 4. Create Enrolments table

# This table links Students and Courses using foreign keys.
cursor.execute("""
CREATE TABLE IF NOT EXISTS Enrolments (
    EnrolmentID INTEGER PRIMARY KEY AUTOINCREMENT,
    StudentID   TEXT,
    CourseID    INTEGER,
    FOREIGN KEY (StudentID) REFERENCES Students(StudentID),
    FOREIGN KEY (CourseID) REFERENCES Courses(CourseID)
);
""")
# ---------------------------
# 5. Save changes and close
# ---------------------------
conn.commit()

#----------------------------
# function 1- Add student
#----------------------------
def add_student():
    print("------ADD STUDENT-----")
    id= input("Enter Student id:")
    fname = input("First name:")
    lname = input("Last name:")
    grade= int(input("Grade level:"))
    sql = "INSERT INTO Students (StudentID,Fname,Lname,GradeLevel) VALUES (?,?,?,?)"
    cursor.execute(sql, (id,fname,lname,grade))
    conn.commit()
    print("Student added successfully")

def view_student():
    sql= "SELECT * FROM Students"
    rows=cursor.execute(sql)
    print("id | name | grade")
    for row in rows:
        print(row[0],"|",row[1],row[2],"| Gr",row[3])

def delete_student():
    id=input("Enter Student ID to delete:")
    sql= "DELETE FROM Students WHERE StudentID=?"
    cursor.execute(sql,(id,))
    conn.commit()
    print("Student deleted successfully")

def add_course():
    id= int(input("Enter Course ID:"))
    courseName= input("Enter Course Name:")
    teacher= input("Enter Teacher Name:")
    sql="INSERT INTO Courses (CourseID,CourseName,TeacherName)VALUES (?,?,?)"
    cursor.execute(sql, (id,courseName,teacher))
    conn.commit()
    print("Course added successfully")

def view_course():
    sql="SELECT * FROM Courses"
    rows=cursor.execute(sql)
    print("id | name | teacher")
    for row in rows:
        print(row[0],row[1],row[2])

def add_enrolment():
    #shows the list of student iD
    print("Student list")
    print("--------------------------------")
    view_student()
    studentid= input("Enter Student ID to enrol:")
    print("Course list")
    print("--------------------------------")
    view_course()
    courseid=int(input("Enter Course ID:"))
    sql="INSERT INTO Enrolments (StudentID,CourseID)VALUES (?,?)"
    cursor.execute(sql, (studentid,courseid))
    conn.commit()
    print("Course added successfully")


def view_enrolment():
    sql="""SELECT Students.StudentID,Students.Fname,Students.Lname,Courses.CourseID,Courses.Coursename,Courses.teachername 
    FROM Enrolments
    INNER JOIN Students ON Enrolments.StudentID = Students.StudentID
    INNER JOIN Courses ON Enrolments.CourseID = Courses.CourseID
    """
    rows=cursor.execute(sql)
    print("ID | FName | LName | CourseID | CourseName | TeacherName")

    for row in rows:
        print(row[0],"|",row[1],"|",row[2],"|",row[3],"|",row[4],"|",row[5])


while True:
    cursor = conn.cursor()
    conn.commit()
    try:
        print("======================")
        print("press 1 to Add Student")
        print("press 2 to View all students")
        print("press 3 to Delete Student")
        print("press 4 to Add Course")
        print("press 5 to Add enrolment")
        print("press 6 to View all Enrolments")
        print("press 0 to exit")
        user=int(input())
        if user==0:
            break
        elif user==1:
            add_student()
        elif user==2:
            view_student()
        elif user==3:
            delete_student()
        elif user==4:
            add_course()
        elif user==5:
            add_enrolment()
        elif user==6:
            view_enrolment()



    except sqlite3.Error as e:
        print(e)
    cursor.close()
conn.close()