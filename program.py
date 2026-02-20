import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "csiaa.db")


def ensure_schema_and_migrate(cursor, conn):
    cursor.execute("PRAGMA foreign_keys = ON")

    # --- Base tables ---
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Teacher (
        TeacherID INTEGER PRIMARY KEY,
        TeacherName TEXT NOT NULL
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Courses (
        CourseID NUMERIC PRIMARY KEY,
        CourseName TEXT NOT NULL,
        CourseLevel TEXT NOT NULL,
        TeacherID INTEGER,
        FOREIGN KEY (TeacherID) REFERENCES Teacher(TeacherID)
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Students (
        StudentID TEXT PRIMARY KEY,
        Name TEXT NOT NULL,
        GradeLevel INTEGER NOT NULL
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Enrollments (
        EnrollmentID INTEGER PRIMARY KEY AUTOINCREMENT,
        StudentID TEXT NOT NULL,
        CourseID NUMERIC NOT NULL,
        FOREIGN KEY (StudentID) REFERENCES Students(StudentID) ON DELETE CASCADE,
        FOREIGN KEY (CourseID) REFERENCES Courses(CourseID) ON DELETE CASCADE,
        UNIQUE(StudentID, CourseID)
    );
    """)

    # --- Check existing Assessments table ---
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='Assessments'")
    assessments_exists = cursor.fetchone() is not None
    old_cols = []
    if assessments_exists:
        cursor.execute("PRAGMA table_info(Assessments)")
        old_cols = [c[1] for c in cursor.fetchall()]

    # --- If Assessments doesn't exist, create it now (so FK works) ---
    if not assessments_exists:
        cursor.execute("""
        CREATE TABLE Assessments (
            AssessmentID INTEGER PRIMARY KEY AUTOINCREMENT,
            AssessmentName TEXT NOT NULL,
            DueDate TEXT NOT NULL,
            Priority INTEGER NOT NULL CHECK (Priority IN (0,1)),
            CreatedAt TEXT NOT NULL DEFAULT (datetime('now','localtime')),
            Audience TEXT NOT NULL DEFAULT 'Both'
        );
        """)
        conn.commit()
        old_cols = ["AssessmentID","AssessmentName","DueDate","Priority","CreatedAt","Audience"]

    # --- Ensure AssessmentTargets exists (after Assessments exists) ---
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS AssessmentTargets (
        AssessmentID INTEGER NOT NULL,
        CourseID NUMERIC NOT NULL,
        PRIMARY KEY (AssessmentID, CourseID),
        FOREIGN KEY (AssessmentID) REFERENCES Assessments(AssessmentID) ON DELETE CASCADE,
        FOREIGN KEY (CourseID) REFERENCES Courses(CourseID) ON DELETE CASCADE
    );
    """)

    # --- Migrate old schema if CourseID existed in Assessments ---
    if "CourseID" in old_cols:
        print("Migrating Assessments: removing CourseID and backfilling AssessmentTargets...")

        cursor.execute("PRAGMA foreign_keys = OFF")
        cursor.execute("ALTER TABLE Assessments RENAME TO Assessments_old")

        cursor.execute("""
        CREATE TABLE Assessments (
            AssessmentID INTEGER PRIMARY KEY AUTOINCREMENT,
            AssessmentName TEXT NOT NULL,
            DueDate TEXT NOT NULL,
            Priority INTEGER NOT NULL CHECK (Priority IN (0,1)),
            CreatedAt TEXT NOT NULL DEFAULT (datetime('now','localtime')),
            Audience TEXT NOT NULL DEFAULT 'Both'
        );
        """)

        cursor.execute("""
        INSERT INTO Assessments (AssessmentID, AssessmentName, DueDate, Priority, CreatedAt, Audience)
        SELECT
            AssessmentID,
            AssessmentName,
            DueDate,
            Priority,
            COALESCE(CreatedAt, datetime('now','localtime')),
            COALESCE(Audience, 'Both')
        FROM Assessments_old
        """)

        cursor.execute("""
        INSERT OR IGNORE INTO AssessmentTargets (AssessmentID, CourseID)
        SELECT AssessmentID, CourseID
        FROM Assessments_old
        WHERE CourseID IS NOT NULL
        """)

        cursor.execute("DROP TABLE Assessments_old")
        cursor.execute("PRAGMA foreign_keys = ON")
        conn.commit()
        print("Migration complete.")

    # --- Safety net: add missing columns (if you had old tables) ---
    cursor.execute("PRAGMA table_info(Assessments)")
    cols = [c[1] for c in cursor.fetchall()]

    if "CreatedAt" not in cols:
        cursor.execute("ALTER TABLE Assessments ADD COLUMN CreatedAt TEXT")
        cursor.execute("""
            UPDATE Assessments
            SET CreatedAt = datetime('now','localtime')
            WHERE CreatedAt IS NULL
        """)

    if "Audience" not in cols:
        cursor.execute("ALTER TABLE Assessments ADD COLUMN Audience TEXT")
        cursor.execute("UPDATE Assessments SET Audience='Both' WHERE Audience IS NULL")

    conn.commit()



def add_student(cursor, conn):
    print("------ADD STUDENT-----")
    sid = input("Enter Student ID: ").strip()
    name = input("Name: ").strip()
    grade = int(input("Grade level: ").strip())

    cursor.execute(
        "INSERT INTO Students (StudentID, Name, GradeLevel) VALUES (?,?,?)",
        (sid, name, grade)
    )
    conn.commit()
    print("Student added successfully")


def view_student(cursor):
    rows = cursor.execute("SELECT StudentID, Name, GradeLevel FROM Students ORDER BY StudentID").fetchall()
    print("StudentID | Name | Grade")
    for sid, name, grade in rows:
        print(f"{sid} | {name} | Gr {grade}")


def delete_student(cursor, conn):
    sid = input("Enter Student ID to delete: ").strip()
    cursor.execute("DELETE FROM Students WHERE StudentID=?", (sid,))
    conn.commit()
    print("Student deleted successfully")

def add_teacher(cursor, conn):
    tid = int(input("Enter Teacher ID: ").strip())
    name = input("Enter Teacher Name: ").strip()

    cursor.execute(
        "INSERT INTO Teacher (TeacherID, TeacherName) VALUES (?, ?)",
        (tid, name)
    )
    conn.commit()
    print("Teacher added successfully.")

def view_teacher(cursor):
    rows = cursor.execute(
        "SELECT TeacherID, TeacherName FROM Teacher ORDER BY TeacherID"
    ).fetchall()

    print("TeacherID | TeacherName")
    for tid, name in rows:
        print(f"{tid} | {name}")

def delete_teacher(cursor, conn):
    tid = int(input("Enter Teacher ID to delete: ").strip())

    cursor.execute(
        "DELETE FROM Teacher WHERE TeacherID = ?",
        (tid,)
    )
    conn.commit()
    print("Teacher deleted successfully.")

def add_course(cursor, conn):
    cid = int(input("Enter Course ID: ").strip())
    cname = input("Enter Course Name: ").strip()
    clevel = input("Enter Course Level (SL/HL/Core): ").strip()
    tid = int(input("Enter Teacher ID: ").strip())

    cursor.execute(
        "INSERT INTO Courses (CourseID, CourseName, CourseLevel, TeacherID) VALUES (?,?,?,?)",
        (cid, cname, clevel, tid)
    )
    conn.commit()
    print("Course added successfully")


def view_course(cursor):
    rows = cursor.execute("""
        SELECT c.CourseID, c.CourseName, c.CourseLevel, COALESCE(t.TeacherName, 'None')
        FROM Courses c
        LEFT JOIN Teacher t ON t.TeacherID = c.TeacherID
        ORDER BY c.CourseID
    """).fetchall()

    print(f"{'CourseID':<8} {'CourseName':<45} {'Level':<6} {'Teacher':<25}")
    print("-" * 90)
    for cid, name, level, teacher in rows:
        print(f"{cid:<8} {name:<45} {level:<6} {teacher:<25}")


def delete_course(cursor, conn):
    print("Course list")
    print("--------------------------------")
    view_course(cursor)
    cid = int(input("Enter Course ID to remove: ").strip())
    cursor.execute("DELETE FROM Courses WHERE CourseID=?", (cid,))
    conn.commit()
    print("Course removed successfully")


def add_enrollment(cursor, conn):
    print("Student list")
    print("--------------------------------")
    view_student(cursor)
    sid = input("Enter Student ID to enroll: ").strip()

    print("Course list")
    print("--------------------------------")
    view_course(cursor)
    cid = int(input("Enter Course ID: ").strip())

    cursor.execute("INSERT INTO Enrollments (StudentID, CourseID) VALUES (?,?)", (sid, cid))
    conn.commit()
    print("Enrollment added successfully")


def view_enrollment(cursor):
    rows = cursor.execute("""
        SELECT s.StudentID, s.Name, c.CourseID, c.CourseName, c.CourseLevel
        FROM Enrollments e
        JOIN Students s ON s.StudentID = e.StudentID
        JOIN Courses c ON c.CourseID = e.CourseID
        ORDER BY s.StudentID, c.CourseID
    """).fetchall()

    print("StudentID | Name | CourseID | CourseName | CourseLevel")
    for r in rows:
        print(f"{r[0]} | {r[1]} | {r[2]} | {r[3]} | {r[4]}")


def add_assessment(cursor, conn):
    print("------ADD ASSESSMENT-----")
    view_course(cursor)

    assessment_name = input("Enter Assessment Name: ").strip()
    due_date = input("Enter Due Date (YYYY-MM-DD): ").strip()
    priority = int(input("Priority (1 = Major, 0 = Minor): ").strip())
    if priority not in (0, 1):
        print("Priority must be 0 or 1")
        return

    targets_raw = input("Target CourseIDs (comma-separated, e.g. 1,2,3): ").strip()
    try:
        target_ids = [int(t.strip()) for t in targets_raw.split(",") if t.strip()]
    except ValueError:
        print("CourseIDs must be numbers.")
        return
    if not target_ids:
        print("You must enter at least one CourseID.")
        return

    # Validate CourseIDs exist
    placeholders = ",".join("?" for _ in target_ids)
    existing = cursor.execute(
        f"SELECT CourseID FROM Courses WHERE CourseID IN ({placeholders})",
        target_ids
    ).fetchall()
    existing_ids = {r[0] for r in existing}
    missing = [cid for cid in target_ids if cid not in existing_ids]
    if missing:
        print(f"Invalid CourseIDs: {missing}")
        return

    audience = input("Audience (SL/HL/Both): ").strip().upper()
    if audience not in ("SL", "HL", "BOTH"):
        print("Audience must be SL, HL, or Both.")
        return
    audience = "Both" if audience == "BOTH" else audience

    # Insert assessment ONCE
    cursor.execute("""
        INSERT INTO Assessments (AssessmentName, DueDate, Priority, Audience)
        VALUES (?, ?, ?, ?)
    """, (assessment_name, due_date, priority, audience))

    assessment_id = cursor.lastrowid

    # Map to courses
    for cid in target_ids:
        cursor.execute("""
            INSERT OR IGNORE INTO AssessmentTargets (AssessmentID, CourseID)
            VALUES (?, ?)
        """, (assessment_id, cid))

    conn.commit()
    print(f"Assessment added (ID={assessment_id}) for courses: {','.join(map(str, target_ids))}")


def view_assessment(cursor):
    rows = cursor.execute("""
        SELECT
            a.AssessmentID,
            a.AssessmentName,
            a.DueDate,
            a.Priority,
            a.Audience,
            a.CreatedAt,
            GROUP_CONCAT(at.CourseID) AS TargetCourseIDs
        FROM Assessments a
        LEFT JOIN AssessmentTargets at ON at.AssessmentID = a.AssessmentID
        GROUP BY a.AssessmentID
        ORDER BY a.DueDate, a.AssessmentID
    """).fetchall()

    print("AssessmentID | Name | DueDate | Priority | Audience | CreatedAt | TargetCourseIDs")
    for r in rows:
        target_courses = r[6] if r[6] else "None"
        print(f"{r[0]} | {r[1]} | {r[2]} | {r[3]} | {r[4]} | {r[5]} | {target_courses}")


def delete_assessment(cursor, conn):
    print("Assessment list")
    print("--------------------------------")
    view_assessment(cursor)
    aid = int(input("Enter Assessment ID to remove: ").strip())
    cursor.execute("DELETE FROM Assessments WHERE AssessmentID=?", (aid,))
    conn.commit()
    print("Assessment removed successfully")


def delete_assessment_all(cursor, conn):
    confirm = input("Type DELETE to remove ALL assessments: ").strip().upper()
    if confirm != "DELETE":
        print("Cancelled.")
        return
    cursor.execute("DELETE FROM Assessments")
    conn.commit()
    print("All assessments removed.")


def detect_assessment_conflicts(cursor):
    # Conflict rule:
    # For each student, count major assessments (Priority=1) in same YearWeek,
    # but ONLY include assessments that apply to that course level:
    # - Audience Both always counts
    # - Audience SL counts only if the targeted course is SL
    # - Audience HL counts only if the targeted course is HL
    sql = """
    WITH Overloads AS (
        SELECT
            e.StudentID,
            strftime('%Y-%W', a.DueDate) AS YearWeek,
            COUNT(*) AS MajorCount
        FROM Enrollments e
        JOIN AssessmentTargets at ON at.CourseID = e.CourseID
        JOIN Courses c ON c.CourseID = at.CourseID
        JOIN Assessments a ON a.AssessmentID = at.AssessmentID
        WHERE a.Priority = 1
          AND (
                a.Audience = 'Both'
                OR (a.Audience = 'SL' AND c.CourseLevel = 'SL')
                OR (a.Audience = 'HL' AND c.CourseLevel = 'HL')
              )
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
        a.Audience,

        c.CourseID,
        c.CourseName,
        c.CourseLevel,

        t.TeacherName
    FROM Overloads o
    JOIN Students s ON s.StudentID = o.StudentID
    JOIN Enrollments e ON e.StudentID = o.StudentID
    JOIN AssessmentTargets at ON at.CourseID = e.CourseID
    JOIN Courses c ON c.CourseID = at.CourseID
    JOIN Assessments a ON a.AssessmentID = at.AssessmentID
    LEFT JOIN Teacher t ON t.TeacherID = c.TeacherID
    WHERE strftime('%Y-%W', a.DueDate) = o.YearWeek
      AND a.Priority = 1
      AND (
            a.Audience = 'Both'
            OR (a.Audience = 'SL' AND c.CourseLevel = 'SL')
            OR (a.Audience = 'HL' AND c.CourseLevel = 'HL')
          )
    ORDER BY o.YearWeek, s.Name, a.DueDate, c.CourseName, a.AssessmentName;
    """

    rows = cursor.execute(sql).fetchall()
    if not rows:
        print("No assessment conflicts detected.")
        return

    current_key = None
    for r in rows:
        student_id, student_name, year_week, major_count = r[0], r[1], r[2], r[3]
        key = (student_id, year_week)

        if key != current_key:
            if current_key is not None:
                print("-" * 80)
            print("ASSESSMENT CONFLICT")
            print(f"Student: {student_id} | {student_name}")
            print(f"Week: {year_week} | Major assessments: {major_count}")
            print("AssessmentID | Name | DueDate | CreatedAt | Audience | Course | Level | Teacher")
            current_key = key

        assessment_id, assessment_name, due_date, created_at, audience = r[4], r[5], r[6], r[7], r[8]
        course_id, course_name, course_level, teacher_name = r[9], r[10], r[11], r[12]

        print(
            f"{assessment_id} | {assessment_name} | {due_date} | {created_at} | {audience} | "
            f"{course_id}-{course_name} | {course_level} | {teacher_name}"
        )


def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    ensure_schema_and_migrate(cursor, conn)

    while True:
        try:
            print("======================")
            print("press 1  to Add Student")
            print("press 2  to View all students")
            print("press 3  to Delete Student")
            print("press 4  to Add Course")
            print("press 5  to Remove Course")
            print("press 6  to Add enrollment")
            print("press 7  to View all Enrollments")
            print("press 8  to Add Assessment")
            print("press 9  to View Assessment")
            print("press 10 to Delete Assessment")
            print("press 11 to Delete ALL Assessments")
            print("press 12 to view clashes")
            print("press 13 to view courses")
            print("press 0  to exit")

            user = int(input().strip())

            if user == 0:
                break
            elif user == 1:
                add_student(cursor, conn)
            elif user == 2:
                view_student(cursor)
            elif user == 3:
                delete_student(cursor, conn)
            elif user == 4:
                add_course(cursor, conn)
            elif user == 5:
                delete_course(cursor, conn)
            elif user == 6:
                add_enrollment(cursor, conn)
            elif user == 7:
                view_enrollment(cursor)
            elif user == 8:
                add_assessment(cursor, conn)
                detect_assessment_conflicts(cursor)
            elif user == 9:
                view_assessment(cursor)
            elif user == 10:
                delete_assessment(cursor, conn)
            elif user == 11:
                delete_assessment_all(cursor, conn)
            elif user == 12:
                detect_assessment_conflicts(cursor)
            elif user == 13:
                view_course(cursor)

        except sqlite3.Error as e:
            print(e)
        except ValueError:
            print("Invalid input. Enter a number.")

    conn.close()


if __name__ == "__main__":
    main()
