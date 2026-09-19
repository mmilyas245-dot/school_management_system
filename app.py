import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import date
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="ZALMI Institute - Clerk Management", page_icon="🎓", layout="wide")

# ----------------------------------------------------------------------------
# CONFIG - edit these lists to match your academy's actual options
# ----------------------------------------------------------------------------
COURSES = ["English Language", "Spoken English", "Computer Basics", "MS Office",
           "Web Development", "Graphic Designing", "IELTS"]
CLASS_LEVELS = ["Level 1", "Level 2", "Level 3", "Level 4", "Level 5"]
CLASS_TIMINGS = ["8 to 9", "9 to 10", "10 to 11", "11 to 12",
                  "2 to 3", "3 to 4", "4 to 5", "5 to 6", "6 to 7", "7 to 8"]
MATERIAL_OPTIONS = ["Book Only", "Book & Vocab", "Not Issued"]
STATUS_OPTIONS = ["Current", "Completed", "Left", "On Hold"]

FIELD_KEYS = ["adm_no", "full_name", "father_name", "dob", "mobile", "address", "gender",
              "course", "class_level", "class_timing", "class_teacher", "material_issued",
              "student_status", "course_fees", "concession_percent", "offer_fees",
              "paid_fees", "due_fees"]

# ----------------------------------------------------------------------------
# LOGIN
# ----------------------------------------------------------------------------
def check_login():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if not st.session_state.logged_in:
        st.title("🎓 ZALMI Institute - Clerk Login")
        with st.form("login_form"):
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            ok = st.form_submit_button("Login")
        if ok:
            if u == st.secrets.get("APP_USERNAME", "admin") and p == st.secrets.get("APP_PASSWORD", "admin"):
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("Invalid username or password")
        st.stop()

check_login()

# ----------------------------------------------------------------------------
# DATABASE (Postgres - e.g. free Supabase / Neon project)
# ----------------------------------------------------------------------------
@st.cache_resource
def get_engine():
    return create_engine(st.secrets["DB_URL"], pool_pre_ping=True)

engine = get_engine()

def init_db():
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS students (
                id SERIAL PRIMARY KEY,
                adm_no TEXT,
                full_name TEXT NOT NULL,
                father_name TEXT,
                dob DATE,
                mobile TEXT,
                address TEXT,
                gender TEXT,
                course TEXT,
                class_level TEXT,
                class_timing TEXT,
                class_teacher TEXT,
                material_issued TEXT,
                student_status TEXT,
                course_fees NUMERIC,
                concession_percent NUMERIC,
                offer_fees NUMERIC,
                paid_fees NUMERIC,
                due_fees NUMERIC,
                entry_date TIMESTAMP DEFAULT now()
            )
        """))

init_db()

# ----------------------------------------------------------------------------
# GOOGLE SHEET SYNC
# ----------------------------------------------------------------------------
@st.cache_resource
def get_sheet():
    scopes = ["https://www.googleapis.com/auth/spreadsheets",
              "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(dict(st.secrets["gcp_service_account"]), scopes=scopes)
    client = gspread.authorize(creds)
    sh = client.open_by_key(st.secrets["GOOGLE_SHEET_ID"])
    return sh.sheet1

def sync_to_google_sheet(df=None):
    """Overwrite Google Sheet with the current database table."""
    try:
        ws = get_sheet()

        if df is None:
            df = read_all_students()

        ws.clear()

        if df.empty:
            ws.update([list(df.columns)])
        else:
            values = [list(df.columns)] + df.astype(str).values.tolist()
            ws.update(values)

        return True, None

    except Exception as e:
        return False, str(e)
# ----------------------------------------------------------------------------
# CRUD FUNCTIONS
# ----------------------------------------------------------------------------
def read_all_students(search=None):
    query = "SELECT * FROM students"
    params = {}
    if search:
        query += " WHERE full_name ILIKE :s OR adm_no ILIKE :s OR mobile ILIKE :s OR father_name ILIKE :s"
        params["s"] = f"%{search}%"
    query += " ORDER BY id DESC"
    with engine.connect() as conn:
        df = pd.read_sql(text(query), conn, params=params)
    return df

def insert_student(data: dict):
    with engine.begin() as conn:
        conn.execute(
            text(f"""
                INSERT INTO students ({', '.join(FIELD_KEYS)})
                VALUES ({', '.join(':' + k for k in FIELD_KEYS)})
            """),
            data
        )

    return sync_to_google_sheet()

def update_student(record_id: int, data: dict):
    data = dict(data)
    data["id"] = record_id

    set_clause = ", ".join(f"{k}=:{k}" for k in FIELD_KEYS)

    with engine.begin() as conn:
        conn.execute(
            text(f"UPDATE students SET {set_clause} WHERE id=:id"),
            data
        )

    return sync_to_google_sheet()


def delete_student(record_id: int):
    with engine.begin() as conn:
        conn.execute(
            text("DELETE FROM students WHERE id=:id"),
            {"id": record_id}
        )

    return sync_to_google_sheet()
# ----------------------------------------------------------------------------
# UI HELPERS
# ----------------------------------------------------------------------------
def student_form(prefix, record=None):
    """Renders the Personal/Academic/Financial fields. Returns a dict of values."""
    def v(key, default=""):
        if record is not None:
            val = record.get(key, default)
            return default if pd.isna(val) else val
        return default

    st.subheader("Personal Information")
    col1, col2 = st.columns(2)
    with col1:
        adm_no = st.text_input("Admission No", value=v("adm_no", ""), key=f"{prefix}_adm_no")
        full_name = st.text_input("Full Name *", value=v("full_name", ""), key=f"{prefix}_full_name")
        father_name = st.text_input("Father Name", value=v("father_name", ""), key=f"{prefix}_father_name")
        dob_default = record["dob"] if record is not None and record.get("dob") not in (None, "") else date(2005, 1, 1)
        if isinstance(dob_default, str):
            try:
                dob_default = date.fromisoformat(dob_default)
            except ValueError:
                dob_default = date(2005, 1, 1)
        dob = st.date_input("Date of Birth", value=dob_default, min_value=date(1960, 1, 1),
                             max_value=date.today(), key=f"{prefix}_dob")
    with col2:
        mobile = st.text_input("Mobile No", value=v("mobile", ""), key=f"{prefix}_mobile")
        address = st.text_input("Address", value=v("address", ""), key=f"{prefix}_address")
        gender_default = v("gender", "Male")
        gender = st.radio("Gender", ["Male", "Female"],
                           index=0 if gender_default == "Male" else 1,
                           horizontal=True, key=f"{prefix}_gender")

    st.subheader("Academic Details")
    col3, col4 = st.columns(2)
    with col3:
        course_default = v("course", COURSES[0])
        course = st.selectbox("Select Course", COURSES,
                               index=COURSES.index(course_default) if course_default in COURSES else 0,
                               key=f"{prefix}_course")
        level_default = v("class_level", CLASS_LEVELS[0])
        class_level = st.selectbox("Class Level", CLASS_LEVELS,
                                    index=CLASS_LEVELS.index(level_default) if level_default in CLASS_LEVELS else 0,
                                    key=f"{prefix}_class_level")
        timing_default = v("class_timing", CLASS_TIMINGS[0])
        class_timing = st.selectbox("Class Timing", CLASS_TIMINGS,
                                     index=CLASS_TIMINGS.index(timing_default) if timing_default in CLASS_TIMINGS else 0,
                                     key=f"{prefix}_class_timing")
    with col4:
        class_teacher = st.text_input("Class Teacher", value=v("class_teacher", ""), key=f"{prefix}_class_teacher")
        material_default = v("material_issued", MATERIAL_OPTIONS[0])
        material_issued = st.selectbox("Material Issued", MATERIAL_OPTIONS,
                                        index=MATERIAL_OPTIONS.index(material_default) if material_default in MATERIAL_OPTIONS else 0,
                                        key=f"{prefix}_material_issued")
        status_default = v("student_status", STATUS_OPTIONS[0])
        student_status = st.selectbox("Student Status", STATUS_OPTIONS,
                                       index=STATUS_OPTIONS.index(status_default) if status_default in STATUS_OPTIONS else 0,
                                       key=f"{prefix}_student_status")

    st.subheader("Financial Details")
    c1, c2, c3 = st.columns(3)
    with c1:
        course_fees = st.number_input("Course Fees", min_value=0.0, step=100.0,
                                       value=float(v("course_fees", 0) or 0), key=f"{prefix}_course_fees")
    with c2:
        concession = st.number_input("Concession (%)", min_value=0.0, max_value=100.0, step=1.0,
                                      value=float(v("concession_percent", 0) or 0), key=f"{prefix}_concession")
    with c3:
        paid_fees = st.number_input("Paid Fees", min_value=0.0, step=100.0,
                                     value=float(v("paid_fees", 0) or 0), key=f"{prefix}_paid_fees")

    offer_fees = course_fees - (course_fees * concession / 100)
    due_fees = offer_fees - paid_fees
    st.info(f"💰 Offer Fees: **{offer_fees:,.0f}**  |  Due Fees: **{due_fees:,.0f}**")

    return {
        "adm_no": adm_no, "full_name": full_name, "father_name": father_name, "dob": dob,
        "mobile": mobile, "address": address, "gender": gender, "course": course,
        "class_level": class_level, "class_timing": class_timing, "class_teacher": class_teacher,
        "material_issued": material_issued, "student_status": student_status,
        "course_fees": course_fees, "concession_percent": concession,
        "offer_fees": offer_fees, "paid_fees": paid_fees, "due_fees": due_fees,
    }

# ----------------------------------------------------------------------------
# SIDEBAR NAV
# ----------------------------------------------------------------------------
st.sidebar.title("📚 ZALMI Institute")
st.sidebar.caption("Clerk Management System")
menu = st.sidebar.radio("Menu", ["➕ New Entry", "🔍 Search / Update / Delete", "📋 All Records", "🚪 Logout"])

if menu == "🚪 Logout":
    st.session_state.logged_in = False
    st.rerun()

elif menu == "➕ New Entry":
    st.header("➕ New Student Entry")
    with st.form("entry_form", clear_on_submit=True):
        data = student_form("new")
        submitted = st.form_submit_button("✅ Entry", type="primary")
    if submitted:
        if not data["full_name"].strip():
            st.error("Full Name is required.")
        else:
            sheet_ok, sheet_error = insert_student(data)

            if sheet_ok:
                st.success(
                    f"Student '{data['full_name']}' added and synced to Google Sheet ✅"
                )
            else:
                st.warning(
                    f"Student '{data['full_name']}' was saved to the database, "
                    f"but Google Sheet sync failed."
                )
                st.error(f"Google Sheets error: {sheet_error}")
elif menu == "🔍 Search / Update / Delete":
    st.header("🔍 Search, Update or Delete")
    search = st.text_input("Search by Name / Admission No / Father Name / Mobile")
    df = read_all_students(search if search else None)

    if df.empty:
        st.info("No matching records.")
    else:
        st.dataframe(df.drop(columns=["entry_date"], errors="ignore"), use_container_width=True, hide_index=True)
        selected_id = st.selectbox("Select record ID to edit", df["id"].tolist())
        record = df[df["id"] == selected_id].iloc[0].to_dict()

        with st.form("update_form"):
            data = student_form("edit", record=record)
            b1, b2 = st.columns(2)
            update_clicked = b1.form_submit_button("💾 Update", type="primary")
            delete_clicked = b2.form_submit_button("🗑️ Delete")

        if update_clicked:
            sheet_ok, sheet_error = update_student(int(selected_id), data)

            if sheet_ok:
                st.success("Record updated and synced to Google Sheet ✅")
            else:
                st.warning("Record updated in database, but Google Sheet sync failed.")
                st.error(f"Google Sheets error: {sheet_error}")

            st.rerun()


        if delete_clicked:
            sheet_ok, sheet_error = delete_student(int(selected_id))

            if sheet_ok:
                st.success("Record deleted and synced to Google Sheet ✅")
            else:
                st.warning("Record deleted from database, but Google Sheet sync failed.")
                st.error(f"Google Sheets error: {sheet_error}")

            st.rerun()

elif menu == "📋 All Records":
    st.header("📋 All Student Records")
    df = read_all_students()
    st.dataframe(df, use_container_width=True, hide_index=True)

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Students", len(df))
    col2.metric("Total Paid Fees", f"{df['paid_fees'].sum():,.0f}" if not df.empty else 0)
    col3.metric("Total Due Fees", f"{df['due_fees'].sum():,.0f}" if not df.empty else 0)

    st.download_button("⬇️ Download as CSV (for printing/reports)",
                        df.to_csv(index=False).encode("utf-8"),
                        "students.csv", "text/csv")
    st.caption("Tip: open the CSV in Excel/Sheets to print, or use your browser's Print (Ctrl+P) on this page.")
