import tkinter as tk
from tkinter import ttk, messagebox
from BackEnd import *


# -----------------------------
# Helpers
# -----------------------------

def is_header_junk(value):
    if value is None:
        return False
    v = str(value).strip()
    return v in ("TeacherID", "TeacherName", "CourseID", "CourseName", "CourseLevel",
                 "StudentID", "Name", "GradeLevel")

def labeled_entry(parent, label_text, default_text=""):
    row = tk.Frame(parent)
    row.pack(fill="x", pady=3)
    tk.Label(row, text=label_text, width=18, anchor="w").pack(side="left")
    entry = tk.Entry(row)
    entry.pack(side="left", fill="x", expand=True)
    if default_text:
        entry.insert(0, default_text)
    return entry

def labeled_combo(parent, label_text, values=None, state="readonly"):
    row = tk.Frame(parent)
    row.pack(fill="x", pady=3)
    tk.Label(row, text=label_text, width=18, anchor="w").pack(side="left")
    combo = ttk.Combobox(row, values=(values or []), state=state)
    combo.pack(side="left", fill="x", expand=True)
    return combo

def make_scrollable_tree(parent, columns, headings=None):
    wrapper = tk.Frame(parent)
    wrapper.pack(fill="both", expand=True, padx=20, pady=10)

    yscroll = ttk.Scrollbar(wrapper, orient="vertical")
    yscroll.pack(side="right", fill="y")

    tree = ttk.Treeview(wrapper, columns=columns, show="headings", yscrollcommand=yscroll.set)
    yscroll.config(command=tree.yview)
    tree.pack(side="left", fill="both", expand=True)

    if headings is None:
        headings = columns
    for col, head in zip(columns, headings):
        tree.heading(col, text=head)
        tree.column(col, anchor="w")

    return tree


# -----------------------------
# Base Page Layout (content + fixed bottom bar)
# -----------------------------

class PageBase(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.conn = controller.conn

        # Two rows: content expands, bottom bar fixed
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)
        self.grid_columnconfigure(0, weight=1)

        self.content = tk.Frame(self)
        self.content.grid(row=0, column=0, sticky="nsew")

        self.bottom_bar = tk.Frame(self)
        self.bottom_bar.grid(row=1, column=0, sticky="ew", padx=12, pady=10)

        # left zone for page actions (optional)
        self.bottom_left = tk.Frame(self.bottom_bar)
        self.bottom_left.pack(side="left", fill="x", expand=True)

        # always visible return button
        tk.Button(
            self.bottom_bar,
            text="Return to Home",
            command=lambda: controller.show_frame(HomePage)
        ).pack(side="right")

    def add_bottom_left_button(self, text, command):
        tk.Button(self.bottom_left, text=text, command=command).pack(side="left", padx=6)


# -----------------------------
# App
# -----------------------------

class SchoolApp(tk.Tk):
    def __init__(self, conn):
        super().__init__()
        self.conn = conn

        self.title("School Assessment Manager")
        self.geometry("1100x650")

        container = tk.Frame(self)
        container.pack(fill="both", expand=True)

        # IMPORTANT: container must be grid-configured
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        for F in (
            HomePage,
            TeacherPage,
            CoursePage,
            StudentPage,
            EnrollmentPage,
            AssessmentPage,
            ConflictPage,
            ReportPage,
        ):
            frame = F(container, self)
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame(HomePage)

    def show_frame(self, page):
        frame = self.frames[page]
        if hasattr(frame, "refresh"):
            frame.refresh()
        frame.tkraise()


# -----------------------------
# Home Page
# -----------------------------

class HomePage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)

        tk.Label(self, text="School System", font=("Arial", 22)).pack(pady=30)

        pages = [
            ("Teachers", TeacherPage),
            ("Courses", CoursePage),
            ("Students", StudentPage),
            ("Enrollments", EnrollmentPage),
            ("Assessments", AssessmentPage),
            ("Conflicts", ConflictPage),
            ("Reports", ReportPage),
        ]

        for text, page in pages:
            tk.Button(
                self,
                text=text,
                width=25,
                command=lambda p=page: controller.show_frame(p)
            ).pack(pady=8)


# -----------------------------
# Teachers
# -----------------------------

class TeacherPage(PageBase):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)

        tk.Label(self.content, text="Teachers", font=("Arial", 18)).pack(pady=10)

        form = tk.Frame(self.content)
        form.pack(fill="x", padx=20)

        self.name_entry = labeled_entry(form, "Teacher Name:")

        tk.Button(self.content, text="Add Teacher", command=self.add_teacher).pack(pady=6)
        tk.Button(self.content, text="Delete Selected", command=self.delete_teacher).pack(pady=5)

        self.tree = make_scrollable_tree(self.content, columns=("ID", "Name"), headings=("ID", "Name"))

    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        for t in get_all_teachers(self.conn):
            if is_header_junk(t["TeacherName"]) or is_header_junk(t["TeacherID"]):
                continue
            self.tree.insert("", "end", values=(t["TeacherID"], t["TeacherName"]))

    def add_teacher(self):
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showerror("Error", "Teacher name required")
            return
        try:
            add_teacher(self.conn, name)
            self.name_entry.delete(0, tk.END)
            self.refresh()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def delete_teacher(self):
        sel = self.tree.selection()
        if not sel:
            return
        teacher_id = self.tree.item(sel[0])["values"][0]
        delete_teacher(self.conn, teacher_id)
        self.refresh()


# -----------------------------
# Courses
# -----------------------------

class CoursePage(PageBase):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        self.teacher_map = {}

        tk.Label(self.content, text="Courses", font=("Arial", 18)).pack(pady=10)

        form = tk.Frame(self.content)
        form.pack(fill="x", padx=20)

        self.name_entry = labeled_entry(form, "Course Name:")
        self.level_combo = labeled_combo(form, "Level:", values=["SL", "HL", "Core"])
        self.teacher_combo = labeled_combo(form, "Teacher:", values=[])

        tk.Button(self.content, text="Add Course", command=self.add_course).pack(pady=6)
        tk.Button(self.content, text="Delete Selected", command=self.delete_course).pack(pady=5)

        self.tree = make_scrollable_tree(
            self.content,
            columns=("ID", "Name", "Level", "Teacher"),
            headings=("ID", "Name", "Level", "Teacher")
        )

    def refresh(self):
        teachers = [t for t in get_all_teachers(self.conn)
                    if not is_header_junk(t["TeacherName"]) and not is_header_junk(t["TeacherID"])]

        self.teacher_map = {t["TeacherName"]: t["TeacherID"] for t in teachers}
        self.teacher_combo["values"] = list(self.teacher_map.keys())
        if self.teacher_combo["values"]:
            self.teacher_combo.current(0)

        self.tree.delete(*self.tree.get_children())
        for c in get_all_courses(self.conn):
            if is_header_junk(c["CourseName"]) or is_header_junk(c["CourseID"]):
                continue
            self.tree.insert("", "end", values=(
                c["CourseID"], c["CourseName"], c["CourseLevel"], c["TeacherName"]
            ))

    def add_course(self):
        name = self.name_entry.get().strip()
        level = self.level_combo.get()
        teacher_name = self.teacher_combo.get()

        if not name or not level or not teacher_name:
            messagebox.showerror("Error", "All fields required")
            return

        try:
            add_course(self.conn, name, level, self.teacher_map[teacher_name])
            self.refresh()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def delete_course(self):
        sel = self.tree.selection()
        if not sel:
            return
        course_id = self.tree.item(sel[0])["values"][0]
        delete_course(self.conn, course_id)
        self.refresh()


# -----------------------------
# Students
# -----------------------------

class StudentPage(PageBase):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)

        tk.Label(self.content, text="Students", font=("Arial", 18)).pack(pady=10)

        form = tk.Frame(self.content)
        form.pack(fill="x", padx=20)

        self.id_entry = labeled_entry(form, "Student ID:")
        self.name_entry = labeled_entry(form, "Name:")
        self.grade_entry = labeled_entry(form, "Grade Level:")

        tk.Button(self.content, text="Add Student", command=self.add_student).pack(pady=6)
        tk.Button(self.content, text="Delete Selected", command=self.delete_student).pack(pady=5)

        self.tree = make_scrollable_tree(
            self.content,
            columns=("ID", "Name", "Grade"),
            headings=("StudentID", "Name", "Grade")
        )

    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        for s in get_all_students(self.conn):
            if is_header_junk(s["StudentID"]) or is_header_junk(s["Name"]):
                continue
            self.tree.insert("", "end", values=(s["StudentID"], s["Name"], s["GradeLevel"]))

    def add_student(self):
        sid = self.id_entry.get().strip()
        name = self.name_entry.get().strip()
        grade = self.grade_entry.get().strip()

        if not sid or not name or not grade.isdigit():
            messagebox.showerror("Error", "Invalid input. Grade must be a number.")
            return

        try:
            add_student(self.conn, sid, name, int(grade))
            self.id_entry.delete(0, tk.END)
            self.name_entry.delete(0, tk.END)
            self.grade_entry.delete(0, tk.END)
            self.refresh()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def delete_student(self):
        sel = self.tree.selection()
        if not sel:
            return
        sid = self.tree.item(sel[0])["values"][0]
        delete_student(self.conn, sid)
        self.refresh()


# -----------------------------
# Enrollments
# -----------------------------

class EnrollmentPage(PageBase):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        self.student_map = {}
        self.course_ids = []

        tk.Label(self.content, text="Enrollments", font=("Arial", 18)).pack(pady=10)

        form = tk.Frame(self.content)
        form.pack(fill="x", padx=20)

        self.student_combo = labeled_combo(form, "Student:", values=[])

        tk.Label(self.content, text="Select Courses").pack(pady=(8, 0))
        self.course_listbox = tk.Listbox(self.content, selectmode="multiple", height=8)
        self.course_listbox.pack(pady=4)

        tk.Button(self.content, text="Enroll Selected Courses", command=self.enroll).pack(pady=6)

        self.tree = make_scrollable_tree(
            self.content,
            columns=("StudentID", "Course", "Level"),
            headings=("StudentID", "Course", "Level")
        )

    def refresh(self):
        students = [s for s in get_all_students(self.conn) if not is_header_junk(s["StudentID"])]
        self.student_map = {f"{s['StudentID']} - {s['Name']}": s["StudentID"] for s in students}
        self.student_combo["values"] = list(self.student_map.keys())
        if self.student_combo["values"]:
            self.student_combo.current(0)

        courses = [c for c in get_all_courses(self.conn) if not is_header_junk(c["CourseName"])]
        self.course_ids = []
        self.course_listbox.delete(0, tk.END)
        for c in courses:
            self.course_listbox.insert(tk.END, f"{c['CourseName']} ({c['CourseLevel']})")
            self.course_ids.append(c["CourseID"])

        self.tree.delete(*self.tree.get_children())
        for s in students:
            sc = get_student_courses(self.conn, s["StudentID"])
            for c in sc:
                self.tree.insert("", "end", values=(s["StudentID"], c["CourseName"], c["CourseLevel"]))

    def enroll(self):
        student_display = self.student_combo.get()
        if not student_display:
            messagebox.showerror("Error", "Select a student")
            return

        selected = self.course_listbox.curselection()
        if not selected:
            messagebox.showerror("Error", "Select at least one course")
            return

        student_id = self.student_map[student_display]

        for i in selected:
            try:
                enroll_student(self.conn, student_id, self.course_ids[i])
            except Exception as e:
                messagebox.showerror("Error", str(e))
                return

        self.refresh()


# -----------------------------
# Assessments (with suggestion feature)
# -----------------------------

class AssessmentPage(PageBase):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        self.course_ids = []
        self.course_display = []

        tk.Label(self.content, text="Assessments", font=("Arial", 18)).pack(pady=10)

        form = tk.Frame(self.content)
        form.pack(fill="x", padx=20)

        self.name_entry = labeled_entry(form, "Assessment Name:")
        self.date_entry = labeled_entry(form, "Due Date:", default_text="YYYY-MM-DD")

        self.priority_combo = labeled_combo(form, "Priority (0/1):", values=["0", "1"])
        self.audience_combo = labeled_combo(form, "Audience:", values=["SL", "HL", "Both"])

        tk.Label(self.content, text="Target Courses").pack(pady=(8, 0))
        self.course_listbox = tk.Listbox(self.content, selectmode="multiple", height=8)
        self.course_listbox.pack(pady=4)

        tk.Button(self.content, text="Add Assessment", command=self.add_assessment_gui).pack(pady=6)
        tk.Button(self.content, text="Delete Selected", command=self.delete_assessment_gui).pack(pady=5)

        self.tree = make_scrollable_tree(
            self.content,
            columns=("ID", "Name", "Date", "Priority", "Audience"),
            headings=("ID", "Name", "DueDate", "Priority", "Audience")
        )

    def refresh(self):
        courses = [c for c in get_all_courses(self.conn) if not is_header_junk(c["CourseName"])]
        self.course_ids = []
        self.course_display = []
        self.course_listbox.delete(0, tk.END)
        for c in courses:
            disp = f"{c['CourseName']} ({c['CourseLevel']})"
            self.course_listbox.insert(tk.END, disp)
            self.course_ids.append(c["CourseID"])
            self.course_display.append(disp)

        self.tree.delete(*self.tree.get_children())
        for a in get_all_assessments(self.conn):
            self.tree.insert("", "end", values=(
                a["AssessmentID"], a["AssessmentName"], a["DueDate"], a["Priority"], a["Audience"]
            ))

    def add_assessment_gui(self):
        name = self.name_entry.get().strip()
        date = self.date_entry.get().strip()
        priority = self.priority_combo.get()
        audience = self.audience_combo.get()
        selected = self.course_listbox.curselection()

        if not name or not date or priority == "" or audience == "":
            messagebox.showerror("Error", "All fields required")
            return
        if not selected:
            messagebox.showerror("Error", "Select at least one target course")
            return

        selected_ids = [self.course_ids[i] for i in selected]

        # Add assessment
        try:
            add_assessment(self.conn, name, date, int(priority), audience, selected_ids)
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return

        # If major, check conflicts and suggest alternative date for any affected student(s)
        if int(priority) == 1:
            conflicts = detect_assessment_conflicts(self.conn)
            if conflicts:
                # show one suggestion (strong enough for IA; you can loop all later)
                student_id = conflicts[0]["StudentID"]
                try:
                    suggestion = suggest_alternative_date(self.conn, student_id, date)
                except Exception:
                    suggestion = None

                if suggestion:
                    messagebox.showwarning(
                        "Conflict Detected",
                        f"A student is overloaded (>=4 major assessments in a week).\n"
                        f"Suggested alternative date: {suggestion}\n\n"
                        f"Current date: {date}"
                    )

        self.refresh()

    def delete_assessment_gui(self):
        sel = self.tree.selection()
        if not sel:
            return
        assessment_id = self.tree.item(sel[0])["values"][0]
        delete_assessment(self.conn, assessment_id)
        self.refresh()


# -----------------------------
# Conflicts
# -----------------------------

class ConflictPage(PageBase):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)

        tk.Label(self.content, text="Assessment Conflicts", font=("Arial", 18)).pack(pady=10)

        self.tree = make_scrollable_tree(
            self.content,
            columns=("StudentID", "Name", "Week", "MajorCount"),
            headings=("StudentID", "Name", "Week", "MajorCount")
        )
        self.tree.bind("<Double-1>", self.show_details)

        self.add_bottom_left_button("Refresh", self.load_conflicts)

    def refresh(self):
        self.load_conflicts()

    def load_conflicts(self):
        self.tree.delete(*self.tree.get_children())
        for c in detect_assessment_conflicts(self.conn):
            self.tree.insert("", "end", values=(c["StudentID"], c["Name"], c["Week"], c["MajorCount"]))

    def show_details(self, event):
        sel = self.tree.selection()
        if not sel:
            return
        student_id, name, week, _ = self.tree.item(sel[0])["values"]
        details = get_student_conflict_details(self.conn, student_id, week)

        popup = tk.Toplevel(self)
        popup.title(f"Conflict Details - {student_id}")
        popup.geometry("900x400")

        tree = make_scrollable_tree(
            popup,
            columns=("Assessment", "Course", "Level", "DueDate", "Teacher"),
            headings=("Assessment", "Course", "Level", "DueDate", "Teacher")
        )

        for d in details:
            tree.insert("", "end", values=(
                d["AssessmentName"], d["CourseName"], d["CourseLevel"], d["DueDate"], d["TeacherName"]
            ))


# -----------------------------
# Reports (Generate Report Feature)
# -----------------------------

class ReportPage(PageBase):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        self.student_map = {}

        tk.Label(self.content, text="Reports", font=("Arial", 18)).pack(pady=10)

        form = tk.Frame(self.content)
        form.pack(fill="x", padx=20)

        self.student_combo = labeled_combo(form, "Student:", values=[])

        tk.Button(self.content, text="Generate Report", command=self.generate_report).pack(pady=8)

        self.output = tk.Text(self.content, wrap="word")
        self.output.pack(fill="both", expand=True, padx=20, pady=10)

    def refresh(self):
        students = [s for s in get_all_students(self.conn) if not is_header_junk(s["StudentID"])]
        self.student_map = {f"{s['StudentID']} - {s['Name']}": s["StudentID"] for s in students}
        self.student_combo["values"] = list(self.student_map.keys())
        if self.student_combo["values"]:
            self.student_combo.current(0)
        self.output.delete("1.0", "end")

    def generate_report(self):
        display = self.student_combo.get()
        if not display:
            messagebox.showerror("Error", "Select a student")
            return

        student_id = self.student_map[display]

        report = generate_student_report(self.conn, student_id)
        if not report:
            messagebox.showerror("Error", "No report data found for this student.")
            return

        self.output.delete("1.0", "end")

        self.output.insert("end", f"StudentID: {report['StudentID']}\n")
        self.output.insert("end", f"Name: {report['Name']}\n")
        self.output.insert("end", f"Total Assessments: {report['TotalAssessments']}\n")
        self.output.insert("end", f"Major Assessments: {report['TotalMajor']}\n")
        self.output.insert("end", f"Overloaded Weeks: {report['OverloadedWeeks']}\n\n")

        self.output.insert("end", "Details:\n")
        self.output.insert("end", "-" * 80 + "\n")

        for d in report["Details"]:
            self.output.insert(
                "end",
                f"{d['DueDate']} | Week {d['Week']} | "
                f"{d['Assessment']} | {d['Course']} ({d['Level']}) | "
                f"Teacher: {d['Teacher']} | Priority: {d['Priority']}\n"
            )