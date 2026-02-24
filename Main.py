import os
from BackEnd import get_connection, ensure_schema
from GUI import SchoolApp

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(base_dir, "csiaa.db") 
    conn = get_connection(db_path)
    ensure_schema(conn)

    app = SchoolApp(conn)
    app.mainloop()

if __name__ == "__main__":
    main()