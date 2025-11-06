from e_table import init_db, add_employee, get_all_employees

# Ensure DB/table exists
init_db()

# Add example "old" employee (existing staff)
id1 = add_employee(
    name="Karthik",
    email="karthik@example.com",
    role="Devops Engineer",
    joined='Yes'
)

# Add example "new hire"
id2 = add_employee(
    name="Saketh E",
    email="srsaketh1901@gmail.com",
    role="Data Scientist"
)


print(f"Inserted IDs: {id1}, {id2}\n")

employees = get_all_employees()
for e in employees:
    print(f"ID: {e['id']}, Name: {e['name']}, Email: {e['email']}, Role: {e['role']}, "
          f"Joined: {e['joined']}")