import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, date, time
from pathlib import Path
import hashlib
import io

# ============================================================
# CẤU HÌNH APP
# ============================================================

st.set_page_config(
    page_title="SMART TOUR - Quản lý Booking",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# DATABASE
# ============================================================

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

DB_PATH = DATA_DIR / "smart_tour.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


conn = get_connection()


def init_database():

    cursor = conn.cursor()

    # --------------------------------------------------------
    # USERS
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            full_name TEXT,
            role TEXT DEFAULT 'admin'
        )
    """)

    # --------------------------------------------------------
    # TOURS
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tours (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            destination TEXT,
            duration TEXT,
            adult_price REAL DEFAULT 0,
            child_price REAL DEFAULT 0,
            infant_price REAL DEFAULT 0,
            description TEXT,
            status TEXT DEFAULT 'Đang hoạt động'
        )
    """)

    # --------------------------------------------------------
    # CUSTOMERS
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            phone TEXT,
            email TEXT,
            gender TEXT,
            birth_date TEXT,
            id_number TEXT,
            address TEXT,
            note TEXT,
            created_at TEXT
        )
    """)

    # --------------------------------------------------------
    # HOTELS
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS hotels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            address TEXT,
            stars INTEGER DEFAULT 3,
            room_type TEXT,
            room_price REAL DEFAULT 0,
            available_rooms INTEGER DEFAULT 0,
            note TEXT
        )
    """)

    # --------------------------------------------------------
    # BOOKINGS
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            booking_code TEXT UNIQUE NOT NULL,
            customer_id INTEGER,
            tour_id INTEGER,

            departure_date TEXT,
            departure_time TEXT,
            return_date TEXT,

            adults INTEGER DEFAULT 0,
            children INTEGER DEFAULT 0,
            infants INTEGER DEFAULT 0,

            hotel_id INTEGER,
            rooms INTEGER DEFAULT 0,
            hotel_total REAL DEFAULT 0,

            tour_total REAL DEFAULT 0,
            discount REAL DEFAULT 0,
            total_amount REAL DEFAULT 0,

            deposit REAL DEFAULT 0,
            paid REAL DEFAULT 0,
            remaining REAL DEFAULT 0,

            payment_status TEXT DEFAULT 'Chưa thanh toán',
            booking_status TEXT DEFAULT 'Mới',
            note TEXT,

            created_at TEXT
        )
    """)

    # --------------------------------------------------------
    # BOOKING HISTORY
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS booking_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            booking_id INTEGER,
            action TEXT,
            created_at TEXT
        )
    """)

    # --------------------------------------------------------
    # DEFAULT ADMIN
    # --------------------------------------------------------

    password_hash = hashlib.sha256(
        "admin123".encode()
    ).hexdigest()

    cursor.execute("""
        INSERT OR IGNORE INTO users
        (username, password, full_name, role)
        VALUES (?, ?, ?, ?)
    """, (
        "admin",
        password_hash,
        "Administrator",
        "admin"
    ))

    conn.commit()


init_database()


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def money(value):
    try:
        return f"{float(value):,.0f} ₫"
    except:
        return "0 ₫"


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def execute_query(query, params=(), fetch=False, many=False):

    cursor = conn.cursor()

    if many:
        cursor.executemany(query, params)
    else:
        cursor.execute(query, params)

    conn.commit()

    if fetch:
        return cursor.fetchall()

    return cursor.lastrowid


def get_dataframe(query, params=()):
    return pd.read_sql_query(query, conn, params=params)


def generate_booking_code():

    prefix = datetime.now().strftime("ST%Y%m%d")

    row = execute_query("""
        SELECT COUNT(*) as total
        FROM bookings
        WHERE booking_code LIKE ?
    """, (prefix + "%",), fetch=True)

    number = row[0]["total"] + 1

    return f"{prefix}{number:03d}"


# ============================================================
# SESSION
# ============================================================

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "username" not in st.session_state:
    st.session_state.username = ""


# ============================================================
# LOGIN
# ============================================================

def login_page():

    st.markdown("""
    <style>
    .login-title {
        text-align:center;
        font-size:42px;
        font-weight:800;
        margin-top:60px;
    }

    .login-subtitle {
        text-align:center;
        color:#666;
        margin-bottom:30px;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown(
        '<div class="login-title">✈️ SMART TOUR</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="login-subtitle">Hệ thống quản lý booking tour</div>',
        unsafe_allow_html=True
    )

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:

        with st.form("login_form"):

            username = st.text_input(
                "Tên đăng nhập",
                placeholder="Nhập username"
            )

            password = st.text_input(
                "Mật khẩu",
                type="password",
                placeholder="Nhập mật khẩu"
            )

            submit = st.form_submit_button(
                "🔐 ĐĂNG NHẬP",
                use_container_width=True
            )

            if submit:

                password_hash = hash_password(password)

                result = execute_query("""
                    SELECT *
                    FROM users
                    WHERE username = ?
                    AND password = ?
                """, (
                    username,
                    password_hash
                ), fetch=True)

                if result:

                    st.session_state.logged_in = True
                    st.session_state.username = username

                    st.rerun()

                else:

                    st.error(
                        "Tên đăng nhập hoặc mật khẩu không chính xác."
                    )

        st.info(
            "Tài khoản mặc định: admin / admin123"
        )


if not st.session_state.logged_in:
    login_page()
    st.stop()


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.markdown("""
# ✈️ SMART TOUR
### Quản lý Booking Tour
""")

st.sidebar.divider()

menu = st.sidebar.radio(
    "MENU",
    [
        "🏠 Dashboard",
        "📋 Booking",
        "👤 Khách hàng",
        "🗺️ Tour",
        "🏨 Khách sạn",
        "📊 Báo cáo",
        "⚙️ Admin"
    ]
)

st.sidebar.divider()

st.sidebar.write(
    f"👤 **{st.session_state.username}**"
)

if st.sidebar.button(
    "🚪 Đăng xuất",
    use_container_width=True
):

    st.session_state.logged_in = False
    st.session_state.username = ""
    st.rerun()


# ============================================================
# DASHBOARD
# ============================================================

if menu == "🏠 Dashboard":

    st.title("🏠 Dashboard")

    st.caption(
        "Tổng quan hoạt động kinh doanh tour"
    )

    # --------------------------------------------------------
    # STATISTICS
    # --------------------------------------------------------

    total_bookings = execute_query("""
        SELECT COUNT(*) AS total
        FROM bookings
    """, fetch=True)[0]["total"]

    total_customers = execute_query("""
        SELECT COUNT(*) AS total
        FROM customers
    """, fetch=True)[0]["total"]

    total_tours = execute_query("""
        SELECT COUNT(*) AS total
        FROM tours
    """, fetch=True)[0]["total"]

    total_revenue = execute_query("""
        SELECT COALESCE(SUM(total_amount), 0) AS total
        FROM bookings
        WHERE booking_status != 'Đã hủy'
    """, fetch=True)[0]["total"]

    total_paid = execute_query("""
        SELECT COALESCE(SUM(paid), 0) AS total
        FROM bookings
        WHERE booking_status != 'Đã hủy'
    """, fetch=True)[0]["total"]

    remaining = total_revenue - total_paid

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "📋 Tổng booking",
        f"{total_bookings:,}"
    )

    col2.metric(
        "👤 Khách hàng",
        f"{total_customers:,}"
    )

    col3.metric(
        "🗺️ Tour",
        f"{total_tours:,}"
    )

    col4.metric(
        "💰 Doanh thu",
        money(total_revenue)
    )

    st.divider()

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "💵 Đã thu",
        money(total_paid)
    )

    col2.metric(
        "⏳ Còn phải thu",
        money(remaining)
    )

    active_bookings = execute_query("""
        SELECT COUNT(*) AS total
        FROM bookings
        WHERE booking_status IN ('Mới', 'Đã xác nhận')
    """, fetch=True)[0]["total"]

    col3.metric(
        "🟢 Booking đang xử lý",
        active_bookings
    )

    st.divider()

    # --------------------------------------------------------
    # RECENT BOOKINGS
    # --------------------------------------------------------

    st.subheader("📋 Booking gần đây")

    recent = get_dataframe("""
        SELECT
            b.booking_code AS 'Mã booking',
            c.full_name AS 'Khách hàng',
            t.name AS 'Tour',
            b.departure_date AS 'Ngày đi',
            b.total_amount AS 'Tổng tiền',
            b.payment_status AS 'Thanh toán',
            b.booking_status AS 'Trạng thái'
        FROM bookings b
        LEFT JOIN customers c
            ON b.customer_id = c.id
        LEFT JOIN tours t
            ON b.tour_id = t.id
        ORDER BY b.id DESC
        LIMIT 10
    """)

    if len(recent):

        recent["Tổng tiền"] = recent["Tổng tiền"].apply(money)

        st.dataframe(
            recent,
            use_container_width=True,
            hide_index=True
        )

    else:

        st.info(
            "Chưa có booking nào."
        )


# ============================================================
# BOOKING
# ============================================================

elif menu == "📋 Booking":

    st.title("📋 Quản lý Booking")

    tab1, tab2, tab3 = st.tabs([
        "➕ Tạo booking",
        "📋 Danh sách booking",
        "🔎 Tra cứu"
    ])

    # ========================================================
    # CREATE BOOKING
    # ========================================================

    with tab1:

        st.subheader("Tạo booking mới")

        customers = get_dataframe("""
            SELECT id, full_name, phone
            FROM customers
            ORDER BY full_name
        """)

        tours = get_dataframe("""
            SELECT *
            FROM tours
            WHERE status = 'Đang hoạt động'
            ORDER BY name
        """)

        hotels = get_dataframe("""
            SELECT *
            FROM hotels
            ORDER BY name
        """)

        if customers.empty:

            st.warning(
                "Chưa có khách hàng. "
                "Hãy tạo khách hàng trước."
            )

        elif tours.empty:

            st.warning(
                "Chưa có tour. "
                "Hãy tạo tour trước."
            )

        else:

            with st.form("booking_form"):

                col1, col2 = st.columns(2)

                with col1:

                    customer_options = {
                        f"{row['full_name']} - {row['phone']}":
                        row["id"]
                        for _, row in customers.iterrows()
                    }

                    customer_label = st.selectbox(
                        "👤 Khách hàng *",
                        list(customer_options.keys())
                    )

                    customer_id = customer_options[
                        customer_label
                    ]

                with col2:

                    tour_options = {
                        f"{row['code']} - {row['name']}":
                        row["id"]
                        for _, row in tours.iterrows()
                    }

                    tour_label = st.selectbox(
                        "🗺️ Tour *",
                        list(tour_options.keys())
                    )

                    tour_id = tour_options[tour_label]

                st.divider()

                col1, col2, col3 = st.columns(3)

                with col1:

                    departure_date = st.date_input(
                        "📅 Ngày khởi hành",
                        value=date.today()
                    )

                with col2:

                    departure_time = st.time_input(
                        "⏰ Giờ khởi hành",
                        value=time(7, 0)
                    )

                with col3:

                    return_date = st.date_input(
                        "📅 Ngày kết thúc",
                        value=date.today()
                    )

                st.subheader(
                    "👨‍👩‍👧 Số lượng khách"
                )

                col1, col2, col3 = st.columns(3)

                with col1:

                    adults = st.number_input(
                        "👨 Người lớn",
                        min_value=0,
                        value=2,
                        step=1
                    )

                with col2:

                    children = st.number_input(
                        "🧒 Trẻ em",
                        min_value=0,
                        value=0,
                        step=1
                    )

                with col3:

                    infants = st.number_input(
                        "👶 Em bé",
                        min_value=0,
                        value=0,
                        step=1
                    )

                st.subheader(
                    "🏨 Khách sạn"
                )

                if hotels.empty:

                    hotel_id = None

                    rooms = 0

                    st.info(
                        "Chưa có khách sạn. "
                        "Booking sẽ không tính tiền phòng."
                    )

                else:

                    hotel_options = {
                        f"{row['name']} - "
                        f"{row['room_type']} - "
                        f"{money(row['room_price'])}/phòng":
                        row["id"]
                        for _, row in hotels.iterrows()
                    }

                    hotel_label = st.selectbox(
                        "Khách sạn",
                        ["Không chọn"] +
                        list(hotel_options.keys())
                    )

                    if hotel_label == "Không chọn":

                        hotel_id = None

                        rooms = 0

                    else:

                        hotel_id = hotel_options[
                            hotel_label
                        ]

                        rooms = st.number_input(
                            "Số phòng",
                            min_value=0,
                            value=1,
                            step=1
                        )

                st.subheader(
                    "💰 Chiết khấu & thanh toán"
                )

                discount = st.number_input(
                    "Chiết khấu",
                    min_value=0.0,
                    value=0.0,
                    step=100000.0
                )

                deposit = st.number_input(
                    "Tiền cọc",
                    min_value=0.0,
                    value=0.0,
                    step=100000.0
                )

                paid = st.number_input(
                    "Đã thanh toán",
                    min_value=0.0,
                    value=0.0,
                    step=100000.0
                )

                booking_status = st.selectbox(
                    "Trạng thái booking",
                    [
                        "Mới",
                        "Đã xác nhận",
                        "Đang đi",
                        "Hoàn thành",
                        "Đã hủy"
                    ]
                )

                note = st.text_area(
                    "Ghi chú"
                )

                submit = st.form_submit_button(
                    "💾 TẠO BOOKING",
                    use_container_width=True
                )

                if submit:

                    tour = get_dataframe("""
                        SELECT *
                        FROM tours
                        WHERE id = ?
                    """, (tour_id,))

                    tour_data = tour.iloc[0]

                    tour_total = (
                        adults * tour_data["adult_price"]
                        + children * tour_data["child_price"]
                        + infants * tour_data["infant_price"]
                    )

                    hotel_total = 0

                    if hotel_id:

                        hotel = get_dataframe("""
                            SELECT room_price
                            FROM hotels
                            WHERE id = ?
                        """, (hotel_id,))

                        if not hotel.empty:

                            room_price = hotel.iloc[0][
                                "room_price"
                            ]

                            hotel_total = (
                                rooms * room_price
                            )

                    total_amount = (
                        tour_total
                        + hotel_total
                        - discount
                    )

                    if total_amount < 0:
                        total_amount = 0

                    remaining = max(
                        total_amount - paid,
                        0
                    )

                    if paid <= 0:

                        payment_status = "Chưa thanh toán"

                    elif paid < total_amount:

                        payment_status = "Đã cọc"

                    else:

                        payment_status = "Đã thanh toán"

                    booking_code = generate_booking_code()

                    booking_id = execute_query("""
                        INSERT INTO bookings (
                            booking_code,
                            customer_id,
                            tour_id,
                            departure_date,
                            departure_time,
                            return_date,
                            adults,
                            children,
                            infants,
                            hotel_id,
                            rooms,
                            hotel_total,
                            tour_total,
                            discount,
                            total_amount,
                            deposit,
                            paid,
                            remaining,
                            payment_status,
                            booking_status,
                            note,
                            created_at
                        )
                        VALUES (
                            ?, ?, ?, ?, ?, ?, ?, ?, ?,
                            ?, ?, ?, ?, ?, ?, ?, ?, ?,
                            ?, ?, ?, ?
                        )
                    """, (
                        booking_code,
                        customer_id,
                        tour_id,
                        str(departure_date),
                        departure_time.strftime("%H:%M"),
                        str(return_date),
                        adults,
                        children,
                        infants,
                        hotel_id,
                        rooms,
                        hotel_total,
                        tour_total,
                        discount,
                        total_amount,
                        deposit,
                        paid,
                        remaining,
                        payment_status,
                        booking_status,
                        note,
                        datetime.now().isoformat()
                    ))

                    execute_query("""
                        INSERT INTO booking_history
                        (booking_id, action, created_at)
                        VALUES (?, ?, ?)
                    """, (
                        booking_id,
                        "Tạo booking",
                        datetime.now().isoformat()
                    ))

                    st.success(
                        f"Đã tạo booking **{booking_code}**"
                    )

                    st.info(
                        f"Tổng tiền: {money(total_amount)} | "
                        f"Còn lại: {money(remaining)}"
                    )

    # ========================================================
    # BOOKING LIST
    # ========================================================

    with tab2:

        st.subheader("Danh sách booking")

        search = st.text_input(
            "🔎 Tìm theo mã booking / khách hàng"
        )

        status_filter = st.multiselect(
            "Trạng thái",
            [
                "Mới",
                "Đã xác nhận",
                "Đang đi",
                "Hoàn thành",
                "Đã hủy"
            ]
        )

        query = """
            SELECT
                b.id,
                b.booking_code AS 'Mã booking',
                c.full_name AS 'Khách hàng',
                c.phone AS 'Số điện thoại',
                t.name AS 'Tour',
                b.departure_date AS 'Ngày đi',
                b.adults AS 'NL',
                b.children AS 'TE',
                b.infants AS 'EB',
                b.total_amount AS 'Tổng tiền',
                b.paid AS 'Đã thu',
                b.remaining AS 'Còn lại',
                b.payment_status AS 'Thanh toán',
                b.booking_status AS 'Trạng thái'
            FROM bookings b
            LEFT JOIN customers c
                ON b.customer_id = c.id
            LEFT JOIN tours t
                ON b.tour_id = t.id
            WHERE 1=1
        """

        params = []

        if search:

            query += """
                AND (
                    b.booking_code LIKE ?
                    OR c.full_name LIKE ?
                    OR c.phone LIKE ?
                )
            """

            keyword = f"%{search}%"

            params.extend([
                keyword,
                keyword,
                keyword
            ])

        if status_filter:

            placeholders = ",".join(
                ["?"] * len(status_filter)
            )

            query += f"""
                AND b.booking_status IN ({placeholders})
            """

            params.extend(status_filter)

        query += """
            ORDER BY b.id DESC
        """

        bookings = get_dataframe(
            query,
            params
        )

        if not bookings.empty:

            display_df = bookings.copy()

            for col in [
                "Tổng tiền",
                "Đã thu",
                "Còn lại"
            ]:

                display_df[col] = display_df[
                    col
                ].apply(money)

            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True
            )

            csv = bookings.to_csv(
                index=False
            ).encode("utf-8-sig")

            st.download_button(
                "⬇️ Xuất CSV",
                csv,
                "booking_smart_tour.csv",
                "text/csv",
                use_container_width=True
            )

        else:

            st.info(
                "Không tìm thấy booking."
            )

    # ========================================================
    # SEARCH
    # ========================================================

    with tab3:

        st.subheader(
            "🔎 Tra cứu chi tiết booking"
        )

        booking_code = st.text_input(
            "Nhập mã booking"
        )

        if booking_code:

            result = get_dataframe("""
                SELECT
                    b.*,
                    c.full_name,
                    c.phone,
                    c.email,
                    t.name AS tour_name,
                    t.destination,
                    h.name AS hotel_name
                FROM bookings b
                LEFT JOIN customers c
                    ON b.customer_id = c.id
                LEFT JOIN tours t
                    ON b.tour_id = t.id
                LEFT JOIN hotels h
                    ON b.hotel_id = h.id
                WHERE b.booking_code = ?
            """, (booking_code,))

            if result.empty:

                st.error(
                    "Không tìm thấy booking."
                )

            else:

                booking = result.iloc[0]

                col1, col2, col3 = st.columns(3)

                col1.metric(
                    "Mã booking",
                    booking["booking_code"]
                )

                col2.metric(
                    "Tổng tiền",
                    money(booking["total_amount"])
                )

                col3.metric(
                    "Còn lại",
                    money(booking["remaining"])
                )

                st.divider()

                c1, c2 = st.columns(2)

                with c1:

                    st.write(
                        f"**Khách hàng:** "
                        f"{booking['full_name']}"
                    )

                    st.write(
                        f"**Điện thoại:** "
                        f"{booking['phone']}"
                    )

                    st.write(
                        f"**Email:** "
                        f"{booking['email']}"
                    )

                with c2:

                    st.write(
                        f"**Tour:** "
                        f"{booking['tour_name']}"
                    )

                    st.write(
                        f"**Điểm đến:** "
                        f"{booking['destination']}"
                    )

                    st.write(
                        f"**Khách sạn:** "
                        f"{booking['hotel_name'] or 'Không có'}"
                    )

                st.divider()

                st.write(
                    f"📅 Ngày đi: "
                    f"**{booking['departure_date']}**"
                )

                st.write(
                    f"⏰ Giờ đi: "
                    f"**{booking['departure_time']}**"
                )

                st.write(
                    f"👨 Người lớn: "
                    f"**{booking['adults']}**"
                )

                st.write(
                    f"🧒 Trẻ em: "
                    f"**{booking['children']}**"
                )

                st.write(
                    f"👶 Em bé: "
                    f"**{booking['infants']}**"
                )

                st.write(
                    f"💰 Tổng tiền tour: "
                    f"**{money(booking['tour_total'])}**"
                )

                st.write(
                    f"🏨 Tiền khách sạn: "
                    f"**{money(booking['hotel_total'])}**"
                )

                st.write(
                    f"🏷️ Giảm giá: "
                    f"**{money(booking['discount'])}**"
                )

                st.write(
                    f"💵 Đã thanh toán: "
                    f"**{money(booking['paid'])}**"
                )

                st.write(
                    f"⏳ Còn lại: "
                    f"**{money(booking['remaining'])}**"
                )


# ============================================================
# CUSTOMERS
# ============================================================

elif menu == "👤 Khách hàng":

    st.title("👤 Quản lý khách hàng")

    tab1, tab2 = st.tabs([
        "➕ Thêm khách hàng",
        "📋 Danh sách"
    ])

    with tab1:

        with st.form("customer_form"):

            col1, col2 = st.columns(2)

            with col1:

                full_name = st.text_input(
                    "Họ và tên *"
                )

                phone = st.text_input(
                    "Số điện thoại"
                )

                email = st.text_input(
                    "Email"
                )

                gender = st.selectbox(
                    "Giới tính",
                    [
                        "Nam",
                        "Nữ",
                        "Khác"
                    ]
                )

            with col2:

                birth_date = st.date_input(
                    "Ngày sinh",
                    value=date(2000, 1, 1)
                )

                id_number = st.text_input(
                    "CCCD / Hộ chiếu"
                )

                address = st.text_input(
                    "Địa chỉ"
                )

            note = st.text_area(
                "Ghi chú"
            )

            submit = st.form_submit_button(
                "💾 LƯU KHÁCH HÀNG",
                use_container_width=True
            )

            if submit:

                if not full_name.strip():

                    st.error(
                        "Vui lòng nhập họ tên."
                    )

                else:

                    execute_query("""
                        INSERT INTO customers (
                            full_name,
                            phone,
                            email,
                            gender,
                            birth_date,
                            id_number,
                            address,
                            note,
                            created_at
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        full_name,
                        phone,
                        email,
                        gender,
                        str(birth_date),
                        id_number,
                        address,
                        note,
                        datetime.now().isoformat()
                    ))

                    st.success(
                        "Đã thêm khách hàng."
                    )

    with tab2:

        customers = get_dataframe("""
            SELECT
                id AS ID,
                full_name AS 'Họ tên',
                phone AS 'Điện thoại',
                email AS 'Email',
                gender AS 'Giới tính',
                birth_date AS 'Ngày sinh',
                id_number AS 'CCCD/Hộ chiếu',
                address AS 'Địa chỉ'
            FROM customers
            ORDER BY id DESC
        """)

        if customers.empty:

            st.info(
                "Chưa có khách hàng."
            )

        else:

            st.dataframe(
                customers,
                use_container_width=True,
                hide_index=True
            )


# ============================================================
# TOURS
# ============================================================

elif menu == "🗺️ Tour":

    st.title("🗺️ Quản lý Tour")

    tab1, tab2 = st.tabs([
        "➕ Thêm tour",
        "📋 Danh sách tour"
    ])

    with tab1:

        with st.form("tour_form"):

            col1, col2 = st.columns(2)

            with col1:

                code = st.text_input(
                    "Mã tour *",
                    placeholder="VD: VT001"
                )

                name = st.text_input(
                    "Tên tour *"
                )

                destination = st.text_input(
                    "Điểm đến"
                )

                duration = st.text_input(
                    "Thời lượng",
                    placeholder="VD: 2N1Đ"
                )

            with col2:

                adult_price = st.number_input(
                    "Giá người lớn",
                    min_value=0.0,
                    step=100000.0
                )

                child_price = st.number_input(
                    "Giá trẻ em",
                    min_value=0.0,
                    step=100000.0
                )

                infant_price = st.number_input(
                    "Giá em bé",
                    min_value=0.0,
                    step=50000.0
                )

                status = st.selectbox(
                    "Trạng thái",
                    [
                        "Đang hoạt động",
                        "Tạm ngưng"
                    ]
                )

            description = st.text_area(
                "Mô tả tour"
            )

            submit = st.form_submit_button(
                "💾 LƯU TOUR",
                use_container_width=True
            )

            if submit:

                if not code or not name:

                    st.error(
                        "Mã tour và tên tour là bắt buộc."
                    )

                else:

                    try:

                        execute_query("""
                            INSERT INTO tours (
                                code,
                                name,
                                destination,
                                duration,
                                adult_price,
                                child_price,
                                infant_price,
                                description,
                                status
                            )
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            code,
                            name,
                            destination,
                            duration,
                            adult_price,
                            child_price,
                            infant_price,
                            description,
                            status
                        ))

                        st.success(
                            "Đã thêm tour."
                        )

                    except sqlite3.IntegrityError:

                        st.error(
                            "Mã tour đã tồn tại."
                        )

    with tab2:

        tours = get_dataframe("""
            SELECT
                id AS ID,
                code AS 'Mã tour',
                name AS 'Tên tour',
                destination AS 'Điểm đến',
                duration AS 'Thời lượng',
                adult_price AS 'Giá NL',
                child_price AS 'Giá TE',
                infant_price AS 'Giá EB',
                status AS 'Trạng thái'
            FROM tours
            ORDER BY id DESC
        """)

        if not tours.empty:

            display = tours.copy()

            for col in [
                "Giá NL",
                "Giá TE",
                "Giá EB"
            ]:

                display[col] = display[
                    col
                ].apply(money)

            st.dataframe(
                display,
                use_container_width=True,
                hide_index=True
            )

        else:

            st.info(
                "Chưa có tour."
            )


# ============================================================
# HOTELS
# ============================================================

elif menu == "🏨 Khách sạn":

    st.title("🏨 Quản lý khách sạn")

    tab1, tab2 = st.tabs([
        "➕ Thêm khách sạn",
        "📋 Danh sách"
    ])

    with tab1:

        with st.form("hotel_form"):

            col1, col2 = st.columns(2)

            with col1:

                name = st.text_input(
                    "Tên khách sạn *"
                )

                address = st.text_input(
                    "Địa chỉ"
                )

                stars = st.number_input(
                    "Số sao",
                    min_value=1,
                    max_value=5,
                    value=3
                )

            with col2:

                room_type = st.text_input(
                    "Loại phòng",
                    placeholder="Standard / Deluxe / Suite"
                )

                room_price = st.number_input(
                    "Giá phòng",
                    min_value=0.0,
                    step=100000.0
                )

                available_rooms = st.number_input(
                    "Số phòng có sẵn",
                    min_value=0,
                    value=10
                )

            note = st.text_area(
                "Ghi chú"
            )

            submit = st.form_submit_button(
                "💾 LƯU KHÁCH SẠN",
                use_container_width=True
            )

            if submit:

                if not name:

                    st.error(
                        "Vui lòng nhập tên khách sạn."
                    )

                else:

                    execute_query("""
                        INSERT INTO hotels (
                            name,
                            address,
                            stars,
                            room_type,
                            room_price,
                            available_rooms,
                            note
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        name,
                        address,
                        stars,
                        room_type,
                        room_price,
                        available_rooms,
                        note
                    ))

                    st.success(
                        "Đã thêm khách sạn."
                    )

    with tab2:

        hotels = get_dataframe("""
            SELECT
                id AS ID,
                name AS 'Khách sạn',
                address AS 'Địa chỉ',
                stars AS 'Sao',
                room_type AS 'Loại phòng',
                room_price AS 'Giá phòng',
                available_rooms AS 'Phòng trống'
            FROM hotels
            ORDER BY id DESC
        """)

        if not hotels.empty:

            display = hotels.copy()

            display["Giá phòng"] = display[
                "Giá phòng"
            ].apply(money)

            st.dataframe(
                display,
                use_container_width=True,
                hide_index=True
            )

        else:

            st.info(
                "Chưa có khách sạn."
            )


# ============================================================
# REPORT
# ============================================================

elif menu == "📊 Báo cáo":

    st.title("📊 Báo cáo & Thống kê")

    # --------------------------------------------------------
    # REVENUE
    # --------------------------------------------------------

    revenue = get_dataframe("""
        SELECT
            departure_date AS date,
            SUM(total_amount) AS revenue,
            COUNT(*) AS bookings
        FROM bookings
        WHERE booking_status != 'Đã hủy'
        GROUP BY departure_date
        ORDER BY departure_date
    """)

    if not revenue.empty:

        revenue["date"] = pd.to_datetime(
            revenue["date"]
        )

        st.subheader(
            "📈 Doanh thu theo ngày"
        )

        st.line_chart(
            revenue.set_index("date")[
                "revenue"
            ]
        )

        st.divider()

    # --------------------------------------------------------
    # TOUR PERFORMANCE
    # --------------------------------------------------------

    st.subheader(
        "🗺️ Doanh thu theo tour"
    )

    tour_report = get_dataframe("""
        SELECT
            t.name AS 'Tour',
            COUNT(b.id) AS 'Số booking',
            SUM(b.adults) AS 'Người lớn',
            SUM(b.children) AS 'Trẻ em',
            SUM(b.infants) AS 'Em bé',
            SUM(b.total_amount) AS 'Doanh thu'
        FROM bookings b
        LEFT JOIN tours t
            ON b.tour_id = t.id
        WHERE b.booking_status != 'Đã hủy'
        GROUP BY t.id
        ORDER BY SUM(b.total_amount) DESC
    """)

    if not tour_report.empty:

        display = tour_report.copy()

        display["Doanh thu"] = display[
            "Doanh thu"
        ].apply(money)

        st.dataframe(
            display,
            use_container_width=True,
            hide_index=True
        )

    else:

        st.info(
            "Chưa có dữ liệu."
        )

    # --------------------------------------------------------
    # PAYMENT STATUS
    # --------------------------------------------------------

    st.subheader(
        "💰 Tình trạng thanh toán"
    )

    payment_report = get_dataframe("""
        SELECT
            payment_status AS 'Trạng thái',
            COUNT(*) AS 'Số booking',
            SUM(total_amount) AS 'Tổng tiền',
            SUM(paid) AS 'Đã thu',
            SUM(remaining) AS 'Còn lại'
        FROM bookings
        GROUP BY payment_status
    """)

    if not payment_report.empty:

        display = payment_report.copy()

        for col in [
            "Tổng tiền",
            "Đã thu",
            "Còn lại"
        ]:

            display[col] = display[
                col
            ].apply(money)

        st.dataframe(
            display,
            use_container_width=True,
            hide_index=True
        )


# ============================================================
# ADMIN
# ============================================================

elif menu == "⚙️ Admin":

    st.title("⚙️ Quản trị hệ thống")

    st.subheader(
        "🔐 Đổi mật khẩu"
    )

    with st.form("change_password"):

        old_password = st.text_input(
            "Mật khẩu hiện tại",
            type="password"
        )

        new_password = st.text_input(
            "Mật khẩu mới",
            type="password"
        )

        confirm_password = st.text_input(
            "Nhập lại mật khẩu mới",
            type="password"
        )

        submit = st.form_submit_button(
            "🔐 ĐỔI MẬT KHẨU",
            use_container_width=True
        )

        if submit:

            current = execute_query("""
                SELECT password
                FROM users
                WHERE username = ?
            """, (
                st.session_state.username,
            ), fetch=True)

            if not current:

                st.error(
                    "Không tìm thấy tài khoản."
                )

            elif current[0]["password"] != hash_password(
                old_password
            ):

                st.error(
                    "Mật khẩu hiện tại không đúng."
                )

            elif len(new_password) < 6:

                st.error(
                    "Mật khẩu mới phải có ít nhất 6 ký tự."
                )

            elif new_password != confirm_password:

                st.error(
                    "Mật khẩu xác nhận không khớp."
                )

            else:

                execute_query("""
                    UPDATE users
                    SET password = ?
                    WHERE username = ?
                """, (
                    hash_password(new_password),
                    st.session_state.username
                ))

                st.success(
                    "Đã đổi mật khẩu thành công."
                )

    st.divider()

    st.subheader(
        "🗄️ Database"
    )

    st.write(
        f"Database hiện tại: `{DB_PATH}`"
    )

    if st.button(
        "🔄 Làm mới dữ liệu",
        use_container_width=True
    ):

        st.cache_data.clear()
        st.rerun()

    st.divider()

    st.warning(
        "Phiên bản này sử dụng SQLite để dễ triển khai "
        "trên Streamlit Cloud. Khi triển khai hệ thống "
        "nhiều nhân viên hoặc nhiều thiết bị, nên chuyển "
        "database sang MySQL/PostgreSQL."
    )


# ============================================================
# FOOTER
# ============================================================

st.sidebar.divider()

st.sidebar.caption(
    "SMART TOUR © 2026"
)
