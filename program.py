import sqlite3
import os 

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "csiaa.db")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("PRAGMA foreign_keys = ON")

cursor.execute("""
CREATE TABLE IF NOT EXISTS Students (
    StudentID   TEXT PRIMARY KEY,
    Name       TEXT,
    GradeLevel  INTEGER
);
""")

# create teacher table
cursor.execute("""
CREATE TABLE IF NOT EXISTS Teacher (
    TeacherID   INTEGER PRIMARY KEY,
    TeacherName    TEXT
);
""")

# 3. Create Courses table
cursor.execute("""
CREATE TABLE IF NOT EXISTS Courses (
    CourseID    NUMERIC PRIMARY KEY,
    CourseName  TEXT,
    CourseLevel TEXT,
    TeacherID INTEGER,
    FOREIGN KEY (TeacherID) REFERENCES Teacher(TeacherID)
);
""")


# 4. Create Enrollments table

# This table links Students and Courses using foreign keys.
cursor.execute("""
CREATE TABLE IF NOT EXISTS Enrollments (
    EnrollmentID INTEGER PRIMARY KEY AUTOINCREMENT,
    StudentID   TEXT,
    CourseID    NUMERIC,
    FOREIGN KEY (StudentID) REFERENCES Students(StudentID),
    FOREIGN KEY (CourseID) REFERENCES Courses(CourseID)
);
""")

# adds assessments to the list 
cursor.execute("""
CREATE TABLE IF NOT EXISTS Assessments (
    AssessmentID INTEGER PRIMARY KEY AUTOINCREMENT,
    AssessmentName    TEXT NOT NULL,
    CourseID     NUMERIC NOT NULL,
    DueDate      TEXT NOT NULL,
    Priority     INTEGER CHECK (Priority IN (0,1)),
    CreatedAt TEXT DEFAULT (datetime('now','localtime')),
    FOREIGN KEY (CourseID) REFERENCES Courses(CourseID)
);
""")

#adjust student table if it existed
cursor.execute("PRAGMA table_info(Students)")
student_cols = [c[1] for c in cursor.fetchall()]
if "Level" not in student_cols:
    cursor.execute("ALTER TABLE Students ADD COLUMN Level TEXT")
    cursor.execute("UPDATE Students SET Level='SL' WHERE Level IS NULL")  # backfill default

# adjust assessment table if it existed
cursor.execute("PRAGMA table_info(Assessments)")
ass_cols = [c[1] for c in cursor.fetchall()]
if "Audience" not in ass_cols:
    cursor.execute("ALTER TABLE Assessments ADD COLUMN Audience TEXT")
    cursor.execute("UPDATE Assessments SET Audience='Both' WHERE Audience IS NULL")  # backfill old rows


# ---- schema migration: ensure CreatedAt exists ----
cursor.execute("PRAGMA table_info(Assessments)")
cols = [c[1] for c in cursor.fetchall()]

if "CreatedAt" not in cols:
    cursor.execute("ALTER TABLE Assessments ADD COLUMN CreatedAt TEXT")

# ---- backfill CreatedAt for old rows ----
cursor.execute("""
UPDATE Assessments
SET CreatedAt = datetime('now','localtime')
WHERE CreatedAt IS NULL
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
    name = input("Name:")
    grade= int(input("Grade level:"))
    sql = "INSERT INTO Students (StudentID,Name,GradeLevel) VALUES (?,?,?)"
    cursor.execute(sql, (id,name,grade))
    conn.commit()
    print("Student added successfully")

def view_student():
    sql= "SELECT * FROM Students"
    rows=cursor.execute(sql)
    print("id | name | grade")
    for row in rows:
        print(row[0],"|",row[1],"| Gr",row[2])

def delete_student():
    id=input("Enter Student ID to delete:")
    sql= "DELETE FROM Students WHERE StudentID=?"
    cursor.execute(sql,(id,))
    conn.commit()
    print("Student deleted successfully")

def add_course():
    id= int(input("Enter Course ID:"))
    courseName= input("Enter Course Name:")
    courseLevel = input("Enter Course Level:")
    teacher= int(input("Enter Teacher ID:"))
    sql="INSERT INTO Courses (CourseID,CourseName,CourseLevel,TeacherID)VALUES (?,?,?,?)"
    cursor.execute(sql, (id,courseName,courseLevel,teacher))
    conn.commit()
    print("Course added successfully")

def delete_course():
    print("Course list")
    print("--------------------------------")
    view_course()
    courseid= input("Enter Course ID to remove:")
    sql= "DELETE FROM Courses WHERE CourseID=?"
    cursor.execute(sql,(courseid,))
    conn.commit()
    print("Course removed successfully")

def view_course():
    sql="SELECT * FROM Courses"
    rows=cursor.execute(sql)
    print("id | name | level | teacher")
    for row in rows:
        print(row[0],row[1],row[2],row[3])

def add_enrollment():
    #shows the list of student iD
    print("Student list")
    print("--------------------------------")
    view_student()
    studentid= input("Enter Student ID to enroll:")
    print("Course list")
    print("--------------------------------")
    view_course()
    courseid=int(input("Enter Course ID:"))
    sql="INSERT INTO Enrollments (StudentID,CourseID)VALUES (?,?)"
    cursor.execute(sql, (studentid,courseid))
    conn.commit()
    print("Course added successfully")


def view_enrollment():
    sql="""SELECT Students.StudentID,Students.Name,Courses.CourseID,Courses.CourseName,Courses.CourseLevel
    FROM Enrollments
    JOIN Students ON Enrollments.StudentID = Students.StudentID
    JOIN Courses ON Enrollments.CourseID = Courses.CourseID;
    """
    rows=cursor.execute(sql)
    print("StudentID | Name | CourseID | CourseName | CourseLevel")

    for row in rows:
        print(row[0],"|",row[1],"|",row[2], "|",row[3],"|",row[4])

def add_assessment():
    print("------ADD ASSESSMENT-----")
    view_course()
    course_id = int(input("Enter Course ID: "))
    assessment_name = input("Enter Assessment Name: ")
    due_date = input("Enter Due Date (YYYY-MM-DD): ")
    priority = int(input("Priority (1 = Major, 0 = Minor): "))
    if priority not in (0,1):
            print ("Priority must be 0 or 1")
            return
    sql = """
    INSERT INTO Assessments (CourseID, AssessmentName, DueDate, Priority, CreatedAt)
    VALUES (?, ?, ?, ?, datetime('now','localtime'))
    """
    cursor.execute(sql, (course_id, assessment_name, due_date, priority))
    conn.commit()

def view_assessment():
    sql = "SELECT AssessmentID, AssessmentName, CourseID, DueDate, Priority, CreatedAt FROM Assessments"
    rows = cursor.execute(sql)
    print("AssessmentID | Name | CourseID | DueDate | Priority | CreatedAt")
    for row in rows:
        print(row[0], "|", row[1], "|", row[2], "|", row[3], "|", row[4], "|", row[5])

def delete_assessment():
    print("Assessment list")
    print("--------------------------------")
    view_assessment()
    courseid= input("Enter Assessment ID to remove:")
    sql= "DELETE FROM Assessments WHERE AssessmentID=?"
    cursor.execute(sql,(courseid,))
    conn.commit()
    print("Assessment removed successfully")

def delete_assessment_all():
    confirm = input("Type DELETE to remove ALL assessments: ").strip().upper()
    if confirm != "DELETE":
        print("Cancelled.")
        return
    cursor.execute("DELETE FROM Assessments")
    conn.commit()
    print("All assessments removed.")

def detect_assessment_conflicts():
    sql = """
    WITH Overloads AS (
        SELECT
            e.StudentID,
            strftime('%Y-%W', a.DueDate) AS YearWeek,
            COUNT(*) AS MajorCount
        FROM Enrollments e
        JOIN Assessments a ON e.CourseID = a.CourseID
        WHERE a.Priority = 1
        GROUP BY e.StudentID, YearWeek
        HAVING COUNT(*) > 3
    )
    SELECT
        o.StudentID,
        s.Name AS StudentName,
        o.YearWeek,
        o.MajorCount,

        a.AssessmentID,
        a.AssessmentName,
        a.DueDate,
        a.CreatedAt,

        c.CourseID,
        c.CourseName,
        c.CourseLevel,

        t.TeacherName
    FROM Overloads o
    JOIN Students s ON s.StudentID = o.StudentID
    JOIN Enrollments e ON e.StudentID = o.StudentID
    JOIN Assessments a ON a.CourseID = e.CourseID
    JOIN Courses c ON c.CourseID = a.CourseID
    LEFT JOIN Teacher t ON t.TeacherID = c.TeacherID
    WHERE a.Priority = 1
      AND strftime('%Y-%W', a.DueDate) = o.YearWeek
    ORDER BY o.YearWeek, s.Name, a.DueDate, c.CourseName, a.AssessmentName;
    """

    rows = cursor.execute(sql).fetchall()

    if not rows:
        print("No assessment conflicts detected.")
        return

    # Group in Python for readable output
    current_key = None
    for r in rows:
        student_id, student_name, year_week, major_count = r[0], r[1], r[2], r[3]
        key = (student_id, year_week)

        if key != current_key:
            if current_key is not None:
                print("-" * 60)
            print("ASSESSMENT CONFLICT")
            print(f"Student: {student_id} | {student_name}")
            print(f"Week: {year_week} | Major assessments: {major_count}")
            print("AssessmentID | AssessmentName | DueDate | CreatedAt | Course | Level | Teacher")
            current_key = key

        assessment_id, assessment_name, due_date, created_at = r[4], r[5], r[6], r[7]
        course_id, course_name, course_level, teacher_name = r[8], r[9], r[10], r[11]

        print(
            f"{assessment_id} | {assessment_name} | {due_date} | {created_at} | "
            f"{course_id}-{course_name} | {course_level} | {teacher_name}"
        )


while True:
    try:
        print("======================")
        print("press 1 to Add Student")
        print("press 2 to View all students")
        print("press 3 to Delete Student")
        print("press 4 to Add Course")
        print("press 5 to Remove Course")
        print("press 6 to Add enrollment")
        print("press 7 to View all Enrollments")
        print("press 8 to Add Assessment")
        print("press 9 to View Assessment")
        print("press 10 to Delete Assessment")
        print("press 11 to Delete ALL Assessments")
        print("press 12 to view clashes")
        
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
            delete_course()
        elif user==6:
            add_enrollment()
        elif user==7:
            view_enrollment()
        elif user==8:
            add_assessment()
            detect_assessment_conflicts()
        elif user==9:
            view_assessment()
        elif user == 10:
            delete_assessment()
        elif user==11:
            delete_assessment_all()
        elif user== 12:
            detect_assessment_conflicts()


    except sqlite3.Error as e:
        print(e)

conn.close()