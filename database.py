# database.py  (PostgreSQL version)
import os
import hashlib
import psycopg2
import psycopg2.extras


# ========== DATABASE CONFIG ==========
# Sab settings environment variables se aati hain (Windows/Linux/hosting sab pe kaam karega).
# Agar env var set nahi hai to neeche wali default value use hogi - LOCAL DEV ke liye
# defaults badal lein ya .env / system env vars set kar dein.


DB_CONFIG = {
    'host': os.environ.get('DB_HOST'),
    'port': os.environ.get('DB_PORT', '5432'),
    'dbname': os.environ.get('DB_NAME'),
    'user': os.environ.get('DB_USER'),
    'password': os.environ.get('DB_PASSWORD'),
}

if not all([DB_CONFIG['host'], DB_CONFIG['dbname'], DB_CONFIG['user'], DB_CONFIG['password']]):
    raise Exception("Database environment variables set nahi hain! .env file check karein.")


def get_connection_string():
    """Backward-compatible helper (kept for reference), asal connection get_db() mein hoti hai."""
    return (
        f"host={DB_CONFIG['host']} port={DB_CONFIG['port']} "
        f"dbname={DB_CONFIG['dbname']} user={DB_CONFIG['user']} "
        f"password={DB_CONFIG['password']}"
    )


def get_db():
    try:
        conn = psycopg2.connect(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            dbname=DB_CONFIG['dbname'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
        )
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        print("Please check:")
        print("1. PostgreSQL server is running")
        print(f"2. Host/Port sahi hai: {DB_CONFIG['host']}:{DB_CONFIG['port']}")
        print(f"3. Database '{DB_CONFIG['dbname']}' exists")
        print("4. psycopg2-binary installed hai (pip install psycopg2-binary)")
        print("5. DB_HOST / DB_PORT / DB_NAME / DB_USER / DB_PASSWORD env vars set hain")
        raise


def fetchall_dict(cursor):
    """Convert psycopg2 rows to list of dictionaries"""
    if cursor.description is None:
        return []
    columns = [column[0] for column in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def fetchone_dict(cursor):
    """Convert single psycopg2 row to dictionary"""
    row = cursor.fetchone()
    if row:
        columns = [column[0] for column in cursor.description]
        return dict(zip(columns, row))
    return None


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def init_db():
    try:
        conn = get_db()
        cursor = conn.cursor()
        print("Connected to database successfully!")
    except Exception as e:
        print(f"Failed to connect: {e}")
        return

    # PostgreSQL syntax: CREATE TABLE IF NOT EXISTS, SERIAL for autoincrement,
    # BOOLEAN instead of BIT, TIMESTAMP + NOW() instead of DATETIME + GETDATE()
    tables = [
        # Users table
        """
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            school_id INT NULL,
            username VARCHAR(100) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            role VARCHAR(50) NOT NULL,
            full_name VARCHAR(200) NOT NULL,
            email VARCHAR(100),
            phone VARCHAR(20),
            is_active BOOLEAN DEFAULT TRUE,
            created_date TIMESTAMP DEFAULT NOW(),
            updated_date TIMESTAMP NULL
        )
        """,

        # Schools table
        """
        CREATE TABLE IF NOT EXISTS schools (
            id SERIAL PRIMARY KEY,
            name VARCHAR(200) NOT NULL,
            address VARCHAR(500),
            phone VARCHAR(50),
            email VARCHAR(100),
            logo VARCHAR(255),
            latitude DECIMAL(10,8),
            longitude DECIMAL(11,8),
            city VARCHAR(100),
            is_active BOOLEAN DEFAULT TRUE,
            created_date TIMESTAMP DEFAULT NOW()
        )
        """,

        # Classes table
        """
        CREATE TABLE IF NOT EXISTS classes (
            id SERIAL PRIMARY KEY,
            school_id INT NOT NULL REFERENCES schools(id),
            class_name VARCHAR(100) NOT NULL,
            section VARCHAR(50),
            academic_year VARCHAR(20),
            created_date TIMESTAMP DEFAULT NOW()
        )
        """,

        # Teachers table
        """
        CREATE TABLE IF NOT EXISTS teachers (
            id SERIAL PRIMARY KEY,
            user_id INT NOT NULL REFERENCES users(id),
            school_id INT NOT NULL REFERENCES schools(id),
            teacher_code VARCHAR(50) UNIQUE,
            full_name VARCHAR(200) NOT NULL,
            email VARCHAR(100),
            phone VARCHAR(20),
            subject_specialization VARCHAR(200),
            qualification VARCHAR(200),
            joining_date DATE,
            salary DECIMAL(10,2),
            address VARCHAR(500),
            profile_pic VARCHAR(255),
            cnic VARCHAR(20),
            is_active BOOLEAN DEFAULT TRUE,
            created_by INT,
            updated_by INT,
            created_date TIMESTAMP DEFAULT NOW(),
            updated_date TIMESTAMP NULL
        )
        """,

        # Students table
        """
        CREATE TABLE IF NOT EXISTS students (
            id SERIAL PRIMARY KEY,
            user_id INT NOT NULL REFERENCES users(id),
            school_id INT NOT NULL REFERENCES schools(id),
            student_code VARCHAR(50) UNIQUE,
            full_name VARCHAR(200) NOT NULL,
            father_name VARCHAR(200),
            email VARCHAR(100),
            phone VARCHAR(20),
            date_of_birth DATE,
            gender VARCHAR(20),
            class_id INT REFERENCES classes(id),
            joining_date DATE,
            address_line1 VARCHAR(255),
            address_line2 VARCHAR(255),
            city VARCHAR(100),
            state VARCHAR(100),
            postal_code VARCHAR(20),
            medical_details TEXT,
            profile_pic VARCHAR(255),
            is_active BOOLEAN DEFAULT TRUE,
            created_by INT,
            updated_by INT,
            created_date TIMESTAMP DEFAULT NOW(),
            updated_date TIMESTAMP NULL
        )
        """,

        # Subjects table
        """
        CREATE TABLE IF NOT EXISTS subjects (
            id SERIAL PRIMARY KEY,
            school_id INT NOT NULL REFERENCES schools(id),
            class_id INT NOT NULL REFERENCES classes(id),
            subject_name VARCHAR(100) NOT NULL,
            total_marks INT DEFAULT 100,
            passing_marks INT DEFAULT 40,
            created_date TIMESTAMP DEFAULT NOW()
        )
        """,

        # Marks table
        """
        CREATE TABLE IF NOT EXISTS marks (
            id SERIAL PRIMARY KEY,
            student_id INT NOT NULL REFERENCES students(id),
            subject_id INT NOT NULL REFERENCES subjects(id),
            class_id INT NOT NULL REFERENCES classes(id),
            school_id INT NOT NULL,
            teacher_id INT NOT NULL REFERENCES teachers(id),
            obtained_marks DECIMAL(5,2) NOT NULL,
            exam_type VARCHAR(50) DEFAULT 'Annual',
            academic_year VARCHAR(20),
            entered_at TIMESTAMP DEFAULT NOW()
        )
        """,

        # Teacher Classes
        """
        CREATE TABLE IF NOT EXISTS teacher_classes (
            id SERIAL PRIMARY KEY,
            teacher_id INT NOT NULL REFERENCES teachers(id),
            class_id INT NOT NULL REFERENCES classes(id),
            school_id INT NOT NULL,
            is_primary BOOLEAN DEFAULT FALSE,
            created_date TIMESTAMP DEFAULT NOW(),
            UNIQUE (teacher_id, class_id)
        )
        """,

        # Teacher Subjects
        """
        CREATE TABLE IF NOT EXISTS teacher_subjects (
            id SERIAL PRIMARY KEY,
            teacher_id INT NOT NULL REFERENCES teachers(id),
            subject_id INT NOT NULL REFERENCES subjects(id),
            school_id INT NOT NULL,
            created_date TIMESTAMP DEFAULT NOW(),
            UNIQUE (teacher_id, subject_id)
        )
        """,

        # Student Parents
        """
        CREATE TABLE IF NOT EXISTS student_parents (
            id SERIAL PRIMARY KEY,
            student_id INT NOT NULL REFERENCES students(id),
            parent_name VARCHAR(200),
            relation VARCHAR(50),
            occupation VARCHAR(200),
            phone VARCHAR(20),
            email VARCHAR(100),
            created_by INT,
            created_date TIMESTAMP DEFAULT NOW()
        )
        """,

        # Student Siblings
        """
        CREATE TABLE IF NOT EXISTS student_siblings (
            id SERIAL PRIMARY KEY,
            student_id INT NOT NULL REFERENCES students(id),
            sibling_name VARCHAR(200),
            age INT,
            class VARCHAR(100),
            school_name VARCHAR(200),
            sibling_student_id INT REFERENCES students(id),
            created_by INT,
            created_date TIMESTAMP DEFAULT NOW()
        )
        """,

        # Student Attendance
        """
        CREATE TABLE IF NOT EXISTS student_attendance (
            id SERIAL PRIMARY KEY,
            student_id INT NOT NULL REFERENCES students(id),
            class_id INT NOT NULL REFERENCES classes(id),
            school_id INT NOT NULL,
            attendance_date DATE NOT NULL,
            status VARCHAR(20) DEFAULT 'Present',
            remarks VARCHAR(500),
            marked_by INT,
            created_by INT,
            updated_by INT,
            created_date TIMESTAMP DEFAULT NOW(),
            updated_date TIMESTAMP NULL,
            UNIQUE (student_id, attendance_date)
        )
        """,

        # Teacher Attendance
        """
        CREATE TABLE IF NOT EXISTS teacher_attendance (
            id SERIAL PRIMARY KEY,
            teacher_id INT NOT NULL REFERENCES teachers(id),
            school_id INT NOT NULL,
            attendance_date DATE NOT NULL,
            status VARCHAR(20) DEFAULT 'Present',
            remarks VARCHAR(500),
            marked_by INT,
            created_by INT,
            updated_by INT,
            created_date TIMESTAMP DEFAULT NOW(),
            updated_date TIMESTAMP NULL,
            UNIQUE (teacher_id, attendance_date)
        )
        """,

        # Fee Collections
        """
        CREATE TABLE IF NOT EXISTS fee_collections (
            id SERIAL PRIMARY KEY,
            student_id INT NOT NULL REFERENCES students(id),
            school_id INT NOT NULL,
            class_id INT NOT NULL REFERENCES classes(id),
            month VARCHAR(20) NOT NULL,
            year INT NOT NULL,
            amount DECIMAL(10,2) NOT NULL,
            payment_mode VARCHAR(50),
            transaction_reference VARCHAR(100),
            remarks VARCHAR(500),
            receipt_number VARCHAR(50) UNIQUE,
            collected_by INT,
            created_by INT,
            created_date TIMESTAMP DEFAULT NOW()
        )
        """,

        # Notices
        """
        CREATE TABLE IF NOT EXISTS notices (
            id SERIAL PRIMARY KEY,
            school_id INT NOT NULL REFERENCES schools(id),
            title VARCHAR(200) NOT NULL,
            body TEXT,
            image_path VARCHAR(255),
            is_active BOOLEAN DEFAULT TRUE,
            created_by INT,
            created_date TIMESTAMP DEFAULT NOW(),
            updated_by INT,
            updated_date TIMESTAMP NULL
        )
        """,

        # Notice Recipients
        """
        CREATE TABLE IF NOT EXISTS notice_recipients (
            id SERIAL PRIMARY KEY,
            notice_id INT NOT NULL REFERENCES notices(id),
            role VARCHAR(50) NOT NULL
        )
        """,

        # Parent Children
        """
        CREATE TABLE IF NOT EXISTS parent_children (
            id SERIAL PRIMARY KEY,
            parent_user_id INT NOT NULL REFERENCES users(id),
            student_id INT NOT NULL REFERENCES students(id),
            school_id INT NOT NULL,
            created_by INT,
            created_date TIMESTAMP DEFAULT NOW(),
            UNIQUE (parent_user_id, student_id)
        )
        """,

        # Teacher Documents
        """
        CREATE TABLE IF NOT EXISTS teacher_documents (
            id SERIAL PRIMARY KEY,
            teacher_id INT NOT NULL REFERENCES teachers(id),
            document_type VARCHAR(100),
            document_name VARCHAR(200),
            file_path VARCHAR(255),
            created_by INT,
            created_date TIMESTAMP DEFAULT NOW()
        )
        """,

        # Staging Tables for Bulk Upload
        """
        CREATE TABLE IF NOT EXISTS staging_classes (
            id SERIAL PRIMARY KEY,
            school_id INT,
            class_name VARCHAR(100),
            section VARCHAR(50),
            academic_year VARCHAR(20),
            validation_status VARCHAR(20),
            error_message VARCHAR(500),
            uploaded_by INT,
            uploaded_date TIMESTAMP DEFAULT NOW()
        )
        """,

        """
        CREATE TABLE IF NOT EXISTS staging_teachers (
            id SERIAL PRIMARY KEY,
            school_id INT,
            full_name VARCHAR(200),
            email VARCHAR(100),
            phone VARCHAR(20),
            subject_specialization VARCHAR(200),
            qualification VARCHAR(200),
            joining_date DATE,
            username VARCHAR(100),
            password VARCHAR(255),
            cnic VARCHAR(20),
            validation_status VARCHAR(20),
            error_message VARCHAR(500),
            uploaded_by INT,
            uploaded_date TIMESTAMP DEFAULT NOW()
        )
        """,

        """
        CREATE TABLE IF NOT EXISTS staging_students (
            id SERIAL PRIMARY KEY,
            school_id INT,
            class_id INT,
            full_name VARCHAR(200),
            father_name VARCHAR(200),
            email VARCHAR(100),
            phone VARCHAR(20),
            date_of_birth DATE,
            gender VARCHAR(20),
            username VARCHAR(100),
            password VARCHAR(255),
            address_line1 VARCHAR(255),
            city VARCHAR(100),
            medical_details TEXT,
            validation_status VARCHAR(20),
            error_message VARCHAR(500),
            uploaded_by INT,
            uploaded_date TIMESTAMP DEFAULT NOW()
        )
        """
    ]

    for table_sql in tables:
        try:
            cursor.execute(table_sql)
            print("Table created/verified successfully")
        except Exception as e:
            print(f"Error creating table: {e}")
            conn.rollback()
        else:
            conn.commit()

    # Check if admin user exists
    try:
        cursor.execute("SELECT id FROM users WHERE username=%s", ('admin',))
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO users (username, password, role, full_name, is_active)
                VALUES (%s, %s, 'admin', %s, TRUE)
            """, ('admin', hash_password('admin@123'), 'System Administrator'))
            conn.commit()
            print("Default admin created: username='admin', password='admin@123'")
    except Exception as e:
        print(f"Error creating admin user: {e}")
        conn.rollback()

    conn.close()
    print("Database initialized successfully!")


if __name__ == "__main__":
    init_db()
