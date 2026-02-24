import tkinter as tk
from tkinter import ttk, messagebox
from BackEnd import *


class NavMixin:
    def add_bottom_nav(self, controller, extra_widgets=None):
        bar = tk.Frame(self)
        bar.pack(side="bottom", fill="x", padx=12, pady=10)

        if extra_widgets:
            for w in extra_widgets:
                w.pack(in_=bar, side="left", padx=6)

        tk.Button(
            bar,
            text="Return to Home",
            command=lambda: controller.show_frame(HomePage)
        ).pack(side="right", padx=6)

        return bar


class SchoolApp(tk.Tk):
    def __init__(self, conn):
        super().__init__()
        self.conn = conn

        self.title("School Assessment Manager")
        self.geometry("1100x650")

        container = tk.Frame(self)
        container.pack(fill="both", expand=True)

        self.frames = {}
        for F in (HomePage, TeacherPage, CoursePage, StudentPage,
                  EnrollmentPage, AssessmentPage, ConflictPage):
            frame = F(container, self)
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame(HomePage)

    def show_frame(self, page):
        frame = self.frames[page]
        if hasattr(frame, "refresh"):
            frame.refresh()
        frame.tkraise()


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
        ]

        for text, page in pages:
            tk.Button(self, text=text, width=20,
                      command=lambda p=page: controller.show_frame(p)
                      ).pack(pady=10)


class TeacherPage(tk.Frame, NavMixin):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.conn = controller.conn

        tk.Label(self, text="Teachers", font=("Arial", 18)).pack(pady=10)

        self.name_entry = tk.Entry(self)
        self.name_entry.pack(pady=5)

        tk.Button(self, text="Add Teacher", command=self.add_teacher).pack(pady=5)

        self.tree = ttk.Treeview(self, columns=("ID", "Name"), show="headings")
        self.tree.heading("ID", text="ID")
        self.tree.heading("Name", text="Name")
        self.tree.pack(fill="both", expand=True)

        tk.Button(self, text="Delete Selected", command=self.delete_teacher).pack(pady=5)

        self.add_bottom_nav(controller)

    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        for t in get_all_teachers(self.conn):
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


class CoursePage(tk.Frame, NavMixin):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.conn = controller.conn
        self.teacher_map = {}

        tk.Label(self, text="Courses", font=("Arial", 18)).pack(pady=10)

        self.name_entry = tk.Entry(self)
        self.name_entry.pack(pady=2)

        self.level_combo = ttk.Combobox(self, values=["SL", "HL", "Core"], state="readonly")
        self.level_combo.pack(pady=2)

        self.teacher_combo = ttk.Combobox(self, state="readonly")
        self.teacher_combo.pack(pady=2)

        tk.Button(self, text="Add Course", command=self.add_course).pack(pady=6)

        self.tree = ttk.Treeview(self, columns=("ID", "Name", "Level", "Teacher"), show="headings")
        for col in ("ID", "Name", "Level", "Teacher"):
            self.tree.heading(col, text=col)
        self.tree.pack(fill="both", expand=True)

        tk.Button(self, text="Delete Selected", command=self.delete_course).pack(pady=5)

        self.add_bottom_nav(controller)

    def refresh(self):
        teachers = get_all_teachers(self.conn)
        self.teacher_map = {t["TeacherName"]: t["TeacherID"] for t in teachers}
        self.teacher_combo["values"] = list(self.teacher_map.keys())

        self.tree.delete(*self.tree.get_children())
        for c in get_all_courses(self.conn):
            self.tree.insert("", "end", values=(c["CourseID"], c["CourseName"], c["CourseLevel"], c["TeacherName"]))

    def add_course(self):
        name = self.name_entry.get().strip()
        level = self.level_combo.get()
        teacher_name = self.teacher_combo.get()

        if not name or not level or not teacher_name:
            messagebox.showerror("Error", "All fields required")
            return

        add_course(self.conn, name, level, self.teacher_map[teacher_name])
        self.refresh()

    def delete_course(self):
        sel = self.tree.selection()
        if not sel:
            return
        course_id = self.tree.item(sel[0])["values"][0]
        delete_course(self.conn, course_id)
        self.refresh()


class StudentPage(tk.Frame, NavMixin):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.conn = controller.conn

        tk.Label(self, text="Students", font=("Arial", 18)).pack(pady=10)

        self.id_entry = tk.Entry(self)
        self.id_entry.pack(pady=2)

        self.name_entry = tk.Entry(self)
        self.name_entry.pack(pady=2)

        self.grade_entry = tk.Entry(self)
        self.grade_entry.pack(pady=2)

        tk.Button(self, text="Add Student", command=self.add_student).pack(pady=6)

        self.tree = ttk.Treeview(self, columns=("ID", "Name", "Grade"), show="headings")
        for col in ("ID", "Name", "Grade"):
            self.tree.heading(col, text=col)
        self.tree.pack(fill="both", expand=True)

        tk.Button(self, text="Delete Selected", command=self.delete_student).pack(pady=5)

        self.add_bottom_nav(controller)

    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        for s in get_all_students(self.conn):
            self.tree.insert("", "end", values=(s["StudentID"], s["Name"], s["GradeLevel"]))

    def add_student(self):
        sid = self.id_entry.get().strip()
        name = self.name_entry.get().strip()
        grade = self.grade_entry.get().strip()

        if not sid or not name or not grade.isdigit():
            messagebox.showerror("Error", "Invalid input")
            return

        add_student(self.conn, sid, name, int(grade))
        self.refresh()

    def delete_student(self):
        sel = self.tree.selection()
        if not sel:
            return
        sid = self.tree.item(sel[0])["values"][0]
        delete_student(self.conn, sid)
        self.refresh()


class EnrollmentPage(tk.Frame, NavMixin):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.conn = controller.conn
        self.student_map = {}
        self.course_ids = []

        tk.Label(self, text="Enrollments", font=("Arial", 18)).pack(pady=10)

        tk.Label(self, text="Student").pack()
        self.student_combo = ttk.Combobox(self, state="readonly")
        self.student_combo.pack(pady=4)

        tk.Label(self, text="Select Courses").pack()
        self.course_listbox = tk.Listbox(self, selectmode="multiple", height=8)
        self.course_listbox.pack(pady=4)

        tk.Button(self, text="Enroll", command=self.enroll).pack(pady=6)

        self.tree = ttk.Treeview(self, columns=("StudentID", "Course", "Level"), show="headings")
        for col in ("StudentID", "Course", "Level"):
            self.tree.heading(col, text=col)
        self.tree.pack(fill="both", expand=True)

        self.add_bottom_nav(controller)

    def refresh(self):
        students = get_all_students(self.conn)
        self.student_map = {f"{s['StudentID']} - {s['Name']}": s["StudentID"] for s in students}
        self.student_combo["values"] = list(self.student_map.keys())
        if self.student_combo["values"]:
            self.student_combo.current(0)

        self.course_listbox.delete(0, tk.END)
        courses = get_all_courses(self.conn)
        self.course_ids = []
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
            messagebox.showerror("Error", "Select student")
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


class AssessmentPage(tk.Frame, NavMixin):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.conn = controller.conn
        self.course_ids = []

        tk.Label(self, text="Assessments", font=("Arial", 18)).pack(pady=10)

        self.name_entry = tk.Entry(self)
        self.name_entry.pack(pady=2)

        self.date_entry = tk.Entry(self)
        self.date_entry.insert(0, "YYYY-MM-DD")
        self.date_entry.pack(pady=2)

        self.priority_combo = ttk.Combobox(self, values=["0", "1"], state="readonly")
        self.priority_combo.pack(pady=2)

        self.audience_combo = ttk.Combobox(self, values=["SL", "HL", "Both"], state="readonly")
        self.audience_combo.pack(pady=2)

        tk.Label(self, text="Target Courses").pack()
        self.course_listbox = tk.Listbox(self, selectmode="multiple", height=8)
        self.course_listbox.pack(pady=4)

        tk.Button(self, text="Add Assessment", command=self.add_assessment).pack(pady=6)

        self.tree = ttk.Treeview(self, columns=("ID", "Name", "Date", "Priority", "Audience"), show="headings")
        for col in ("ID", "Name", "Date", "Priority", "Audience"):
            self.tree.heading(col, text=col)
        self.tree.pack(fill="both", expand=True)

        tk.Button(self, text="Delete Selected", command=self.delete_assessment).pack(pady=5)

        self.add_bottom_nav(controller)

    def refresh(self):
        self.course_listbox.delete(0, tk.END)
        courses = get_all_courses(self.conn)
        self.course_ids = []
        for c in courses:
            self.course_listbox.insert(tk.END, f"{c['CourseName']} ({c['CourseLevel']})")
            self.course_ids.append(c["CourseID"])

        self.tree.delete(*self.tree.get_children())
        for a in get_all_assessments(self.conn):
            self.tree.insert("", "end", values=(
                a["AssessmentID"], a["AssessmentName"], a["DueDate"], a["Priority"], a["Audience"]
            ))

    def add_assessment(self):
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

        try:
            add_assessment(self.conn, name, date, int(priority), audience, selected_ids)
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return

        self.refresh()

    def delete_assessment(self):
        sel = self.tree.selection()
        if not sel:
            return
        assessment_id = self.tree.item(sel[0])["values"][0]
        delete_assessment(self.conn, assessment_id)
        self.refresh()


class ConflictPage(tk.Frame, NavMixin):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.conn = controller.conn

        tk.Label(self, text="Assessment Conflicts", font=("Arial", 18)).pack(pady=10)

        self.tree = ttk.Treeview(self, columns=("StudentID", "Name", "Week", "MajorCount"), show="headings")
        for col in ("StudentID", "Name", "Week", "MajorCount"):
            self.tree.heading(col, text=col)
        self.tree.pack(fill="both", expand=True)

        self.tree.bind("<Double-1>", self.show_details)

        self.add_bottom_nav(controller, extra_widgets=[
            tk.Button(self, text="Refresh", command=self.load_conflicts)
        ])

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

        tree = ttk.Treeview(popup, columns=("Assessment", "Course", "Level", "DueDate", "Teacher"), show="headings")
        for col in ("Assessment", "Course", "Level", "DueDate", "Teacher"):
            tree.heading(col, text=col)
        tree.pack(fill="both", expand=True)

        for d in details:
            tree.insert("", "end", values=(
                d["AssessmentName"], d["CourseName"], d["CourseLevel"], d["DueDate"], d["TeacherName"]
            ))