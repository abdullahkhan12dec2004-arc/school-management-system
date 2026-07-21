"""
models.py - Business Logic Models for School Management System
Compatible with database.py (Connection Pooling Version)
All database operations yahan handle hongi
"""

import datetime
import os
from werkzeug.utils import secure_filename
from database import get_db, fetchall_dict, fetchone_dict, hash_password


# ========== AUDIT MIXIN ==========
class AuditMixin:
    """Har model ke liye audit fields handle karta hai"""

    @staticmethod
    def get_current_user_id():
        """Session se current user ID nikalta hai"""
        from flask import session
        return session.get('user_id')

    @staticmethod
    def add_create_audit(cursor, table_name, record_id):
        """Create audit fields set karta hai"""
        user_id = AuditMixin.get_current_user_id()
        if user_id:
            cursor.execute(f"""
                UPDATE {table_name} 
                SET created_by = ?, created_date = GETDATE() 
                WHERE id = ?
            """, (user_id, record_id))

    @staticmethod
    def add_update_audit(cursor, table_name, record_id):
        """Update audit fields set karta hai"""
        user_id = AuditMixin.get_current_user_id()
        if user_id:
            cursor.execute(f"""
                UPDATE {table_name} 
                SET updated_by = ?, updated_date = GETDATE() 
                WHERE id = ?
            """, (user_id, record_id))


# ========== SCHOOL MODEL ==========
class School:
    """School related operations"""

    @staticmethod
    def get_all():
        """Saare schools fetch karo"""
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT * FROM schools ORDER BY name")
        schools = fetchall_dict(c)
        conn.close()
        return schools

    @staticmethod
    def get_by_id(school_id):
        """ID se school fetch karo"""
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT * FROM schools WHERE id=?", (school_id,))
        school = fetchone_dict(c)
        conn.close()
        return school

    @staticmethod
    def create(data, logo_file=None):
        """Naya school create karo with location details"""
        conn = get_db()
        c = conn.cursor()

        # Logo handle karo
        logo = None
        if logo_file and logo_file.filename:
            filename = secure_filename(logo_file.filename)
            upload_folder = 'static/uploads/logos'
            os.makedirs(upload_folder, exist_ok=True)
            logo_file.save(os.path.join(upload_folder, filename))
            logo = filename

        c.execute("""
            INSERT INTO schools 
            (name, address, phone, email, logo, country, city, area, latitude, longitude)
            OUTPUT INSERTED.id
            VALUES (?,?,?,?,?,?,?,?,?,?)
        """, (
            data.get('name'),
            data.get('address', ''),
            data.get('phone', ''),
            data.get('email', ''),
            logo,
            data.get('country', ''),
            data.get('city', ''),
            data.get('area', ''),
            data.get('latitude'),
            data.get('longitude')
        ))

        school_id = c.fetchone()[0]
        conn.commit()
        conn.close()
        return school_id

    @staticmethod
    def update(school_id, data, logo_file=None):
        """School update karo with location details"""
        conn = get_db()
        c = conn.cursor()

        if logo_file and logo_file.filename:
            filename = secure_filename(logo_file.filename)
            upload_folder = 'static/uploads/logos'
            os.makedirs(upload_folder, exist_ok=True)
            logo_file.save(os.path.join(upload_folder, filename))

            c.execute("""
                UPDATE schools 
                SET name=?, address=?, phone=?, email=?, country=?, city=?, 
                    area=?, latitude=?, longitude=?, logo=?
                WHERE id=?
            """, (
                data.get('name'), data.get('address'), data.get('phone'),
                data.get('email'), data.get('country'), data.get('city'),
                data.get('area'), data.get('latitude'), data.get('longitude'),
                filename, school_id
            ))
        else:
            c.execute("""
                UPDATE schools 
                SET name=?, address=?, phone=?, email=?, country=?, city=?, 
                    area=?, latitude=?, longitude=?
                WHERE id=?
            """, (
                data.get('name'), data.get('address'), data.get('phone'),
                data.get('email'), data.get('country'), data.get('city'),
                data.get('area'), data.get('latitude'), data.get('longitude'),
                school_id
            ))

        conn.commit()
        conn.close()
        return True


# ========== STUDENT MODEL ==========
class Student:
    """Student related operations"""

    @staticmethod
    def get_all(school_id=None, class_id=None):
        """Students fetch karo with filters"""
        conn = get_db()
        c = conn.cursor()

        query = """
            SELECT st.*, c.class_name, c.section, s.name AS school_name,
                   u.username, u.is_active
            FROM students st
            LEFT JOIN classes c ON st.class_id = c.id
            JOIN schools s ON st.school_id = s.id
            JOIN users u ON st.user_id = u.id
            WHERE 1=1
        """
        params = []

        if school_id:
            query += " AND st.school_id = ?"
            params.append(school_id)
        if class_id:
            query += " AND st.class_id = ?"
            params.append(class_id)

        query += " ORDER BY st.full_name"

        c.execute(query, params)
        students = fetchall_dict(c)
        conn.close()
        return students

    @staticmethod
    def get_by_id(student_id):
        """ID se student fetch karo with all details"""
        conn = get_db()
        c = conn.cursor()
        c.execute("""
            SELECT st.*, c.class_name, c.section, s.name AS school_name,
                   u.username, u.email AS user_email,
                   cr.full_name AS created_by_name,
                   up.full_name AS updated_by_name
            FROM students st
            LEFT JOIN classes c ON st.class_id = c.id
            JOIN schools s ON st.school_id = s.id
            JOIN users u ON st.user_id = u.id
            LEFT JOIN users cr ON st.created_by = cr.id
            LEFT JOIN users up ON st.updated_by = up.id
            WHERE st.id = ?
        """, (student_id,))
        student = fetchone_dict(c)
        conn.close()
        return student

    @staticmethod
    def get_by_user_id(user_id):
        """User ID se student fetch karo"""
        conn = get_db()
        c = conn.cursor()
        c.execute("""
            SELECT st.*, c.class_name, c.section
            FROM students st
            LEFT JOIN classes c ON st.class_id = c.id
            WHERE st.user_id = ?
        """, (user_id,))
        student = fetchone_dict(c)
        conn.close()
        return student

    @staticmethod
    def create(data, profile_pic=None):
        """Naya student create karo with all new fields"""
        conn = get_db()
        c = conn.cursor()

        # Profile picture handle karo
        pic_filename = None
        if profile_pic and profile_pic.filename:
            pic_filename = secure_filename(
                f"student_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}_{profile_pic.filename}"
            )
            upload_folder = 'static/uploads/students'
            os.makedirs(upload_folder, exist_ok=True)
            profile_pic.save(os.path.join(upload_folder, pic_filename))

        # Pehle user table mein entry
        c.execute("""
            INSERT INTO users 
            (school_id, username, password, role, full_name, email, phone)
            OUTPUT INSERTED.id
            VALUES (?,?,?,?,?,?,?)
        """, (
            data.get('school_id'),
            data.get('username'),
            hash_password(data.get('password')),
            'student',
            data.get('full_name'),
            data.get('email', ''),
            data.get('phone', '')
        ))

        user_id = c.fetchone()[0]

        # Student code generate karo
        student_code = f"STD-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"

        # Student table mein entry
        c.execute("""
            INSERT INTO students 
            (user_id, school_id, student_code, full_name, father_name, email, phone,
             date_of_birth, gender, class_id, joining_date, profile_pic, medical_details,
             address_line1, address_line2, city, state, postal_code)
            OUTPUT INSERTED.id
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            user_id,
            data.get('school_id'),
            student_code,
            data.get('full_name'),
            data.get('father_name', ''),
            data.get('email', ''),
            data.get('phone', ''),
            data.get('date_of_birth'),
            data.get('gender', ''),
            data.get('class_id'),
            data.get('joining_date'),
            pic_filename,
            data.get('medical_details', ''),
            data.get('address_line1', ''),
            data.get('address_line2', ''),
            data.get('city', ''),
            data.get('state', ''),
            data.get('postal_code', '')
        ))

        student_id = c.fetchone()[0]

        # Audit fields set karo
        AuditMixin.add_create_audit(c, 'students', student_id)

        conn.commit()
        conn.close()
        return student_id

    @staticmethod
    def update(student_id, data, profile_pic=None):
        """Student update karo with all fields"""
        conn = get_db()
        c = conn.cursor()

        # Profile picture handle karo
        if profile_pic and profile_pic.filename:
            pic_filename = secure_filename(f"student_{student_id}_{profile_pic.filename}")
            upload_folder = 'static/uploads/students'
            os.makedirs(upload_folder, exist_ok=True)
            profile_pic.save(os.path.join(upload_folder, pic_filename))

            c.execute("""
                UPDATE students 
                SET full_name=?, father_name=?, email=?, phone=?,
                    date_of_birth=?, gender=?, class_id=?, joining_date=?,
                    address_line1=?, address_line2=?, city=?, state=?,
                    postal_code=?, medical_details=?, profile_pic=?
                WHERE id=?
            """, (
                data.get('full_name'), data.get('father_name'),
                data.get('email'), data.get('phone'),
                data.get('date_of_birth'), data.get('gender'),
                data.get('class_id'), data.get('joining_date'),
                data.get('address_line1', ''), data.get('address_line2', ''),
                data.get('city', ''), data.get('state', ''),
                data.get('postal_code', ''), data.get('medical_details', ''),
                pic_filename, student_id
            ))
        else:
            c.execute("""
                UPDATE students 
                SET full_name=?, father_name=?, email=?, phone=?,
                    date_of_birth=?, gender=?, class_id=?, joining_date=?,
                    address_line1=?, address_line2=?, city=?, state=?,
                    postal_code=?, medical_details=?
                WHERE id=?
            """, (
                data.get('full_name'), data.get('father_name'),
                data.get('email'), data.get('phone'),
                data.get('date_of_birth'), data.get('gender'),
                data.get('class_id'), data.get('joining_date'),
                data.get('address_line1', ''), data.get('address_line2', ''),
                data.get('city', ''), data.get('state', ''),
                data.get('postal_code', ''), data.get('medical_details', ''),
                student_id
            ))

        # Audit fields update karo
        AuditMixin.add_update_audit(c, 'students', student_id)

        conn.commit()
        conn.close()
        return True


# ========== STUDENT PARENT MODEL ==========
class StudentParent:
    """Student ke parents/guardians handle karta hai"""

    @staticmethod
    def get_by_student(student_id):
        """Student ke saare parents fetch karo"""
        conn = get_db()
        c = conn.cursor()
        c.execute("""
            SELECT * FROM student_parents 
            WHERE student_id = ? 
            ORDER BY is_primary DESC, id
        """, (student_id,))
        parents = fetchall_dict(c)
        conn.close()
        return parents

    @staticmethod
    def add(student_id, parent_data):
        """Naya parent add karo"""
        conn = get_db()
        c = conn.cursor()

        c.execute("""
            INSERT INTO student_parents 
            (student_id, parent_name, relation, occupation, phone, email, address, is_primary)
            OUTPUT INSERTED.id
            VALUES (?,?,?,?,?,?,?,?)
        """, (
            student_id,
            parent_data.get('parent_name'),
            parent_data.get('relation', 'Father'),
            parent_data.get('occupation', ''),
            parent_data.get('phone', ''),
            parent_data.get('email', ''),
            parent_data.get('address', ''),
            parent_data.get('is_primary', 0)
        ))

        parent_id = c.fetchone()[0]
        AuditMixin.add_create_audit(c, 'student_parents', parent_id)

        conn.commit()
        conn.close()
        return parent_id

    @staticmethod
    def update(parent_id, parent_data):
        """Parent details update karo"""
        conn = get_db()
        c = conn.cursor()

        c.execute("""
            UPDATE student_parents 
            SET parent_name=?, relation=?, occupation=?, phone=?, email=?, address=?, is_primary=?
            WHERE id=?
        """, (
            parent_data.get('parent_name'),
            parent_data.get('relation'),
            parent_data.get('occupation'),
            parent_data.get('phone'),
            parent_data.get('email'),
            parent_data.get('address'),
            parent_data.get('is_primary', 0),
            parent_id
        ))

        AuditMixin.add_update_audit(c, 'student_parents', parent_id)

        conn.commit()
        conn.close()
        return True

    @staticmethod
    def delete(parent_id):
        """Parent delete karo"""
        conn = get_db()
        c = conn.cursor()
        c.execute("DELETE FROM student_parents WHERE id=?", (parent_id,))
        conn.commit()
        conn.close()
        return True

    @staticmethod
    def delete_all_for_student(student_id):
        """Student ke saare parents delete karo"""
        conn = get_db()
        c = conn.cursor()
        c.execute("DELETE FROM student_parents WHERE student_id=?", (student_id,))
        conn.commit()
        conn.close()
        return True

    @staticmethod
    def save_multiple(student_id, parents_list):
        """Multiple parents ek saath save karo"""
        StudentParent.delete_all_for_student(student_id)

        for parent in parents_list:
            if parent.get('parent_name', '').strip():
                StudentParent.add(student_id, parent)


# ========== STUDENT SIBLING MODEL ==========
class StudentSibling:
    """Student ke siblings handle karta hai"""

    @staticmethod
    def get_by_student(student_id):
        """Student ke saare siblings fetch karo"""
        conn = get_db()
        c = conn.cursor()
        c.execute("""
            SELECT ss.*, 
                   s.full_name AS linked_student_name,
                   s.student_code AS linked_student_code,
                   c.class_name AS linked_class_name
            FROM student_siblings ss
            LEFT JOIN students s ON ss.sibling_student_id = s.id
            LEFT JOIN classes c ON s.class_id = c.id
            WHERE ss.student_id = ?
            ORDER BY ss.id
        """, (student_id,))
        siblings = fetchall_dict(c)
        conn.close()
        return siblings

    @staticmethod
    def add(student_id, sibling_data):
        """Naya sibling add karo"""
        conn = get_db()
        c = conn.cursor()

        sibling_student_id = sibling_data.get('sibling_student_id')
        if sibling_student_id == '' or sibling_student_id == 'None' or sibling_student_id == 0:
            sibling_student_id = None

        c.execute("""
            INSERT INTO student_siblings 
            (student_id, sibling_name, age, class, school_name, sibling_student_id)
            OUTPUT INSERTED.id
            VALUES (?,?,?,?,?,?)
        """, (
            student_id,
            sibling_data.get('sibling_name'),
            sibling_data.get('age'),
            sibling_data.get('class', ''),
            sibling_data.get('school_name', ''),
            sibling_student_id
        ))

        sibling_id = c.fetchone()[0]
        AuditMixin.add_create_audit(c, 'student_siblings', sibling_id)

        conn.commit()
        conn.close()
        return sibling_id

    @staticmethod
    def update(sibling_id, sibling_data):
        """Sibling details update karo"""
        conn = get_db()
        c = conn.cursor()

        sibling_student_id = sibling_data.get('sibling_student_id')
        if sibling_student_id == '' or sibling_student_id == 'None' or sibling_student_id == 0:
            sibling_student_id = None

        c.execute("""
            UPDATE student_siblings 
            SET sibling_name=?, age=?, class=?, school_name=?, sibling_student_id=?
            WHERE id=?
        """, (
            sibling_data.get('sibling_name'),
            sibling_data.get('age'),
            sibling_data.get('class'),
            sibling_data.get('school_name'),
            sibling_student_id,
            sibling_id
        ))

        AuditMixin.add_update_audit(c, 'student_siblings', sibling_id)

        conn.commit()
        conn.close()
        return True

    @staticmethod
    def delete(sibling_id):
        """Sibling delete karo"""
        conn = get_db()
        c = conn.cursor()
        c.execute("DELETE FROM student_siblings WHERE id=?", (sibling_id,))
        conn.commit()
        conn.close()
        return True

    @staticmethod
    def delete_all_for_student(student_id):
        """Student ke saare siblings delete karo"""
        conn = get_db()
        c = conn.cursor()
        c.execute("DELETE FROM student_siblings WHERE student_id=?", (student_id,))
        conn.commit()
        conn.close()
        return True

    @staticmethod
    def save_multiple(student_id, siblings_list):
        """Multiple siblings ek saath save karo"""
        StudentSibling.delete_all_for_student(student_id)

        for sibling in siblings_list:
            if sibling.get('sibling_name', '').strip():
                StudentSibling.add(student_id, sibling)

    @staticmethod
    def get_students_for_linking(school_id, exclude_student_id=None):
        """Same school mein siblings link karne ke liye students ki list"""
        conn = get_db()
        c = conn.cursor()

        if exclude_student_id:
            c.execute("""
                SELECT id, full_name, student_code, class_id 
                FROM students 
                WHERE school_id=? AND id != ?
                ORDER BY full_name
            """, (school_id, exclude_student_id))
        else:
            c.execute("""
                SELECT id, full_name, student_code, class_id 
                FROM students 
                WHERE school_id=?
                ORDER BY full_name
            """, (school_id,))

        students = fetchall_dict(c)
        conn.close()
        return students


# ========== TEACHER MODEL ==========
class Teacher:
    """Teacher related operations"""

    @staticmethod
    def get_all(school_id=None):
        """Teachers fetch karo with school info"""
        conn = get_db()
        c = conn.cursor()

        query = """
            SELECT t.*, s.name AS school_name, u.username, u.is_active
            FROM teachers t
            JOIN schools s ON t.school_id = s.id
            JOIN users u ON t.user_id = u.id
            WHERE 1=1
        """
        params = []

        if school_id:
            query += " AND t.school_id = ?"
            params.append(school_id)

        query += " ORDER BY t.full_name"

        c.execute(query, params)
        teachers = fetchall_dict(c)
        conn.close()
        return teachers

    @staticmethod
    def get_by_id(teacher_id):
        """ID se teacher fetch karo"""
        conn = get_db()
        c = conn.cursor()
        c.execute("""
            SELECT t.*, s.name AS school_name,
                   cr.full_name AS created_by_name,
                   up.full_name AS updated_by_name
            FROM teachers t
            JOIN schools s ON t.school_id = s.id
            LEFT JOIN users cr ON t.created_by = cr.id
            LEFT JOIN users up ON t.updated_by = up.id
            WHERE t.id = ?
        """, (teacher_id,))
        teacher = fetchone_dict(c)
        conn.close()
        return teacher

    @staticmethod
    def get_by_user_id(user_id):
        """User ID se teacher fetch karo"""
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT * FROM teachers WHERE user_id = ?", (user_id,))
        teacher = fetchone_dict(c)
        conn.close()
        return teacher

    @staticmethod
    def create(data, profile_pic=None):
        """Naya teacher create karo"""
        conn = get_db()
        c = conn.cursor()

        # Profile picture handle karo
        pic_filename = None
        if profile_pic and profile_pic.filename:
            pic_filename = secure_filename(
                f"teacher_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}_{profile_pic.filename}"
            )
            upload_folder = 'static/uploads/teachers'
            os.makedirs(upload_folder, exist_ok=True)
            profile_pic.save(os.path.join(upload_folder, pic_filename))

        # User table mein entry
        c.execute("""
            INSERT INTO users 
            (school_id, username, password, role, full_name, email, phone)
            OUTPUT INSERTED.id
            VALUES (?,?,?,?,?,?,?)
        """, (
            data.get('school_id'),
            data.get('username'),
            hash_password(data.get('password')),
            'teacher',
            data.get('full_name'),
            data.get('email', ''),
            data.get('phone', '')
        ))

        user_id = c.fetchone()[0]

        # Teacher code generate karo
        teacher_code = f"TCH-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"

        # Teacher table mein entry
        c.execute("""
            INSERT INTO teachers 
            (user_id, school_id, teacher_code, full_name, email, phone,
             subject_specialization, qualification, joining_date, profile_pic, salary)
            OUTPUT INSERTED.id
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """, (
            user_id,
            data.get('school_id'),
            teacher_code,
            data.get('full_name'),
            data.get('email', ''),
            data.get('phone', ''),
            data.get('subject_specialization', ''),
            data.get('qualification', ''),
            data.get('joining_date'),
            pic_filename,
            data.get('salary')
        ))

        teacher_id = c.fetchone()[0]
        AuditMixin.add_create_audit(c, 'teachers', teacher_id)

        conn.commit()
        conn.close()
        return teacher_id

    @staticmethod
    def update(teacher_id, data, profile_pic=None):
        """Teacher update karo"""
        conn = get_db()
        c = conn.cursor()

        if profile_pic and profile_pic.filename:
            pic_filename = secure_filename(f"teacher_{teacher_id}_{profile_pic.filename}")
            upload_folder = 'static/uploads/teachers'
            os.makedirs(upload_folder, exist_ok=True)
            profile_pic.save(os.path.join(upload_folder, pic_filename))

            c.execute("""
                UPDATE teachers 
                SET full_name=?, email=?, phone=?, subject_specialization=?,
                    qualification=?, joining_date=?, salary=?, profile_pic=?
                WHERE id=?
            """, (
                data.get('full_name'), data.get('email'), data.get('phone'),
                data.get('subject_specialization'), data.get('qualification'),
                data.get('joining_date'), data.get('salary'),
                pic_filename, teacher_id
            ))
        else:
            c.execute("""
                UPDATE teachers 
                SET full_name=?, email=?, phone=?, subject_specialization=?,
                    qualification=?, joining_date=?, salary=?
                WHERE id=?
            """, (
                data.get('full_name'), data.get('email'), data.get('phone'),
                data.get('subject_specialization'), data.get('qualification'),
                data.get('joining_date'), data.get('salary'),
                teacher_id
            ))

        AuditMixin.add_update_audit(c, 'teachers', teacher_id)

        conn.commit()
        conn.close()
        return True


# ========== TEACHER DOCUMENTS MODEL ==========
class TeacherDocument:
    """Teacher ke certificates/degrees handle karta hai"""

    @staticmethod
    def get_by_teacher(teacher_id):
        """Teacher ke saare documents fetch karo"""
        conn = get_db()
        c = conn.cursor()
        c.execute("""
            SELECT * FROM teacher_documents 
            WHERE teacher_id = ?
            ORDER BY upload_date DESC
        """, (teacher_id,))
        documents = fetchall_dict(c)
        conn.close()
        return documents

    @staticmethod
    def add(teacher_id, document_file, document_type='Certificate'):
        """Naya document add karo"""
        conn = get_db()
        c = conn.cursor()

        if document_file and document_file.filename:
            filename = secure_filename(
                f"doc_{teacher_id}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}_{document_file.filename}"
            )
            upload_folder = 'static/uploads/certificates'
            os.makedirs(upload_folder, exist_ok=True)
            document_file.save(os.path.join(upload_folder, filename))

            c.execute("""
                INSERT INTO teacher_documents 
                (teacher_id, document_type, document_name, file_path)
                OUTPUT INSERTED.id
                VALUES (?,?,?,?)
            """, (teacher_id, document_type, document_file.filename, filename))

            doc_id = c.fetchone()[0]
            AuditMixin.add_create_audit(c, 'teacher_documents', doc_id)

            conn.commit()
            conn.close()
            return doc_id

        conn.close()
        return None

    @staticmethod
    def delete(document_id):
        """Document delete karo"""
        conn = get_db()
        c = conn.cursor()
        c.execute("DELETE FROM teacher_documents WHERE id=?", (document_id,))
        conn.commit()
        conn.close()
        return True


# ========== FEE COLLECTION MODEL ==========
class FeeCollection:
    """Fee collection operations"""

    @staticmethod
    def create(data):
        """Nayi fee entry create karo"""
        conn = get_db()
        c = conn.cursor()

        receipt_number = f"FEE-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"

        c.execute("""
            INSERT INTO fee_collections 
            (student_id, school_id, class_id, month, year, amount, 
             payment_mode, transaction_reference, remarks, collected_by, 
             receipt_number, created_by)
            OUTPUT INSERTED.id
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            data.get('student_id'),
            data.get('school_id'),
            data.get('class_id'),
            data.get('month'),
            data.get('year'),
            data.get('amount'),
            data.get('payment_mode'),
            data.get('transaction_reference', ''),
            data.get('remarks', ''),
            data.get('collected_by'),
            receipt_number,
            data.get('collected_by')  # created_by same as collected_by
        ))

        fee_id = c.fetchone()[0]
        conn.commit()
        conn.close()
        return fee_id

    @staticmethod
    def get_by_id(fee_id):
        """Fee receipt details fetch karo"""
        conn = get_db()
        c = conn.cursor()
        c.execute("""
            SELECT fc.*, s.full_name AS student_name, s.student_code,
                   c.class_name, c.section, sch.name AS school_name,
                   u.full_name AS collector_name
            FROM fee_collections fc
            JOIN students s ON fc.student_id = s.id
            JOIN classes c ON fc.class_id = c.id
            JOIN schools sch ON fc.school_id = sch.id
            JOIN users u ON fc.collected_by = u.id
            WHERE fc.id = ?
        """, (fee_id,))
        receipt = fetchone_dict(c)
        conn.close()
        return receipt

    @staticmethod
    def get_by_school(school_id, class_id=None, month=None, year=None):
        """School-wise fee collection report"""
        conn = get_db()
        c = conn.cursor()

        query = """
            SELECT fc.*, s.full_name AS student_name, s.student_code,
                   c.class_name, c.section,
                   u.full_name AS collector_name
            FROM fee_collections fc
            JOIN students s ON fc.student_id = s.id
            JOIN classes c ON fc.class_id = c.id
            JOIN users u ON fc.collected_by = u.id
            WHERE fc.school_id = ?
        """
        params = [school_id]

        if class_id:
            query += " AND fc.class_id = ?"
            params.append(class_id)
        if month:
            query += " AND fc.month = ?"
            params.append(month)
        if year:
            query += " AND fc.year = ?"
            params.append(year)

        query += " ORDER BY fc.created_date DESC"

        c.execute(query, params)
        fees = fetchall_dict(c)
        conn.close()
        return fees

    @staticmethod
    def get_by_student(student_id, month=None, year=None):
        """Student-wise fee history"""
        conn = get_db()
        c = conn.cursor()

        query = """
            SELECT fc.*, u.full_name AS collector_name
            FROM fee_collections fc
            JOIN users u ON fc.collected_by = u.id
            WHERE fc.student_id = ?
        """
        params = [student_id]

        if month:
            query += " AND fc.month = ?"
            params.append(month)
        if year:
            query += " AND fc.year = ?"
            params.append(year)

        query += " ORDER BY fc.created_date DESC"

        c.execute(query, params)
        fees = fetchall_dict(c)
        conn.close()
        return fees


# ========== ATTENDANCE MODELS ==========
class StudentAttendance:
    """Student attendance operations"""

    @staticmethod
    def mark_attendance(attendance_list, marked_by):
        """Multiple students ki attendance mark karo"""
        conn = get_db()
        c = conn.cursor()

        for record in attendance_list:
            # Check if already exists
            c.execute("""
                SELECT id FROM student_attendance 
                WHERE student_id=? AND attendance_date=?
            """, (record['student_id'], record['attendance_date']))

            existing = c.fetchone()

            if existing:
                c.execute("""
                    UPDATE student_attendance 
                    SET status=?, remarks=?, marked_by=?,
                        updated_by=?, updated_date=GETDATE()
                    WHERE id=?
                """, (
                    record['status'],
                    record.get('remarks', ''),
                    marked_by,
                    marked_by,
                    existing[0]
                ))
            else:
                c.execute("""
                    INSERT INTO student_attendance 
                    (student_id, class_id, school_id, attendance_date, 
                     status, remarks, marked_by, created_by)
                    VALUES (?,?,?,?,?,?,?,?)
                """, (
                    record['student_id'],
                    record['class_id'],
                    record['school_id'],
                    record['attendance_date'],
                    record['status'],
                    record.get('remarks', ''),
                    marked_by,
                    marked_by
                ))

        conn.commit()
        conn.close()
        return True

    @staticmethod
    def get_by_class(class_id, attendance_date):
        """Class-wise attendance fetch karo"""
        conn = get_db()
        c = conn.cursor()
        c.execute("""
            SELECT sa.*, s.full_name AS student_name, s.student_code
            FROM student_attendance sa
            JOIN students s ON sa.student_id = s.id
            WHERE sa.class_id=? AND sa.attendance_date=?
            ORDER BY s.full_name
        """, (class_id, attendance_date))
        attendance = fetchall_dict(c)
        conn.close()
        return attendance

    @staticmethod
    def get_student_report(student_id, month=None, year=None):
        """Student ka attendance report"""
        conn = get_db()
        c = conn.cursor()

        query = """
            SELECT * FROM student_attendance 
            WHERE student_id = ?
        """
        params = [student_id]

        if month and year:
            query += " AND MONTH(attendance_date)=? AND YEAR(attendance_date)=?"
            params.extend([month, year])
        elif year:
            query += " AND YEAR(attendance_date)=?"
            params.append(year)

        query += " ORDER BY attendance_date DESC"

        c.execute(query, params)
        attendance = fetchall_dict(c)
        conn.close()
        return attendance


class TeacherAttendance:
    """Teacher attendance operations"""

    @staticmethod
    def mark_attendance(attendance_list, marked_by):
        """Multiple teachers ki attendance mark karo"""
        conn = get_db()
        c = conn.cursor()

        for record in attendance_list:
            c.execute("""
                SELECT id FROM teacher_attendance 
                WHERE teacher_id=? AND attendance_date=?
            """, (record['teacher_id'], record['attendance_date']))

            existing = c.fetchone()

            if existing:
                c.execute("""
                    UPDATE teacher_attendance 
                    SET status=?, remarks=?, marked_by=?,
                        updated_by=?, updated_date=GETDATE()
                    WHERE id=?
                """, (
                    record['status'],
                    record.get('remarks', ''),
                    marked_by,
                    marked_by,
                    existing[0]
                ))
            else:
                c.execute("""
                    INSERT INTO teacher_attendance 
                    (teacher_id, school_id, attendance_date, 
                     status, remarks, marked_by, created_by)
                    VALUES (?,?,?,?,?,?,?)
                """, (
                    record['teacher_id'],
                    record['school_id'],
                    record['attendance_date'],
                    record['status'],
                    record.get('remarks', ''),
                    marked_by,
                    marked_by
                ))

        conn.commit()
        conn.close()
        return True

    @staticmethod
    def get_by_school(school_id, attendance_date=None):
        """School-wise teacher attendance"""
        conn = get_db()
        c = conn.cursor()

        if attendance_date:
            c.execute("""
                SELECT ta.*, t.full_name AS teacher_name, t.teacher_code
                FROM teacher_attendance ta
                JOIN teachers t ON ta.teacher_id = t.id
                WHERE ta.school_id=? AND ta.attendance_date=?
                ORDER BY t.full_name
            """, (school_id, attendance_date))
        else:
            c.execute("""
                SELECT ta.*, t.full_name AS teacher_name, t.teacher_code
                FROM teacher_attendance ta
                JOIN teachers t ON ta.teacher_id = t.id
                WHERE ta.school_id=?
                ORDER BY ta.attendance_date DESC, t.full_name
            """, (school_id,))

        attendance = fetchall_dict(c)
        conn.close()
        return attendance

    @staticmethod
    def get_teacher_report(teacher_id, month=None, year=None):
        """Teacher ka attendance report"""
        conn = get_db()
        c = conn.cursor()

        query = """
            SELECT * FROM teacher_attendance 
            WHERE teacher_id = ?
        """
        params = [teacher_id]

        if month and year:
            query += " AND MONTH(attendance_date)=? AND YEAR(attendance_date)=?"
            params.extend([month, year])
        elif year:
            query += " AND YEAR(attendance_date)=?"
            params.append(year)

        query += " ORDER BY attendance_date DESC"

        c.execute(query, params)
        attendance = fetchall_dict(c)
        conn.close()
        return attendance

################################################################
class Notice:
    def __init__(self):
        self.id = None
        self.school_id = None
        self.title = None
        self.body = None
        self.image_path = None
        self.is_active = True
        self.created_by = None
        self.created_date = None

class NoticeRecipient:
    def __init__(self):
        self.id = None
        self.notice_id = None
        self.role = None  # 'all', 'student', 'teacher'
# ========== CLASS MODEL ==========
class Class:
    """Class related operations"""

    @staticmethod
    def get_all(school_id=None):
        """Classes fetch karo"""
        conn = get_db()
        c = conn.cursor()

        query = """
            SELECT c.*, s.name AS school_name,
                   (SELECT COUNT(*) FROM students st WHERE st.class_id = c.id) AS student_count
            FROM classes c
            JOIN schools s ON c.school_id = s.id
            WHERE 1=1
        """
        params = []

        if school_id:
            query += " AND c.school_id = ?"
            params.append(school_id)

        query += " ORDER BY c.class_name, c.section"

        c.execute(query, params)
        classes = fetchall_dict(c)
        conn.close()
        return classes

    @staticmethod
    def get_by_id(class_id):
        """ID se class fetch karo"""
        conn = get_db()
        c = conn.cursor()
        c.execute("""
            SELECT c.*, s.name AS school_name
            FROM classes c
            JOIN schools s ON c.school_id = s.id
            WHERE c.id = ?
        """, (class_id,))
        class_info = fetchone_dict(c)
        conn.close()
        return class_info

    @staticmethod
    def create(data):
        """Nayi class create karo"""
        conn = get_db()
        c = conn.cursor()

        c.execute("""
            INSERT INTO classes 
            (school_id, class_name, section, academic_year)
            OUTPUT INSERTED.id
            VALUES (?,?,?,?)
        """, (
            data.get('school_id'),
            data.get('class_name'),
            data.get('section', ''),
            data.get('academic_year', '')
        ))

        class_id = c.fetchone()[0]
        AuditMixin.add_create_audit(c, 'classes', class_id)

        conn.commit()
        conn.close()
        return class_id


# ========== UTILITY FUNCTIONS ==========
def get_audit_info(table_name, record_id):
    """Kisi bhi record ki audit info fetch karo"""
    conn = get_db()
    c = conn.cursor()

    try:
        c.execute(f"""
            SELECT 
                cr.full_name AS created_by_name,
                crd.full_name AS created_by_name,
                record.created_date,
                up.full_name AS updated_by_name,
                record.updated_date
            FROM {table_name} record
            LEFT JOIN users cr ON record.created_by = cr.id
            LEFT JOIN users up ON record.updated_by = up.id
            WHERE record.id = ?
        """, (record_id,))

        return fetchone_dict(c)
    except:
        return None
    finally:
        conn.close()