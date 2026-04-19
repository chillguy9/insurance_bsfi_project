import streamlit as st
import requests
import psycopg2
import bcrypt
import os
from datetime import datetime
from psycopg2.extras import RealDictCursor
import json
import google.generativeai as genai
from dotenv import load_dotenv  

# ============================================================================
# CONFIG & SETUP
# ============================================================================

# ============================================================================

# LOAD ENV VARIABLES

# ============================================================================

load_dotenv()  # loads from .env in local, ignored in production

# ============================================================================

# CONFIG (NO HARDCODED SECRETS)

# ============================================================================




API_URL = st.secrets.get("API_URL", os.getenv("API_URL"))
DATABASE_URL = st.secrets.get("DATABASE_URL", os.getenv("DATABASE_URL"))
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY"))

# ============================================================================

# VALIDATION (FAIL FAST - VERY IMPORTANT)

# ============================================================================

if not API_URL:

    raise ValueError("❌ API_URL is missing. Set it in environment variables.")

if not DATABASE_URL:

    raise ValueError("❌ DATABASE_URL is missing. Set it in environment variables.")

if not GEMINI_API_KEY:

    raise ValueError("❌ GEMINI_API_KEY is missing. Set it in environment variables.")

# ============================================================================

# GEMINI CLIENT SETUP

# ============================================================================
genai.configure(api_key=GEMINI_API_KEY)
model= genai.GenerativeModel("gemini-1.5-flash")

st.set_page_config(
    page_title="Insurance Price Predictor",
    page_icon="💰",
    layout="wide"
)

# CITY TO REGION MAPPING
CITY_TO_REGION = {
    # Northeast
    "boston": "northeast", "new york": "northeast", "philadelphia": "northeast",
    "hartford": "northeast", "providence": "northeast", "albany": "northeast",
    "buffalo": "northeast", "pittsburgh": "northeast", "baltimore": "northeast",
    "washington dc": "northeast", "newark": "northeast", "cambridge": "northeast",
    # Northwest
    "seattle": "northwest", "portland": "northwest", "spokane": "northwest",
    "boise": "northwest", "salem": "northwest", "olympia": "northwest",
    "tacoma": "northwest", "vancouver": "northwest", "eugene": "northwest",
    "bend": "northwest", "yakima": "northwest", "wenatchee": "northwest",
    # Southeast
    "miami": "southeast","atlanta": "southeast", "charlotte": "southeast",
    "orlando": "southeast", "tampa": "southeast", "jacksonville": "southeast",
    "nashville": "southeast", "memphis": "southeast", "birmingham": "southeast",
    "raleigh": "southeast", "greensboro": "southeast", "durham": "southeast",
    # Southwest
    "los angeles": "southwest", "phoenix": "southwest", "las vegas": "southwest",
    "albuquerque": "southwest", "tucson": "southwest", "denver": "southwest",
    "salt lake city": "southwest", "san diego": "southwest", "san jose": "southwest",
    "fresno": "southwest", "sacramento": "southwest", "colorado springs": "southwest"
}

# ============================================================================
# DATABASE FUNCTIONS
# ============================================================================

def connect_db():
    """Create a NEW database connection (no caching)"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except Exception as e:
        st.error(f"❌ Database Connection Error: {e}")
        return None


def init_database():
    """Initialize database tables if they don't exist"""
    conn = connect_db()
    if not conn:
        return False
    
    try:
        with conn.cursor() as cur:
            # Create users table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    name TEXT,
                    email TEXT UNIQUE,
                    password_hash TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Create predictions table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS predictions (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    age INTEGER,
                    sex TEXT,
                    bmi FLOAT,
                    children INTEGER,
                    smoker TEXT,
                    region TEXT,
                    city TEXT,
                    height_cm FLOAT,
                    weight_kg FLOAT,
                    charges FLOAT,
                    category TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
        
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        st.error(f"❌ Database Init Error: {e}")
        return False
    finally:
        conn.close()


def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(password: str, password_hash: str) -> bool:
    """Verify password against hash"""
    return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))


def create_user(name: str, email: str, password: str) -> dict:
    """Create new user account with proper connection handling"""
    conn = connect_db()
    if not conn:
        return {"success": False, "message": "Database connection failed"}
    
    try:
        password_hash = hash_password(password)
        
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO users (name, email, password_hash)
                VALUES (%s, %s, %s)
                RETURNING id, email, name;
                """,
                (name, email, password_hash)
            )
            result = cur.fetchone()
        
        conn.commit()
        
        return {
            "success": True,
            "message": "User created successfully",
            "user_id": result[0],
            "email": result[1]
        }
    
    except psycopg2.IntegrityError:
        conn.rollback()
        return {"success": False, "message": "Email already registered"}
    
    except Exception as e:
        conn.rollback()
        return {"success": False, "message": f"Error: {str(e)}"}
    
    finally:
        conn.close()


def login_user(email: str, password: str) -> dict:
    """Verify user credentials with proper connection handling"""
    conn = connect_db()
    if not conn:
        return {"success": False, "message": "Database connection failed"}
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT id, name, email, password_hash
                FROM users
                WHERE email = %s;
                """,
                (email,)
            )
            user = cur.fetchone()
        
        if not user:
            return {"success": False, "message": "Email not found"}
        
        if not verify_password(password, user['password_hash']):
            return {"success": False, "message": "Incorrect password"}
        
        return {
            "success": True,
            "message": "Login successful",
            "user_id": user['id'],
            "name": user['name'],
            "email": user['email']
        }
    
    except Exception as e:
        return {"success": False, "message": f"Error: {str(e)}"}
    
    finally:
        conn.close()


def insert_prediction(user_id: int, prediction_data: dict, result: dict) -> dict:
    """Store prediction in database with proper connection handling"""
    conn = connect_db()
    if not conn:
        return {"success": False, "message": "Database connection failed"}
    
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO predictions 
                (user_id, age, sex, bmi, children, smoker, region, city, 
                 height_cm, weight_kg, charges, category)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id;
                """,
                (
                    user_id,
                    prediction_data['age'],
                    prediction_data['sex'],
                    prediction_data['bmi'],
                    prediction_data['children'],
                    prediction_data['smoker'],
                    prediction_data['region'],
                    prediction_data.get('city', ''),
                    prediction_data.get('height', 0),
                    prediction_data.get('weight', 0),
                    result['charges'],
                    result['category']
                )
            )
            prediction_id = cur.fetchone()[0]
        
        conn.commit()
        return {"success": True, "prediction_id": prediction_id}
    
    except Exception as e:
        conn.rollback()
        return {"success": False, "message": f"Error: {str(e)}"}
    
    finally:
        conn.close()


def get_user_predictions(user_id: int) -> list:
    """Fetch all predictions for a user with proper connection handling"""
    conn = connect_db()
    if not conn:
        return []
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT id, age, sex, bmi, children, smoker, region, city,
                       height_cm, weight_kg, charges, category, created_at
                FROM predictions
                WHERE user_id = %s
                ORDER BY created_at DESC;
                """,
                (user_id,)
            )
            predictions = cur.fetchall()
        
        return [dict(p) for p in predictions]
    
    except Exception as e:
        st.error(f"Error fetching predictions: {e}")
        return []
    
    finally:
        conn.close()


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_region_from_city(city: str) -> str:
    """Get region from city name"""
    city_lower = city.lower().strip()
    return CITY_TO_REGION.get(city_lower, "southeast")


def calculate_age(dob) -> int:
    """Calculate age from date of birth"""
    today = datetime.today()
    age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    return age


def calculate_bmi(height: float, weight: float) -> float:
    """Calculate BMI (height in cm, weight in kg)"""
    height_m = height / 100
    return round(weight / (height_m ** 2), 2)


def get_insurance_tips(data: dict) -> list:
    """Generate personalized insurance tips"""
    tips = []
    if data.get("smoker") == "yes":
        tips.append("🚭 Quit smoking to significantly reduce your insurance premiums.")
    if data.get("bmi", 0) > 30:
        tips.append("⚖️ Maintain a healthy BMI (under 30) through diet and exercise.")
    if data.get("age", 0) > 50:
        tips.append("🏃‍♂️ Regular exercise and healthy lifestyle can help lower rates.")
    if data.get("children", 0) > 2:
        tips.append("👨‍👩‍👧‍👦 Consider family plans or shop around for better rates.")
    tips.append("💡 Compare quotes from multiple insurers annually.")
    tips.append("🏥 Preventive care visits can sometimes qualify you for discounts.")
    return tips


def generate_recommendation(data: dict) -> dict:

    if not GEMINI_API_KEY:

        return {"error": "Gemini API key not configured"}

    prompt = f"""

    Give insurance recommendation in JSON.

    Age: {data['age']}

    BMI: {data['bmi']}

    Smoker: {data['smoker']}

    Charges: {data['charges']}

    Format:

    {{

      "risk_level": "",

      "tips": ["", "", ""],

      "plans": [

        {{"name": "", "reason": ""}},

        {{"name": "", "reason": ""}},

        {{"name": "", "reason": ""}}

      ]

    }}

    """

    try:

        response = model.generate_content(prompt)

        text = response.text

        result = json.loads(text)

       
        if not all(k in result for k in ["risk_level", "tips", "plans"]):

            raise ValueError("Invalid response structure")

        if len(result["tips"]) != 3 or len(result["plans"]) != 3:

            raise ValueError("Expected exactly 3 tips and 3 plans")

        return result

    except Exception as e:

        return {"error": str(e)}
# ============================================================================
# CUSTOM STYLING
# ============================================================================

st.markdown("""
    <style>
        .main {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        .title {
            text-align: center;
            font-size: 48px;
            font-weight: bold;
            color: #ffffff;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
            margin-bottom: 10px;
        }
        .subtitle {
            text-align: center;
            font-size: 18px;
            color: #e0e7ff;
            margin-bottom: 30px;
        }
        .form-container {
            background: rgba(15, 23, 42, 0.95) !important;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.3);
            margin: 20px 0;
            border: 1px solid rgba(100, 116, 139, 0.35);
        }
        .stForm {
            background: rgba(15, 23, 42, 0.95) !important;
            border: 1px solid rgba(100, 116, 139, 0.35) !important;
            border-radius: 15px !important;
            box-shadow: 0 8px 32px rgba(0,0,0,0.3) !important;
            padding: 20px !important;
        }
        .stForm > div {
            background: transparent !important;
        }
        .result-card {
            background: linear-gradient(135deg, #1f2937, #111827);
            padding: 30px;
            border-radius: 15px;
            text-align: center;
            margin-top: 25px;
            box-shadow: 0px 4px 20px rgba(0,0,0,0.4);
            color: white;
        }
        .result-title {
            font-size: 24px;
            color: #9ca3af;
            margin-bottom: 15px;
        }
        .result-amount {
            font-size: 48px;
            font-weight: bold;
            color: #22c55e;
            margin: 15px 0;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
        }
        .result-category {
            font-size: 18px;
            color: #e5e7eb;
        }
        .tips-section {
            background: linear-gradient(135deg, #0f172a, #111827);
            padding: 22px;
            border-radius: 16px;
            margin-top: 20px;
            border: 1px solid rgba(148, 163, 184, 0.2);
            color: #e2e8f0;
        }
        .tip-item {
            background: rgba(14, 165, 233, 0.12);
            padding: 14px;
            border-radius: 10px;
            margin: 8px 0;
            border-left: 4px solid #38bdf8;
            color: #e2e8f0;
            box-shadow: 0 4px 18px rgba(15, 23, 42, 0.18);
        }
        .sidebar-card {
            background: rgba(15, 23, 42, 0.9);
            border: 1px solid rgba(148, 163, 184, 0.2);
            border-radius: 14px;
            padding: 16px;
            margin-bottom: 12px;
            color: #e2e8f0;
        }
        .sidebar-card strong {
            color: #ffffff;
        }
        .auth-container {
            background: rgba(15, 23, 42, 0.95);
            padding: 30px;
            border-radius: 15px;
            border: 1px solid rgba(100, 116, 139, 0.35);
            max-width: 500px;
            margin: 50px auto;
        }
    </style>
""", unsafe_allow_html=True)

# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_id = None
    st.session_state.user_name = None
    st.session_state.user_email = None

# Initialize database on first run
init_database()

# ============================================================================
# AUTHENTICATION UI (SIDEBAR)
# ============================================================================

with st.sidebar:
    st.markdown("---")
    
    if not st.session_state.logged_in:
        st.subheader("🔐 Authentication")
        
        auth_mode = st.radio("Choose action:", ["Login", "Sign Up"], key="auth_mode")
        
        if auth_mode == "Sign Up":
            st.subheader("📝 Create Account")
            signup_name = st.text_input("Full Name", key="signup_name")
            signup_email = st.text_input("Email", key="signup_email")
            signup_password = st.text_input("Password", type="password", key="signup_password")
            signup_confirm = st.text_input("Confirm Password", type="password", key="signup_confirm")
            
            if st.button("Sign Up", use_container_width=True):
                if not signup_name or not signup_email or not signup_password:
                    st.error("❌ Please fill all fields")
                elif signup_password != signup_confirm:
                    st.error("❌ Passwords do not match")
                elif len(signup_password) < 6:
                    st.error("❌ Password must be at least 6 characters")
                else:
                    result = create_user(signup_name, signup_email, signup_password)
                    if result['success']:
                        st.success("✅ Account created! Please login.")
                    else:
                        st.error(f"❌ {result['message']}")
        
        else:  # Login mode
            st.subheader("🔓 Login")
            login_email = st.text_input("Email", key="login_email")
            login_password = st.text_input("Password", type="password", key="login_password")
            
            if st.button("Login", use_container_width=True):
                if not login_email or not login_password:
                    st.error("❌ Please fill all fields")
                else:
                    result = login_user(login_email, login_password)
                    if result['success']:
                        st.session_state.logged_in = True
                        st.session_state.user_id = result['user_id']
                        st.session_state.user_name = result['name']
                        st.session_state.user_email = result['email']
                        st.success("✅ Login successful!")
                        st.rerun()
                    else:
                        st.error(f"❌ {result['message']}")
    
    else:  # User is logged in
        st.success(f"✅ Logged in as {st.session_state.user_name}")
        st.write(f"📧 {st.session_state.user_email}")
        
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.user_id = None
            st.session_state.user_name = None
            st.session_state.user_email = None
            st.rerun()
        
        st.markdown("---")

# ============================================================================
# MAIN CONTENT
# ============================================================================

st.markdown('<div class="title">💰 Insurance Price Predictor</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Get accurate insurance estimates with personalized tips</div>', unsafe_allow_html=True)

if not st.session_state.logged_in:
    st.info("👈 Please login or sign up in the sidebar to continue")

else:
    # Logged in - show prediction form
    st.header("📝 Personal Information")
    
    with st.form("prediction_form"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.subheader("👤 Basic Info")
            dob = st.date_input("Date of Birth", min_value=datetime(1900, 1, 1), max_value=datetime.today())
            sex = st.selectbox("Sex", ["male", "female"])
            city = st.text_input("City", placeholder="Enter your city")
        
        with col2:
            st.subheader("📏 Physical Metrics")
            height = st.number_input("Height (cm)", min_value=50.0, max_value=250.0, value=170.0)
            weight = st.number_input("Weight (kg)", min_value=20.0, max_value=300.0, value=70.0)
            children = st.number_input("Number of Children", min_value=0, max_value=10, value=0)
        
        with col3:
            st.subheader("🏥 Health & Lifestyle")
            smoker = st.selectbox("Do you smoke?", ["no", "yes"])
            st.write("---")
            st.write("**Calculated Values:**")
            age = calculate_age(dob)
            bmi = calculate_bmi(height, weight)
            region = get_region_from_city(city)
            st.write(f"**Age:** {age} years")
            st.write(f"**BMI:** {bmi}")
            st.write(f"**Region:** {region.title()}")
        
        submit = st.form_submit_button("🔮 Get Prediction", use_container_width=True)
    
    # API Call and Database Storage
    if submit:
        prediction_data = {
            "age": age,
            "sex": sex,
            "bmi": bmi,
            "children": children,
            "smoker": smoker,
            "region": region,
            "city": city,
            "height": height,
            "weight": weight
        }
        
        try:
            with st.spinner("🔍 Analyzing your data and calculating prediction..."):
                response = requests.post(API_URL, json={
                    "age": age,
                    "sex": sex,
                    "bmi": bmi,
                    "children": children,
                    "smoker": smoker,
                    "region": region
                })
            
            if response.status_code == 200:
                result = response.json()
                charges = result["prediction"]["estimated_charges"]
                category = result["prediction"]["category"]
                
                # Store in database
                db_result = insert_prediction(
                    st.session_state.user_id,
                    prediction_data,
                    {"charges": charges, "category": category}
                )
                
                if db_result['success']:
                    st.success("✅ Prediction saved to your account!")
                
                # Display result
                st.markdown(f"""
                    <div class="result-card">
                        <div class="result-title">💰 Your Estimated Insurance Charges</div>
                        <div class="result-amount">₹ {charges:,.2f}</div>
                        <div class="result-category">Risk Category: {category.title()}</div>
                    </div>
                """, unsafe_allow_html=True)
                
                # Tips section
                st.markdown('<div class="tips-section">', unsafe_allow_html=True)
                st.subheader("💡 Personalized Tips to Reduce Your Insurance Costs")
                tips = get_insurance_tips(prediction_data)
                for tip in tips:
                    st.markdown(f'<div class="tip-item">{tip}</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
                
                # AI Recommendations
                st.markdown("---")
                st.subheader("🤖 AI-Powered Insurance Recommendations")
                
                with st.spinner("🧠 Generating personalized recommendations..."):
                    recommendation_data = {
                        "age": age,
                        "bmi": bmi,
                        "smoker": smoker,
                        "city": city,
                        "region": region,
                        "charges": charges
                    }
                    
                    ai_recommendation = generate_recommendation(recommendation_data)
                
                if "error" in ai_recommendation:
                    st.warning(f"⚠️ AI Recommendations unavailable: {ai_recommendation['error']}")
                else:
                    # Risk Level
                    risk_colors = {
                        "Low": "🟢",
                        "Medium": "🟡", 
                        "High": "🔴"
                    }
                    
                    risk_color = risk_colors.get(ai_recommendation["risk_level"], "⚪")
                    st.metric(
                        label="Risk Assessment",
                        value=f"{risk_color} {ai_recommendation['risk_level']}",
                        help="AI-evaluated risk level based on your profile"
                    )
                    
                    # AI Tips
                    st.subheader("💡 AI-Generated Cost Reduction Tips")
                    for i, tip in enumerate(ai_recommendation["tips"], 1):
                        st.success(f"**{i}.** {tip}")
                    
                    # Top 3 Plans
                    st.subheader("🏆 Recommended Insurance Plans")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    for i, plan in enumerate(ai_recommendation["plans"]):
                        with [col1, col2, col3][i]:
                            st.markdown(f"""
                                <div style="
                                    background: linear-gradient(135deg, #f8fafc, #e2e8f0);
                                    padding: 20px;
                                    border-radius: 12px;
                                    border: 2px solid #cbd5e1;
                                    text-align: center;
                                    margin: 5px;
                                    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
                                ">
                                    <h4 style="color: #1e293b; margin-bottom: 10px;">{plan['name']}</h4>
                                    <p style="color: #64748b; font-size: 14px; margin: 0;">{plan['reason']}</p>
                                </div>
                            """, unsafe_allow_html=True)
                
                # Detailed summary
                with st.expander("📊 Detailed Input Summary"):
                    st.json({
                        "Personal Info": {
                            "Age": age,
                            "Sex": sex,
                            "City": city,
                            "Region": region
                        },
                        "Health Metrics": {
                            "Height": f"{height} cm",
                            "Weight": f"{weight} kg",
                            "BMI": bmi,
                            "Smoker": smoker
                        },
                        "Family": {
                            "Children": children
                        },
                        "Prediction": {
                            "Charges": f"₹{charges}",
                            "Category": category
                        }
                    })
            else:
                st.error(f"❌ API Error: {response.text}")
        
        except Exception as e:
            st.error(f"❌ Error: {e}")
    
    # Show prediction history
    st.markdown("---")
    st.header("📊 Your Prediction History")
    
    predictions = get_user_predictions(st.session_state.user_id)
    
    if predictions:
        # Create dataframe for display
        display_data = []
        for pred in predictions:
            display_data.append({
                "Date": pred['created_at'].strftime("%Y-%m-%d %H:%M:%S"),
                "Age": pred['age'],
                "Sex": pred['sex'].title(),
                "BMI": pred['bmi'],
                "Smoker": pred['smoker'].title(),
                "Region": pred['region'].title(),
                "Charges (₹)": f"{pred['charges']:,.2f}",
                "Category": pred['category'].title()
            })
        
        st.dataframe(display_data, use_container_width=True)
    else:
        st.info("📭 No predictions yet. Create your first prediction above!")

# Footer
st.markdown("---")
st.markdown("""
    <div style='text-align: center; color: #666; padding: 20px;'>
        <p>🔒 Your data is processed securely and encrypted in our database.</p>
        <p>📞 For questions, contact our support team.</p>
    </div>
""", unsafe_allow_html=True)
