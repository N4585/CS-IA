from BackEnd import get_connection, ensure_schema
from gui import run_app

def main():
    conn = get_connection()
    ensure_schema(conn)
    run_app(conn)

if __name__ == "__main__":
    main()