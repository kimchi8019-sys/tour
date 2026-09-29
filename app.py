import streamlit as st
import sqlite3
import pandas as pd
from pathlib import Path
from datetime import datetime, date
import hashlib
import base64

# =========================================================
# CONFIG
# =========================================================

st.set_page_config(
    page_title="Smart Tour | Đặt tour trực tuyến",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =========================================================
# IMAGE URLS
# =========================================================

HERO_IMAGE = (
    "https://images.unsplash.com/"
    "photo-1500534623283-312aade485b7"
    "?auto=format&fit=crop&w=2000&q=85"
)

TOUR_IMAGES = {
    "Vũng Tàu": (
        "https://images.unsplash.com/"
        "photo-1559827260-dc66d52bef19"
        "?auto=format&fit=crop&w=1200&q=80"
    ),
    "Đà Lạt": (
        "https://images.unsplash.com/"
        "photo-1500534623283-312aade485b7"
        "?auto=format&fit=crop&w=1200&q=80"
    ),
    "Phú Quốc": (
        "https://images.unsplash.com/"
        "photo-1507525428034-b723cf961d3e"
        "?auto=format&fit=crop&w=1200&q=80"
    ),
    "Đà Nẵng": (
        "https://images.unsplash.com/"
        "photo-1559592413-7cec4d0cae2b"
        "?auto=format&fit=crop&w=1200&q=80"
    ),
    "Hội An": (
        "https://images.unsplash.com/"
        "photo-1528127269322-539801943592"
        "?auto=format&fit=crop&w=1200&q=80"
    ),
}

DEFAULT_TOUR_IMAGE = (
    "https://images.unsplash.com/"
    "photo-1469474968028-56623f02e42e"
    "?auto=format&fit=crop&w=1200&q=80"
)

# =========================================================
# DATABASE
# =========================================================

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

DB_PATH = DATA_DIR / "smart_tour.db"


def get_connection():
    connection = sqlite3.connect(
        DB_PATH,
        check_same_thread=False
    )
    connection.row_factory = sqlite3.Row
    return connection


db = get_connection()


def query(sql, params=(), fetch=False):
    cursor = db.cursor()
    cursor.execute(sql, params)
    db.commit()

    if fetch:
        return cursor.fetchall()

    return cursor.lastrowid


def dataframe(sql, params=()):
    return pd.read_sql_query(
        sql,
        db,
        params=params
    )


# =========================================================
# DATABASE INIT
# =========================================================

def init_database():

    # -----------------------------------------------------
    # ADMIN
    # -----------------------------------------------------

    query("""
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            full_name TEXT
        )
    """)

    # -----------------------------------------------------
    # TOURS
    # -----------------------------------------------------

    query("""
        CREATE TABLE IF NOT EXISTS tours (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            destination TEXT,
            duration TEXT,
            adult_price REAL DEFAULT 0,
            child_price REAL DEFAULT 0,
            infant_price REAL DEFAULT 0,
            image_url TEXT,
            description TEXT,
            status TEXT DEFAULT 'Đang hoạt động'
        )
    """)

    # -----------------------------------------------------
    # HOTELS
    # -----------------------------------------------------

    query("""
        CREATE TABLE IF NOT EXISTS hotels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            address TEXT,
            stars INTEGER DEFAULT 3,
            room_type TEXT,
            room_price REAL DEFAULT 0,
            available_rooms INTEGER DEFAULT 0,
            image_url TEXT,
            status TEXT DEFAULT 'Đang hoạt động'
        )
    """)

    # -----------------------------------------------------
    # CUSTOMERS
    # -----------------------------------------------------

    query("""
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            phone TEXT NOT NULL,
            email TEXT,
            birth_date TEXT,
            address TEXT,
            note TEXT,
            created_at TEXT
        )
    """)

    # -----------------------------------------------------
    # BOOKINGS
    # -----------------------------------------------------

    query("""
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            booking_code TEXT UNIQUE NOT NULL,

            customer_id INTEGER,
            tour_id INTEGER,
            hotel_id INTEGER,

            departure_date TEXT,
            departure_time TEXT,
            return_date TEXT,

            adults INTEGER DEFAULT 0,
            children INTEGER DEFAULT 0,
            infants INTEGER DEFAULT 0,

            rooms INTEGER DEFAULT 0,

            tour_total REAL DEFAULT 0,
            hotel_total REAL DEFAULT 0,
            discount REAL DEFAULT 0,
            total_amount REAL DEFAULT 0,

            deposit REAL DEFAULT 0,
            paid REAL DEFAULT 0,
            remaining REAL DEFAULT 0,

            payment_status TEXT DEFAULT 'Chưa thanh toán',
            booking_status TEXT DEFAULT 'Chờ xác nhận',

            customer_note TEXT,

            created_at TEXT
        )
    """)

    # -----------------------------------------------------
    # DEFAULT ADMIN
    # -----------------------------------------------------

    password = hashlib.sha256(
        "admin123".encode()
    ).hexdigest()

    query("""
        INSERT OR IGNORE INTO admins
        (username, password, full_name)
        VALUES (?, ?, ?)
    """, (
        "admin",
        password,
        "Quản trị viên"
    ))


# =========================================================
# SAMPLE DATA
# =========================================================

def create_sample_data():

    tours = query("""
        SELECT COUNT(*) AS total
        FROM tours
    """, fetch=True)[0]["total"]

    if tours == 0:

        sample_tours = [

            (
                "VT001",
                "Vũng Tàu - Bạch Dinh - Minh Đạm",
                "Vũng Tàu",
                "2 ngày 1 đêm",
                1490000,
                1090000,
                300000,
                TOUR_IMAGES["Vũng Tàu"],
                "Khám phá biển Vũng Tàu, Bạch Dinh và các điểm lịch sử nổi bật.",
                "Đang hoạt động"
            ),

            (
                "DL001",
                "Đà Lạt - Thành phố ngàn hoa",
                "Đà Lạt",
                "3 ngày 2 đêm",
                3290000,
                2490000,
                500000,
                TOUR_IMAGES["Đà Lạt"],
                "Hành trình khám phá Đà Lạt với khí hậu mát mẻ và nhiều điểm check-in.",
                "Đang hoạt động"
            ),

            (
                "PQ001",
                "Phú Quốc - Thiên đường biển đảo",
                "Phú Quốc",
                "3 ngày 2 đêm",
                4290000,
                3290000,
                600000,
                TOUR_IMAGES["Phú Quốc"],
                "Tận hưởng biển xanh, đảo đẹp và những trải nghiệm đặc sắc tại Phú Quốc.",
                "Đang hoạt động"
            ),

            (
                "DN001",
                "Đà Nẵng - Hội An - Bà Nà Hills",
                "Đà Nẵng",
                "4 ngày 3 đêm",
                5290000,
                3990000,
                700000,
                TOUR_IMAGES["Đà Nẵng"],
                "Khám phá Đà Nẵng, Hội An và Bà Nà Hills.",
                "Đang hoạt động"
            ),

            (
                "HA001",
                "Hội An - Phố cổ bên sông Hoài",
                "Hội An",
                "2 ngày 1 đêm",
                2190000,
                1690000,
                400000,
                TOUR_IMAGES["Hội An"],
                "Trải nghiệm vẻ đẹp cổ kính và văn hóa đặc sắc của Hội An.",
                "Đang hoạt động"
            )
        ]

        for tour in sample_tours:

            query("""
                INSERT INTO tours (
                    code,
                    name,
                    destination,
                    duration,
                    adult_price,
                    child_price,
                    infant_price,
                    image_url,
                    description,
                    status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, tour)

    hotels = query("""
        SELECT COUNT(*) AS total
        FROM hotels
    """, fetch=True)[0]["total"]

    if hotels == 0:

        sample_hotels = [

            (
                "Premier Pearl Hotel",
                "Vũng Tàu",
                4,
                "Deluxe Ocean View",
                1800000,
                20,
                "https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&w=1200&q=80",
                "Đang hoạt động"
            ),

            (
                "Seaside Resort",
                "Vũng Tàu",
                4,
                "Superior",
                1400000,
                15,
                "https://images.unsplash.com/photo-1584132967334-10e028bd69f7?auto=format&fit=crop&w=1200&q=80",
                "Đang hoạt động"
            ),

            (
                "Dalat Palace",
                "Đà Lạt",
                5,
                "Deluxe",
                2300000,
                10,
                "https://images.unsplash.com/photo-1564501049412-61c2a3083791?auto=format&fit=crop&w=1200&q=80",
                "Đang hoạt động"
            ),

            (
                "Phu Quoc Resort",
                "Phú Quốc",
                5,
                "Ocean View",
                2800000,
                12,
                "https://images.unsplash.com/photo-1540541338287-41700207dee6?auto=format&fit=crop&w=1200&q=80",
                "Đang hoạt động"
            )
        ]

        for hotel in sample_hotels:

            query("""
                INSERT INTO hotels (
                    name,
                    address,
                    stars,
                    room_type,
                    room_price,
                    available_rooms,
                    image_url,
                    status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, hotel)


init_database()
create_sample_data()


# =========================================================
# HELPERS
# =========================================================

def money(value):

    if value is None:
        value = 0

    return f"{float(value):,.0f} ₫"


def hash_password(password):

    return hashlib.sha256(
        password.encode()
    ).hexdigest()


def generate_booking_code():

    today = datetime.now().strftime("%Y%m%d")

    result = query("""
        SELECT COUNT(*) AS total
        FROM bookings
        WHERE booking_code LIKE ?
    """, (
        f"ST{today}%"
    ), fetch=True)

    number = result[0]["total"] + 1

    return f"ST{today}{number:03d}"


def calculate_price(
    tour,
    hotel_price,
    adults,
    children,
    infants,
    rooms,
    discount
):

    tour_total = (
        adults * tour["adult_price"]
        + children * tour["child_price"]
        + infants * tour["infant_price"]
    )

    hotel_total = rooms * hotel_price

    total = (
        tour_total
        + hotel_total
        - discount
    )

    if total < 0:
        total = 0

    return (
        tour_total,
        hotel_total,
        total
    )


# =========================================================
# CSS
# =========================================================

st.markdown("""
<style>

.main {
    padding-top: 1rem;
}

.hero {
    padding: 70px 50px;
    border-radius: 24px;
    background-image:
        linear-gradient(
            rgba(0,0,0,0.45),
            rgba(0,0,0,0.45)
        ),
        url("https://images.unsplash.com/photo-1500534623283-312aade485b7?auto=format&fit=crop&w=2000&q=85");
    background-size: cover;
    background-position: center;
    color: white;
    margin-bottom: 30px;
}

.hero h1 {
    font-size: 50px;
    font-weight: 800;
    margin-bottom: 10px;
}

.hero p {
    font-size: 20px;
}

.tour-card {
    border-radius: 18px;
    overflow: hidden;
    border: 1px solid #e5e7eb;
    background: white;
    margin-bottom: 20px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.06);
}

.tour-image {
    width: 100%;
    height: 210px;
    object-fit: cover;
}

.tour-content {
    padding: 18px;
}

.price {
    font-size: 22px;
    font-weight: 800;
}

.small-text {
    color: #6b7280;
}

.admin-header {
    padding: 25px;
    border-radius: 18px;
    background: linear-gradient(135deg,#0f172a,#1e3a8a);
    color: white;
    margin-bottom: 25px;
}

.booking-success {
    padding: 25px;
    border-radius: 18px;
    background: #ecfdf5;
    border: 1px solid #10b981;
}

.metric-card {
    padding: 20px;
    border-radius: 16px;
    border: 1px solid #e5e7eb;
    background: white;
}

</style>
""", unsafe_allow_html=True)


# =========================================================
# SESSION
# =========================================================

if "page" not in st.session_state:
    st.session_state.page = "home"

if "admin_logged_in" not in st.session_state:
    st.session_state.admin_logged_in = False

if "booking_success" not in st.session_state:
    st.session_state.booking_success = None


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.markdown("## ✈️ SMART TOUR")

    st.caption(
        "Đặt tour trực tuyến"
    )

    st.divider()

    if st.button(
        "🏠 Trang chủ",
        use_container_width=True
    ):
        st.session_state.page = "home"
        st.rerun()

    if st.button(
        "🗺️ Khám phá tour",
        use_container_width=True
    ):
        st.session_state.page = "tours"
        st.rerun()

    if st.button(
        "🔎 Tra cứu booking",
        use_container_width=True
    ):
        st.session_state.page = "lookup"
        st.rerun()

    st.divider()

    if st.button(
        "🔐 Admin",
        use_container_width=True
    ):
        st.session_state.page = "admin"
        st.rerun()


# =========================================================
# HOME
# =========================================================

if st.session_state.page == "home":

    st.markdown("""
    <div class="hero">

        <h1>Khám phá hành trình<br>theo cách của bạn</h1>

        <p>
        Đặt tour nhanh chóng · Chọn khách sạn ·
        Tính giá tự động
        </p>

    </div>
    """, unsafe_allow_html=True)

    st.markdown(
        "## 🌎 Những hành trình nổi bật"
    )

    tours = dataframe("""
        SELECT *
        FROM tours
        WHERE status = 'Đang hoạt động'
        ORDER BY id DESC
        LIMIT 6
    """)

    if not tours.empty:

        cols = st.columns(3)

        for index, (_, tour) in enumerate(
            tours.iterrows()
        ):

            with cols[index % 3]:

                image = (
                    tour["image_url"]
                    if tour["image_url"]
                    else DEFAULT_TOUR_IMAGE
                )

                st.markdown(
                    f"""
                    <div class="tour-card">

                        <img
                            src="{image}"
                            class="tour-image"
                        />

                        <div class="tour-content">

                            <h3>
                                {tour["name"]}
                            </h3>

                            <p class="small-text">
                                📍 {tour["destination"]}
                                · ⏱️ {tour["duration"]}
                            </p>

                            <div class="price">
                                Từ {money(tour["adult_price"])}
                            </div>

                        </div>

                    </div>
                    """,
                    unsafe_allow_html=True
                )

                if st.button(
                    "Xem & đặt tour",
                    key=f"home_tour_{tour['id']}",
                    use_container_width=True
                ):

                    st.session_state.selected_tour = int(
                        tour["id"]
                    )

                    st.session_state.page = "booking"

                    st.rerun()

    st.divider()

    st.markdown(
        "## ✨ Vì sao chọn Smart Tour?"
    )

    c1, c2, c3, c4 = st.columns(4)

    c1.markdown(
        "### 🗺️\nTour đa dạng\n\n"
        "Nhiều hành trình hấp dẫn."
    )

    c2.markdown(
        "### 💰\nGiá rõ ràng\n\n"
        "Tự động tính tổng chi phí."
    )

    c3.markdown(
        "### 🏨\nKhách sạn\n\n"
        "Lựa chọn nhiều loại phòng."
    )

    c4.markdown(
        "### 📩\nĐặt nhanh\n\n"
        "Nhận mã booking ngay."
    )

    st.divider()

    st.info(
        "💡 Bạn có thể vào **Khám phá tour** để xem toàn bộ chương trình."
    )


# =========================================================
# TOUR LIST
# =========================================================

elif st.session_state.page == "tours":

    st.title("🗺️ Khám phá tour")

    tours = dataframe("""
        SELECT *
        FROM tours
        WHERE status = 'Đang hoạt động'
        ORDER BY id DESC
    """)

    search = st.text_input(
        "🔎 Tìm tour hoặc điểm đến",
        placeholder="Ví dụ: Vũng Tàu, Đà Lạt..."
    )

    if search:

        tours = tours[
            tours["name"].str.contains(
                search,
                case=False,
                na=False
            )
            |
            tours["destination"].str.contains(
                search,
                case=False,
                na=False
            )
        ]

    if tours.empty:

        st.warning(
            "Không tìm thấy tour."
        )

    else:

        for start in range(
            0,
            len(tours),
            3
        ):

            cols = st.columns(3)

            for column_index, (_, tour) in enumerate(
                tours.iloc[start:start+3].iterrows()
            ):

                with cols[column_index]:

                    image = (
                        tour["image_url"]
                        if tour["image_url"]
                        else DEFAULT_TOUR_IMAGE
                    )

                    st.image(
                        image,
                        use_container_width=True
                    )

                    st.subheader(
                        tour["name"]
                    )

                    st.caption(
                        f"📍 {tour['destination']}  "
                        f"·  ⏱️ {tour['duration']}"
                    )

                    st.write(
                        tour["description"]
                    )

                    st.markdown(
                        f"### {money(tour['adult_price'])}"
                    )

                    st.caption(
                        f"Người lớn · "
                        f"Trẻ em {money(tour['child_price'])}"
                    )

                    if st.button(
                        "✈️ Đặt tour này",
                        key=f"tour_{tour['id']}",
                        use_container_width=True
                    ):

                        st.session_state.selected_tour = int(
                            tour["id"]
                        )

                        st.session_state.page = "booking"

                        st.rerun()


# =========================================================
# BOOKING PAGE
# =========================================================

elif st.session_state.page == "booking":

    st.title("✈️ Đặt tour")

    tour_id = st.session_state.get(
        "selected_tour"
    )

    if not tour_id:

        st.warning(
            "Bạn chưa chọn tour."
        )

        if st.button(
            "← Quay lại danh sách tour"
        ):

            st.session_state.page = "tours"
            st.rerun()

        st.stop()

    tour_result = dataframe("""
        SELECT *
        FROM tours
        WHERE id = ?
    """, (tour_id,))

    if tour_result.empty:

        st.error(
            "Tour không tồn tại."
        )

        st.stop()

    tour = tour_result.iloc[0]

    st.image(
        tour["image_url"],
        use_container_width=True
    )

    st.markdown(
        f"# {tour['name']}"
    )

    st.caption(
        f"📍 {tour['destination']} "
        f"· ⏱️ {tour['duration']}"
    )

    st.write(
        tour["description"]
    )

    st.divider()

    # -----------------------------------------------------
    # FORM
    # -----------------------------------------------------

    st.subheader(
        "1️⃣ Thông tin hành trình"
    )

    c1, c2, c3 = st.columns(3)

    with c1:

        departure_date = st.date_input(
            "Ngày khởi hành",
            min_value=date.today(),
            value=date.today()
        )

    with c2:

        departure_time = st.time_input(
            "Giờ khởi hành"
        )

    with c3:

        return_date = st.date_input(
            "Ngày kết thúc",
            min_value=departure_date,
            value=departure_date
        )

    st.subheader(
        "2️⃣ Số lượng hành khách"
    )

    c1, c2, c3 = st.columns(3)

    with c1:

        adults = st.number_input(
            "👨 Người lớn",
            min_value=1,
            value=2,
            step=1
        )

    with c2:

        children = st.number_input(
            "🧒 Trẻ em",
            min_value=0,
            value=0,
            step=1
        )

    with c3:

        infants = st.number_input(
            "👶 Em bé",
            min_value=0,
            value=0,
            step=1
        )

    st.subheader(
        "3️⃣ Khách sạn"
    )

    hotels = dataframe("""
        SELECT *
        FROM hotels
        WHERE status = 'Đang hoạt động'
        ORDER BY name
    """)

    hotel_id = None
    hotel_price = 0
    rooms = 0

    if not hotels.empty:

        hotel_names = [
            "Không chọn khách sạn"
        ] + [
            f"{row['name']} | "
            f"{row['room_type']} | "
            f"{money(row['room_price'])}/phòng"
            for _, row in hotels.iterrows()
        ]

        selected_hotel = st.selectbox(
            "Chọn khách sạn",
            hotel_names
        )

        if selected_hotel != "Không chọn khách sạn":

            hotel_index = (
                hotel_names.index(
                    selected_hotel
                ) - 1
            )

            selected_hotel_row = hotels.iloc[
                hotel_index
            ]

            hotel_id = int(
                selected_hotel_row["id"]
            )

            hotel_price = float(
                selected_hotel_row["room_price"]
            )

            available_rooms = int(
                selected_hotel_row["available_rooms"]
            )

            rooms = st.number_input(
                f"Số phòng "
                f"(còn {available_rooms} phòng)",
                min_value=1,
                max_value=max(
                    available_rooms,
                    1
                ),
                value=1,
                step=1
            )

    st.subheader(
        "4️⃣ Thông tin người đặt"
    )

    with st.form("customer_booking_form"):

        c1, c2 = st.columns(2)

        with c1:

            full_name = st.text_input(
                "Họ và tên *"
            )

            phone = st.text_input(
                "Số điện thoại *"
            )

            email = st.text_input(
                "Email"
            )

        with c2:

            birth_date = st.date_input(
                "Ngày sinh",
                value=date(2000, 1, 1)
            )

            address = st.text_input(
                "Địa chỉ"
            )

        note = st.text_area(
            "Yêu cầu / ghi chú"
        )

        # -------------------------------------------------
        # PRICE
        # -------------------------------------------------

        tour_total, hotel_total, total = calculate_price(
            tour,
            hotel_price,
            adults,
            children,
            infants,
            rooms,
            0
        )

        st.divider()

        st.markdown("### 💰 Chi phí dự kiến")

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "Tour",
            money(tour_total)
        )

        c2.metric(
            "Khách sạn",
            money(hotel_total)
        )

        c3.metric(
            "TỔNG CỘNG",
            money(total)
        )

        submit = st.form_submit_button(
            "✈️ XÁC NHẬN ĐẶT TOUR",
            use_container_width=True
        )

        if submit:

            if not full_name.strip():

                st.error(
                    "Vui lòng nhập họ tên."
                )

            elif not phone.strip():

                st.error(
                    "Vui lòng nhập số điện thoại."
                )

            else:

                # -----------------------------------------
                # CREATE CUSTOMER
                # -----------------------------------------

                customer_id = query("""
                    INSERT INTO customers (
                        full_name,
                        phone,
                        email,
                        birth_date,
                        address,
                        note,
                        created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    full_name,
                    phone,
                    email,
                    str(birth_date),
                    address,
                    note,
                    datetime.now().isoformat()
                ))

                # -----------------------------------------
                # BOOKING CODE
                # -----------------------------------------

                booking_code = generate_booking_code()

                # -----------------------------------------
                # CREATE BOOKING
                # -----------------------------------------

                query("""
                    INSERT INTO bookings (
                        booking_code,
                        customer_id,
                        tour_id,
                        hotel_id,
                        departure_date,
                        departure_time,
                        return_date,
                        adults,
                        children,
                        infants,
                        rooms,
                        tour_total,
                        hotel_total,
                        discount,
                        total_amount,
                        deposit,
                        paid,
                        remaining,
                        payment_status,
                        booking_status,
                        customer_note,
                        created_at
                    )
                    VALUES (
                        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                    )
                """, (
                    booking_code,
                    customer_id,
                    tour_id,
                    hotel_id,
                    str(departure_date),
                    str(departure_time),
                    str(return_date),
                    adults,
                    children,
                    infants,
                    rooms,
                    tour_total,
                    hotel_total,
                    0,
                    total,
                    0,
                    0,
                    total,
                    "Chưa thanh toán",
                    "Chờ xác nhận",
                    note,
                    datetime.now().isoformat()
                ))

                # -----------------------------------------
                # REDUCE HOTEL INVENTORY
                # -----------------------------------------

                if hotel_id and rooms > 0:

                    query("""
                        UPDATE hotels
                        SET available_rooms =
                            available_rooms - ?
                        WHERE id = ?
                    """, (
                        rooms,
                        hotel_id
                    ))

                st.session_state.booking_success = {
                    "code": booking_code,
                    "name": full_name,
                    "tour": tour["name"],
                    "date": str(departure_date),
                    "total": total
                }

                st.session_state.page = "success"

                st.rerun()


# =========================================================
# BOOKING SUCCESS
# =========================================================

elif st.session_state.page == "success":

    booking = st.session_state.booking_success

    if booking:

        st.markdown(
            f"""
            <div class="booking-success">

                <h1>🎉 Đặt tour thành công!</h1>

                <p>
                Cảm ơn <b>{booking["name"]}</b>
                đã đặt tour cùng Smart Tour.
                </p>

                <h2>
                Mã booking: {booking["code"]}
                </h2>

                <p>
                Tour: <b>{booking["tour"]}</b>
                </p>

                <p>
                Ngày khởi hành:
                <b>{booking["date"]}</b>
                </p>

                <p>
                Tổng tiền:
                <b>{money(booking["total"])}</b>
                </p>

            </div>
            """,
            unsafe_allow_html=True
        )

        st.warning(
            "Booking đang ở trạng thái "
            "**Chờ xác nhận**. Nhân viên Smart Tour "
            "sẽ kiểm tra và xác nhận thông tin."
        )

        if st.button(
            "🔎 Tra cứu booking",
            use_container_width=True
        ):

            st.session_state.page = "lookup"
            st.rerun()

        if st.button(
            "🏠 Về trang chủ",
            use_container_width=True
        ):

            st.session_state.page = "home"
            st.rerun()


# =========================================================
# LOOKUP BOOKING
# =========================================================

elif st.session_state.page == "lookup":

    st.title("🔎 Tra cứu booking")

    st.write(
        "Nhập mã booking được cung cấp sau khi đặt tour."
    )

    code = st.text_input(
        "Mã booking",
        placeholder="VD: ST20260929001"
    )

    if st.button(
        "🔎 TRA CỨU",
        use_container_width=True
    ):

        result = dataframe("""
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
        """, (
            code.strip()
        ))

        if result.empty:

            st.error(
                "Không tìm thấy booking."
            )

        else:

            booking = result.iloc[0]

            st.success(
                "Đã tìm thấy booking."
            )

            c1, c2, c3 = st.columns(3)

            c1.metric(
                "Mã booking",
                booking["booking_code"]
            )

            c2.metric(
                "Trạng thái",
                booking["booking_status"]
            )

            c3.metric(
                "Tổng tiền",
                money(booking["total_amount"])
            )

            st.divider()

            st.write(
                f"👤 **Khách hàng:** "
                f"{booking['full_name']}"
            )

            st.write(
                f"📞 **Điện thoại:** "
                f"{booking['phone']}"
            )

            st.write(
                f"✈️ **Tour:** "
                f"{booking['tour_name']}"
            )

            st.write(
                f"📍 **Điểm đến:** "
                f"{booking['destination']}"
            )

            st.write(
                f"📅 **Ngày đi:** "
                f"{booking['departure_date']}"
            )

            st.write(
                f"⏰ **Giờ đi:** "
                f"{booking['departure_time']}"
            )

            st.write(
                f"🏨 **Khách sạn:** "
                f"{booking['hotel_name'] or 'Không chọn'}"
            )

            st.write(
                f"👨 **Người lớn:** "
                f"{booking['adults']}"
            )

            st.write(
                f"🧒 **Trẻ em:** "
                f"{booking['children']}"
            )

            st.write(
                f"👶 **Em bé:** "
                f"{booking['infants']}"
            )

            st.write(
                f"💰 **Tổng tiền:** "
                f"{money(booking['total_amount'])}"
            )

            st.write(
                f"💳 **Thanh toán:** "
                f"{booking['payment_status']}"
            )


# =========================================================
# ADMIN LOGIN
# =========================================================

elif st.session_state.page == "admin":

    if not st.session_state.admin_logged_in:

        st.title("🔐 Đăng nhập Admin")

        st.info(
            "Khu vực này chỉ dành cho quản trị viên."
        )

        with st.form("admin_login"):

            username = st.text_input(
                "Tên đăng nhập"
            )

            password = st.text_input(
                "Mật khẩu",
                type="password"
            )

            submit = st.form_submit_button(
                "🔐 ĐĂNG NHẬP",
                use_container_width=True
            )

            if submit:

                result = query("""
                    SELECT *
                    FROM admins
                    WHERE username = ?
                    AND password = ?
                """, (
                    username,
                    hash_password(password)
                ), fetch=True)

                if result:

                    st.session_state.admin_logged_in = True

                    st.rerun()

                else:

                    st.error(
                        "Sai tên đăng nhập hoặc mật khẩu."
                    )

        st.caption(
            "Tài khoản lần đầu: admin / admin123"
        )

    else:

        # =================================================
        # ADMIN DASHBOARD
        # =================================================

        st.markdown(
            """
            <div class="admin-header">

                <h1>📊 Smart Tour Admin</h1>

                <p>
                Quản lý booking · Khách hàng · Tour ·
                Khách sạn · Doanh thu
                </p>

            </div>
            """,
            unsafe_allow_html=True
        )

        # -------------------------------------------------
        # METRICS
        # -------------------------------------------------

        total_bookings = query("""
            SELECT COUNT(*) AS total
            FROM bookings
        """, fetch=True)[0]["total"]

        pending = query("""
            SELECT COUNT(*) AS total
            FROM bookings
            WHERE booking_status = 'Chờ xác nhận'
        """, fetch=True)[0]["total"]

        confirmed = query("""
            SELECT COUNT(*) AS total
            FROM bookings
            WHERE booking_status = 'Đã xác nhận'
        """, fetch=True)[0]["total"]

        revenue = query("""
            SELECT COALESCE(
                SUM(total_amount), 0
            ) AS total
            FROM bookings
            WHERE booking_status != 'Đã hủy'
        """, fetch=True)[0]["total"]

        customers = query("""
            SELECT COUNT(*) AS total
            FROM customers
        """, fetch=True)[0]["total"]

        c1, c2, c3, c4, c5 = st.columns(5)

        c1.metric(
            "📋 Booking",
            total_bookings
        )

        c2.metric(
            "⏳ Chờ xử lý",
            pending
        )

        c3.metric(
            "✅ Đã xác nhận",
            confirmed
        )

        c4.metric(
            "👥 Khách hàng",
            customers
        )

        c5.metric(
            "💰 Doanh thu",
            money(revenue)
        )

        st.divider()

        # -------------------------------------------------
        # ADMIN TABS
        # -------------------------------------------------

        admin_tabs = st.tabs([
            "📋 Booking",
            "📊 Thống kê",
            "🗺️ Tour",
            "🏨 Khách sạn",
            "👥 Khách hàng"
        ])

        # =================================================
        # BOOKINGS
        # =================================================

        with admin_tabs[0]:

            st.subheader(
                "📋 Danh sách booking khách hàng"
            )

            status = st.multiselect(
                "Lọc trạng thái",
                [
                    "Chờ xác nhận",
                    "Đã xác nhận",
                    "Đang thực hiện",
                    "Hoàn thành",
                    "Đã hủy"
                ]
            )

            booking_query = """
                SELECT
                    b.id,
                    b.booking_code AS 'Mã booking',
                    c.full_name AS 'Khách hàng',
                    c.phone AS 'Điện thoại',
                    c.email AS 'Email',
                    t.name AS 'Tour',
                    b.departure_date AS 'Ngày đi',
                    b.departure_time AS 'Giờ đi',
                    b.adults AS 'NL',
                    b.children AS 'TE',
                    b.infants AS 'EB',
                    h.name AS 'Khách sạn',
                    b.rooms AS 'Phòng',
                    b.total_amount AS 'Tổng tiền',
                    b.paid AS 'Đã thu',
                    b.remaining AS 'Còn lại',
                    b.payment_status AS 'Thanh toán',
                    b.booking_status AS 'Trạng thái',
                    b.customer_note AS 'Ghi chú',
                    b.created_at AS 'Thời gian đặt'
                FROM bookings b

                LEFT JOIN customers c
                    ON b.customer_id = c.id

                LEFT JOIN tours t
                    ON b.tour_id = t.id

                LEFT JOIN hotels h
                    ON b.hotel_id = h.id

                WHERE 1=1
            """

            params = []

            if status:

                placeholders = ",".join(
                    ["?"] * len(status)
                )

                booking_query += f"""
                    AND b.booking_status
                    IN ({placeholders})
                """

                params.extend(status)

            booking_query += """
                ORDER BY b.id DESC
            """

            bookings = dataframe(
                booking_query,
                params
            )

            if bookings.empty:

                st.info(
                    "Chưa có booking."
                )

            else:

                display = bookings.copy()

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

                csv = bookings.to_csv(
                    index=False
                ).encode("utf-8-sig")

                st.download_button(
                    "⬇️ Xuất danh sách booking",
                    csv,
                    "smart_tour_bookings.csv",
                    "text/csv",
                    use_container_width=True
                )

                st.divider()

                st.subheader(
                    "🔧 Cập nhật booking"
                )

                selected_code = st.selectbox(
                    "Chọn booking",
                    bookings["Mã booking"].tolist()
                )

                selected = bookings[
                    bookings["Mã booking"]
                    == selected_code
                ].iloc[0]

                new_status = st.selectbox(
                    "Trạng thái mới",
                    [
                        "Chờ xác nhận",
                        "Đã xác nhận",
                        "Đang thực hiện",
                        "Hoàn thành",
                        "Đã hủy"
                    ],
                    index=[
                        "Chờ xác nhận",
                        "Đã xác nhận",
                        "Đang thực hiện",
                        "Hoàn thành",
                        "Đã hủy"
                    ].index(
                        selected["Trạng thái"]
                    )
                )

                paid_amount = st.number_input(
                    "Số tiền khách đã thanh toán",
                    min_value=0.0,
                    value=float(
                        selected["Đã thu"]
                        if pd.notna(
                            selected["Đã thu"]
                        )
                        else 0
                    ),
                    step=100000.0
                )

                update = st.button(
                    "💾 CẬP NHẬT BOOKING",
                    use_container_width=True
                )

                if update:

                    booking_id = int(
                        selected["id"]
                    )

                    total_amount = float(
                        selected["Tổng tiền"]
                    )

                    remaining = max(
                        total_amount - paid_amount,
                        0
                    )

                    if paid_amount <= 0:

                        payment_status = (
                            "Chưa thanh toán"
                        )

                    elif paid_amount < total_amount:

                        payment_status = "Đã cọc"

                    else:

                        payment_status = (
                            "Đã thanh toán"
                        )

                    query("""
                        UPDATE bookings
                        SET
                            booking_status = ?,
                            paid = ?,
                            remaining = ?,
                            payment_status = ?
                        WHERE id = ?
                    """, (
                        new_status,
                        paid_amount,
                        remaining,
                        payment_status,
                        booking_id
                    ))

                    st.success(
                        "Đã cập nhật booking."
                    )

                    st.rerun()

        # =================================================
        # STATISTICS
        # =================================================

        with admin_tabs[1]:

            st.subheader(
                "📊 Thống kê kinh doanh"
            )

            col1, col2 = st.columns(2)

            with col1:

                status_report = dataframe("""
                    SELECT
                        booking_status AS 'Trạng thái',
                        COUNT(*) AS 'Số booking'
                    FROM bookings
                    GROUP BY booking_status
                """)

                if not status_report.empty:

                    st.markdown(
                        "### Booking theo trạng thái"
                    )

                    st.bar_chart(
                        status_report.set_index(
                            "Trạng thái"
                        )
                    )

            with col2:

                tour_report = dataframe("""
                    SELECT
                        t.name AS 'Tour',
                        COUNT(b.id) AS 'Booking'
                    FROM bookings b
                    JOIN tours t
                        ON b.tour_id = t.id
                    GROUP BY t.id
                    ORDER BY Booking DESC
                """)

                if not tour_report.empty:

                    st.markdown(
                        "### Tour được đặt"
                    )

                    st.bar_chart(
                        tour_report.set_index(
                            "Tour"
                        )
                    )

            st.divider()

            st.subheader(
                "💰 Doanh thu theo tour"
            )

            revenue_report = dataframe("""
                SELECT
                    t.name AS 'Tour',
                    COUNT(b.id) AS 'Số booking',
                    SUM(b.total_amount) AS 'Doanh thu',
                    SUM(b.paid) AS 'Đã thu',
                    SUM(b.remaining) AS 'Còn lại'
                FROM bookings b
                JOIN tours t
                    ON b.tour_id = t.id
                WHERE b.booking_status != 'Đã hủy'
                GROUP BY t.id
                ORDER BY SUM(b.total_amount) DESC
            """)

            if not revenue_report.empty:

                display = revenue_report.copy()

                for col in [
                    "Doanh thu",
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

        # =================================================
        # TOUR MANAGEMENT
        # =================================================

        with admin_tabs[2]:

            st.subheader(
                "🗺️ Quản lý tour"
            )

            tours = dataframe("""
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

            st.divider()

            st.subheader(
                "➕ Thêm tour"
            )

            with st.form("admin_add_tour"):

                c1, c2 = st.columns(2)

                with c1:

                    code = st.text_input(
                        "Mã tour"
                    )

                    name = st.text_input(
                        "Tên tour"
                    )

                    destination = st.text_input(
                        "Điểm đến"
                    )

                    duration = st.text_input(
                        "Thời lượng"
                    )

                with c2:

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

                    image_url = st.text_input(
                        "URL hình ảnh"
                    )

                description = st.text_area(
                    "Mô tả"
                )

                submit = st.form_submit_button(
                    "💾 THÊM TOUR",
                    use_container_width=True
                )

                if submit:

                    try:

                        query("""
                            INSERT INTO tours (
                                code,
                                name,
                                destination,
                                duration,
                                adult_price,
                                child_price,
                                infant_price,
                                image_url,
                                description
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
                            image_url,
                            description
                        ))

                        st.success(
                            "Đã thêm tour."
                        )

                        st.rerun()

                    except sqlite3.IntegrityError:

                        st.error(
                            "Mã tour đã tồn tại."
                        )

        # =================================================
        # HOTEL MANAGEMENT
        # =================================================

        with admin_tabs[3]:

            st.subheader(
                "🏨 Quản lý khách sạn"
            )

            hotels = dataframe("""
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

            st.divider()

            st.subheader(
                "➕ Thêm khách sạn"
            )

            with st.form("admin_add_hotel"):

                c1, c2 = st.columns(2)

                with c1:

                    name = st.text_input(
                        "Tên khách sạn"
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

                with c2:

                    room_type = st.text_input(
                        "Loại phòng"
                    )

                    room_price = st.number_input(
                        "Giá phòng",
                        min_value=0.0,
                        step=100000.0
                    )

                    available_rooms = st.number_input(
                        "Số phòng",
                        min_value=0,
                        value=10
                    )

                image_url = st.text_input(
                    "URL hình ảnh khách sạn"
                )

                submit = st.form_submit_button(
                    "💾 THÊM KHÁCH SẠN",
                    use_container_width=True
                )

                if submit:

                    query("""
                        INSERT INTO hotels (
                            name,
                            address,
                            stars,
                            room_type,
                            room_price,
                            available_rooms,
                            image_url
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        name,
                        address,
                        stars,
                        room_type,
                        room_price,
                        available_rooms,
                        image_url
                    ))

                    st.success(
                        "Đã thêm khách sạn."
                    )

                    st.rerun()

        # =================================================
        # CUSTOMERS
        # =================================================

        with admin_tabs[4]:

            st.subheader(
                "👥 Danh sách khách hàng"
            )

            customers = dataframe("""
                SELECT
                    c.id AS ID,
                    c.full_name AS 'Họ tên',
                    c.phone AS 'Điện thoại',
                    c.email AS 'Email',
                    c.birth_date AS 'Ngày sinh',
                    c.address AS 'Địa chỉ',
                    c.created_at AS 'Ngày tạo'
                FROM customers c
                ORDER BY c.id DESC
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

        st.divider()

        if st.button(
            "🚪 Đăng xuất Admin",
            use_container_width=True
        ):

            st.session_state.admin_logged_in = False
            st.session_state.page = "home"

            st.rerun()


# =========================================================
# FOOTER
# =========================================================

st.markdown(
    """
    <br>
    <hr>
    <center>
        <small>
        ✈️ SMART TOUR · Đặt tour trực tuyến
        </small>
    </center>
    """,
    unsafe_allow_html=True
)
