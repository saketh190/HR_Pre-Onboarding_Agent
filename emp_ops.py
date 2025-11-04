from e_table import init_db, get_all_employees

if __name__ == "__main__":
    # ensure table exists
    init_db()

    employees = get_all_employees()
    if not employees:
        print("No employees found.")
    else:
        for e in employees:
            print(f"ID: {e['id']}, Email: {e['email']}, Name: {e['name']}, Role: {e['role']}, Joined: {e['joined']}")