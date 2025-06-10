from .migrate_employees import migrate_employees
from .migrate_students import migrate_students
from .migrate_courses import migrate_courses

def run_full_migration():
    migrate_employees()
    migrate_students()
    migrate_courses()
