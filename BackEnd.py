import sqlite3
from datetime import datetime

def get_connection(db_name="csiaa.db"):
    conn = sqlite3.connect(db_name)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def ensure_schema(conn):
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS Teacher (
        TeacherID INTEGER PRIMARY KEY AUTOINCREMENT,
        TeacherName TEXT NOT NULL UNIQUE
    );

    CREATE TABLE IF NOT EXISTS Courses (
        CourseID INTEGER PRIMARY KEY AUTOINCREMENT,
        CourseName TEXT NOT NULL,
        CourseLevel TEXT NOT NULL CHECK (CourseLevel IN ('SL','HL','Core')),
        TeacherID INTEGER,
        FOREIGN KEY (TeacherID) REFERENCES Teacher(TeacherID) ON DELETE SET NULL
    );

    CREATE TABLE IF NOT EXISTS Students (
        StudentID TEXT PRIMARY KEY,
        Name TEXT NOT NULL,
        GradeLevel INTEGER NOT NULL
    );

    CREATE TABLE IF NOT EXISTS Enrollments (
        EnrollmentID INTEGER PRIMARY KEY AUTOINCREMENT,
        StudentID TEXT NOT NULL,
        CourseID INTEGER NOT NULL,
        UNIQUE(StudentID, CourseID),
        FOREIGN KEY (StudentID) REFERENCES Students(StudentID) ON DELETE CASCADE,
        FOREIGN KEY (CourseID) REFERENCES Courses(CourseID) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS Assessments (
        AssessmentID INTEGER PRIMARY KEY AUTOINCREMENT,
        AssessmentName TEXT NOT NULL,
        DueDate TEXT NOT NULL,
        Priority INTEGER NOT NULL CHECK (Priority IN (0,1)),
        CreatedAt TEXT NOT NULL DEFAULT (datetime('now','localtime')),
        Audience TEXT NOT NULL CHECK (Audience IN ('SL','HL','Both'))
    );

    CREATE TABLE IF NOT EXISTS AssessmentTargets (
        AssessmentID INTEGER NOT NULL,
        CourseID INTEGER NOT NULL,
        PRIMARY KEY (AssessmentID, CourseID),
        FOREIGN KEY (AssessmentID) REFERENCES Assessments(AssessmentID) ON DELETE CASCADE,
        FOREIGN KEY (CourseID) REFERENCES Courses(CourseID) ON DELETE CASCADE
    );

    CREATE INDEX IF NOT EXISTS idx_enroll_student ON Enrollments(StudentID);
    CREATE INDEX IF NOT EXISTS idx_target_course ON AssessmentTargets(CourseID);
    CREATE INDEX IF NOT EXISTS idx_assessment_date ON Assessments(DueDate);
    """)
    conn.commit()

def add_teacher(conn, teacher_name):
    conn.execute(
        "INSERT INTO Teacher (TeacherName) VALUES (?)",
        (teacher_name,)
    )
    conn.commit()


def get_all_teachers(conn):
    return conn.execute(
        "SELECT * FROM Teacher ORDER BY TeacherName"
    ).fetchall()


def delete_teacher(conn, teacher_id):
    conn.execute(
        "DELETE FROM Teacher WHERE TeacherID = ?",
        (teacher_id,)
    )
    conn.commit()

def add_course(conn, name, level, teacher_id):
    conn.execute(
        "INSERT INTO Courses (CourseName, CourseLevel, TeacherID) VALUES (?,?,?)",
        (name, level, teacher_id)
    )
    conn.commit()


def get_all_courses(conn):
    return conn.execute("""
        SELECT c.CourseID, c.CourseName, c.CourseLevel, t.TeacherName
        FROM Courses c
        LEFT JOIN Teacher t ON c.TeacherID = t.TeacherID
        ORDER BY c.CourseName, c.CourseLevel
    """).fetchall()


def delete_course(conn, course_id):
    conn.execute(
        "DELETE FROM Courses WHERE CourseID = ?",
        (course_id,)
    )
    conn.commit()

def add_student(conn, student_id, name, grade):
    conn.execute(
        "INSERT INTO Students (StudentID, Name, GradeLevel) VALUES (?,?,?)",
        (student_id, name, grade)
    )
    conn.commit()


def get_all_students(conn):
    return conn.execute(
        "SELECT * FROM Students ORDER BY StudentID"
    ).fetchall()


def delete_student(conn, student_id):
    conn.execute(
        "DELETE FROM Students WHERE StudentID = ?",
        (student_id,)
    )
    conn.commit()

def enroll_student(conn, student_id, course_id):
    conn.execute(
        "INSERT INTO Enrollments (StudentID, CourseID) VALUES (?,?)",
        (student_id, course_id)
    )
    conn.commit()


def get_student_courses(conn, student_id):
    return conn.execute("""
        SELECT c.CourseID, c.CourseName, c.CourseLevel
        FROM Enrollments e
        JOIN Courses c ON e.CourseID = c.CourseID
        WHERE e.StudentID = ?
    """, (student_id,)).fetchall()

def add_assessment(conn, name, due_date, priority, audience, target_course_ids):
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO Assessments (AssessmentName, DueDate, Priority, Audience)
        VALUES (?,?,?,?)
    """, (name, due_date, priority, audience))

    assessment_id = cursor.lastrowid

    for cid in target_course_ids:
        cursor.execute("""
            INSERT INTO AssessmentTargets (AssessmentID, CourseID)
            VALUES (?,?)
        """, (assessment_id, cid))

    conn.commit()


def get_all_assessments(conn):
    return conn.execute("""
        SELECT a.AssessmentID,
               a.AssessmentName,
               a.DueDate,
               a.Priority,
               a.Audience,
               a.CreatedAt,
               GROUP_CONCAT(at.CourseID) AS TargetCourseIDs
        FROM Assessments a
        LEFT JOIN AssessmentTargets at ON a.AssessmentID = at.AssessmentID
        GROUP BY a.AssessmentID
        ORDER BY a.DueDate
    """).fetchall()


def delete_assessment(conn, assessment_id):
    conn.execute(
        "DELETE FROM Assessments WHERE AssessmentID = ?",
        (assessment_id,)
    )
    conn.commit()

def detect_assessment_conflicts(conn):
    """
    Returns students who have >= 4 major assessments (Priority = 1)
    in the same ISO week.
    """

    return conn.execute("""
        SELECT 
            s.StudentID,
            s.Name,
            strftime('%Y-%W', a.DueDate) AS Week,
            COUNT(*) AS MajorCount
        FROM Students s
        JOIN Enrollments e ON s.StudentID = e.StudentID
        JOIN AssessmentTargets at ON e.CourseID = at.CourseID
        JOIN Assessments a ON at.AssessmentID = a.AssessmentID
        WHERE a.Priority = 1
        GROUP BY s.StudentID, Week
        HAVING COUNT(*) >= 4
        ORDER BY Week DESC
    """).fetchall()


def get_student_conflict_details(conn, student_id, week):
    """
    Returns full assessment list for a student in a specific week.
    """

    return conn.execute("""
        SELECT 
            a.AssessmentID,
            a.AssessmentName,
            a.DueDate,
            a.Audience,
            c.CourseName,
            c.CourseLevel,
            t.TeacherName
        FROM Enrollments e
        JOIN AssessmentTargets at ON e.CourseID = at.CourseID
        JOIN Assessments a ON at.AssessmentID = a.AssessmentID
        JOIN Courses c ON e.CourseID = c.CourseID
        LEFT JOIN Teacher t ON c.TeacherID = t.TeacherID
        WHERE e.StudentID = ?
          AND strftime('%Y-%W', a.DueDate) = ?
          AND a.Priority = 1
        ORDER BY a.DueDate
    """, (student_id, week)).fetchall()

# generate report function

def generate_student_report(conn, student_id):
    cursor = conn.cursor()

    # Get student name
    cursor.execute("""
        SELECT Name FROM Students
        WHERE StudentID = ?
    """, (student_id,))
    student = cursor.fetchone()
    if not student:
        return None

    student_name = student["Name"]

    cursor.execute("""
        SELECT 
            a.AssessmentID,
            a.AssessmentName,
            a.DueDate,
            a.Priority,
            c.CourseName,
            c.CourseLevel,
            t.TeacherName
        FROM Assessments a
        JOIN AssessmentTargets at ON a.AssessmentID = at.AssessmentID
        JOIN Courses c ON at.CourseID = c.CourseID
        JOIN Enrollments e ON e.CourseID = c.CourseID
        JOIN Teachers t ON c.TeacherID = t.TeacherID
        WHERE e.StudentID = ?
        ORDER BY a.DueDate
    """, (student_id,))

    rows = cursor.fetchall()

    report_data = []
    overload_weeks = {}
    major_count = 0

    for r in rows:
        week = datetime.datetime.strptime(r["DueDate"], "%Y-%m-%d").strftime("%Y-%W")

        if r["Priority"] == 1:
            major_count += 1
            overload_weeks[week] = overload_weeks.get(week, 0) + 1

        report_data.append({
            "Assessment": r["AssessmentName"],
            "Course": r["CourseName"],
            "Level": r["CourseLevel"],
            "DueDate": r["DueDate"],
            "Week": week,
            "Teacher": r["TeacherName"],
            "Priority": r["Priority"]
        })

    overloaded = [w for w, count in overload_weeks.items() if count >= 4]

    return {
        "StudentID": student_id,
        "Name": student_name,
        "TotalAssessments": len(rows),
        "TotalMajor": major_count,
        "OverloadedWeeks": overloaded,
        "Details": report_data
    }

#suggest nearest 3 dates available function
def suggest_alternative_date(conn, student_id, original_date, max_search_days=14):
    import datetime

    cursor = conn.cursor()
    base_date = datetime.datetime.strptime(original_date, "%Y-%m-%d")

    def is_week_overloaded(test_date):
        week = test_date.strftime("%Y-%W")

        cursor.execute("""
            SELECT COUNT(*) as cnt
            FROM Assessments a
            JOIN AssessmentTargets at ON a.AssessmentID = at.AssessmentID
            JOIN Enrollments e ON e.CourseID = at.CourseID
            WHERE e.StudentID = ?
            AND a.Priority = 1
            AND strftime('%Y-%W', a.DueDate) = ?
        """, (student_id, week))

        result = cursor.fetchone()
        return result["cnt"] >= 4

    for i in range(1, max_search_days + 1):
        forward = base_date + datetime.timedelta(days=i)
        backward = base_date - datetime.timedelta(days=i)

        if not is_week_overloaded(forward):
            return forward.strftime("%Y-%m-%d")

        if not is_week_overloaded(backward):
            return backward.strftime("%Y-%m-%d")

    return None