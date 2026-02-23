import tkinter as tk
from tkinter import ttk, messagebox
from BackEnd import *


class SchoolApp(tk.Tk):
    def __init__(self, conn):
        super().__init__()
        self.conn = conn

        self.title("School Assessment Manager")
        self.geometry("1100x650")

        container = tk.Frame(self)
        container.pack(fill="both", expand=True)

        self.frames = {}

        for F in (HomePage, TeacherPage, CoursePage,
                  StudentPage, EnrollmentPage, AssessmentPage, ConflictPage):
            frame = F(container, self)
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame(HomePage)

    def show_frame(self, page):
        frame = self.frames[page]
        frame.tkraise()


# =========================
# HOME PAGE
# =========================

class HomePage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)

        tk.Label(self, text="School System", font=("Arial", 22)).pack(pady=30)

        pages = [
            ("Teachers", TeacherPage),
            ("Courses", CoursePage),
            ("Students", StudentPage),
            ("Assessments", AssessmentPage),
            ("Conflicts", ConflictPage)
        ]

        for text, page in pages:
            tk.Button(self, text=text,
                      width=20,
                      command=lambda p=page: controller.show_frame(p)
                      ).pack(pady=10)


# =========================
# TEACHER PAGE
# =========================

class TeacherPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.conn = controller.conn

        tk.Label(self, text="Teachers", font=("Arial", 18)).pack(pady=10)

        self.name_entry = tk.Entry(self)
        self.name_entry.pack(pady=5)

        tk.Button(self, text="Add Teacher",
                  command=self.add_teacher).pack(pady=5)

        self.tree = ttk.Treeview(self, columns=("ID", "Name"), show="headings")
        self.tree.heading("ID", text="ID")
        self.tree.heading("Name", text="Name")
        self.tree.pack(fill="both", expand=True)

        tk.Button(self, text="Delete Selected",
                  command=self.delete_teacher).pack(pady=5)

        tk.Button(self, text="Back",
                  command=lambda: controller.show_frame(HomePage)).pack()

        self.refresh()

    def refresh(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        for t in get_all_teachers(self.conn):
            self.tree.insert("", "end",
                             values=(t["TeacherID"], t["TeacherName"]))

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
        selected = self.tree.selection()
        if not selected:
            return
        teacher_id = self.tree.item(selected[0])["values"][0]
        delete_teacher(self.conn, teacher_id)
        self.refresh()


# =========================
# COURSE PAGE
# =========================

class CoursePage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.conn = controller.conn

        tk.Label(self, text="Courses", font=("Arial", 18)).pack(pady=10)

        self.name_entry = tk.Entry(self)
        self.name_entry.pack()

        self.level_combo = ttk.Combobox(self,
                                        values=["SL", "HL", "Core"])
        self.level_combo.pack()

        self.teacher_combo = ttk.Combobox(self)
        self.teacher_combo.pack()

        tk.Button(self, text="Add Course",
                  command=self.add_course).pack(pady=5)

        self.tree = ttk.Treeview(self,
                                 columns=("ID", "Name", "Level", "Teacher"),
                                 show="headings")
        for col in ("ID", "Name", "Level", "Teacher"):
            self.tree.heading(col, text=col)
        self.tree.pack(fill="both", expand=True)

        tk.Button(self, text="Delete Selected",
                  command=self.delete_course).pack(pady=5)

        tk.Button(self, text="Back",
                  command=lambda: controller.show_frame(HomePage)).pack()

        self.refresh()

    def refresh(self):
        teachers = get_all_teachers(self.conn)
        self.teacher_map = {t["TeacherName"]: t["TeacherID"] for t in teachers}
        self.teacher_combo["values"] = list(self.teacher_map.keys())

        for row in self.tree.get_children():
            self.tree.delete(row)

        for c in get_all_courses(self.conn):
            self.tree.insert("", "end",
                             values=(c["CourseID"],
                                     c["CourseName"],
                                     c["CourseLevel"],
                                     c["TeacherName"]))

    def add_course(self):
        name = self.name_entry.get().strip()
        level = self.level_combo.get()
        teacher = self.teacher_combo.get()

        if not name or not level or not teacher:
            messagebox.showerror("Error", "All fields required")
            return

        add_course(self.conn, name, level,
                   self.teacher_map[teacher])
        self.refresh()

    def delete_course(self):
        selected = self.tree.selection()
        if not selected:
            return
        course_id = self.tree.item(selected[0])["values"][0]
        delete_course(self.conn, course_id)
        self.refresh()


# =========================
# STUDENT PAGE
# =========================

class StudentPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.conn = controller.conn

        tk.Label(self, text="Students", font=("Arial", 18)).pack(pady=10)

        self.id_entry = tk.Entry(self)
        self.id_entry.pack()

        self.name_entry = tk.Entry(self)
        self.name_entry.pack()

        self.grade_entry = tk.Entry(self)
        self.grade_entry.pack()

        tk.Button(self, text="Add Student",
                  command=self.add_student).pack(pady=5)

        self.tree = ttk.Treeview(self,
                                 columns=("ID", "Name", "Grade"),
                                 show="headings")
        for col in ("ID", "Name", "Grade"):
            self.tree.heading(col, text=col)
        self.tree.pack(fill="both", expand=True)

        tk.Button(self, text="Delete Selected",
                  command=self.delete_student).pack(pady=5)

        tk.Button(self, text="Back",
                  command=lambda: controller.show_frame(HomePage)).pack()

        self.refresh()

    def refresh(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        for s in get_all_students(self.conn):
            self.tree.insert("", "end",
                             values=(s["StudentID"],
                                     s["Name"],
                                     s["GradeLevel"]))

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
        selected = self.tree.selection()
        if not selected:
            return
        sid = self.tree.item(selected[0])["values"][0]
        delete_student(self.conn, sid)
        self.refresh()


# =========================
# ASSESSMENT + CONFLICT PAGES
# =========================

class AssessmentPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        tk.Label(self, text="Assessment Page",
                 font=("Arial", 18)).pack(pady=20)
        tk.Button(self, text="Back",
                  command=lambda: controller.show_frame(HomePage)).pack()


class ConflictPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        tk.Label(self, text="Conflict Page",
                 font=("Arial", 18)).pack(pady=20)
        tk.Button(self, text="Back",
                  command=lambda: controller.show_frame(HomePage)).pack()