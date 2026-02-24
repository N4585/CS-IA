from BackEnd import get_connection, ensure_schema
from GUI import SchoolApp

def main():
    conn = get_connection("csiaa.db")
    ensure_schema(conn)
    app = SchoolApp(conn)
    app.mainloop()

if __name__ == "__main__":
    from BackEnd import get_connection, ensure_schema
    conn = get_connection()
    ensure_schema(conn)
    app = SchoolApp(conn)
    app.mainloop()