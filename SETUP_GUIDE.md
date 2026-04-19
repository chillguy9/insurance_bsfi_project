# Insurance Price Predictor - Setup Guide

## 📋 Project Overview

A complete Streamlit application with PostgreSQL (Supabase) integration featuring:
- ✅ User Authentication (Signup/Login with bcrypt hashing)
- ✅ Session Management using `st.session_state`
- ✅ Insurance Charge Prediction via FastAPI backend
- ✅ Secure Database Storage with parameterized queries
- ✅ Prediction History tracking per user
- ✅ Modern UI with custom styling
- ✅ Error handling and validation

## 🗄️ Database Schema

### Users Table
```sql
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Predictions Table
```sql
CREATE TABLE predictions (
    prediction_id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    age INTEGER NOT NULL,
    sex VARCHAR(10) NOT NULL,
    bmi FLOAT NOT NULL,
    children INTEGER NOT NULL,
    smoker VARCHAR(10) NOT NULL,
    region VARCHAR(50) NOT NULL,
    city VARCHAR(100),
    height_cm FLOAT,
    weight_kg FLOAT,
    estimated_charges FLOAT NOT NULL,
    category VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.10+
- Virtual environment (venv, conda, etc.)
- PostgreSQL database (using Supabase)

### 2. Installation

```bash
# Navigate to project directory
cd /Users/karanbayas/Documents/FAST_API

# Activate virtual environment
source myenv/bin/activate

# Install dependencies
pip install -r requirements.txt

# OR manually install required packages:
pip install psycopg2-binary bcrypt streamlit requests
```

### 3. Environment Setup

Create a `.env` file in the project root:
```
DATABASE_URL=postgresql://user:password@host:5432/database
```

Or use the provided `.env.example` as a template.

### 4. Run the Application

```bash
# From the project root directory
streamlit run ui/ui.py

# The app will be available at http://localhost:8501
```

## 📚 Core Functions

### Database Functions

#### `connect_db()`
- Creates and caches database connection
- Uses `@st.cache_resource` decorator for performance
- Returns connection object or None on failure

#### `create_user(name, email, password)`
- Registers new user with bcrypt-hashed password
- Validates email uniqueness
- Returns success/failure status

#### `login_user(email, password)`
- Authenticates user credentials
- Verifies bcrypt hash
- Returns user_id on success

#### `insert_prediction(user_id, prediction_data, result)`
- Stores prediction in database
- Uses parameterized queries to prevent SQL injection
- Captures all user input and prediction results

#### `get_user_predictions(user_id)`
- Fetches all predictions for a specific user
- Returns list of predictions sorted by date (newest first)
- Used to populate prediction history

#### `init_database()`
- Initializes database tables if they don't exist
- Runs on app startup
- Creates users and predictions tables

### Security Features

✅ **Password Hashing**: Uses bcrypt with salt
✅ **SQL Injection Prevention**: All queries use parameterized queries with `%s` placeholders
✅ **Session Management**: Uses `st.session_state` for secure login tracking
✅ **Foreign Key Constraints**: Predictions linked to users with CASCADE delete

## 🔐 Authentication Flow

### Sign Up
1. User enters name, email, password
2. Password is hashed using bcrypt.hashpw()
3. Data stored in database with unique constraint on email
4. Returns error if email already exists

### Login
1. User enters email and password
2. Email is looked up in users table
3. Password is verified against hash using bcrypt.checkpw()
4. user_id stored in st.session_state["user_id"]
5. Session maintained until logout

## 📊 Prediction Storage

After prediction is generated:
1. API returns estimated_charges and category
2. All user inputs + prediction stored in predictions table
3. Linked to user via user_id (foreign key)
4. Timestamp automatically recorded as created_at
5. User can view all historical predictions

## 🎨 UI Structure

### Sidebar
- **Not Logged In**: Login/Sign Up tabs
- **Logged In**: User info, Logout button

### Main Page
- **Not Logged In**: Info message to login
- **Logged In**: 
  - Prediction form with 3 columns
  - Result display card
  - Insurance tips section
  - Prediction history table

## 🛠️ Development Tips

### Testing the Database
```python
# In terminal or Python REPL
import psycopg2
import os

conn = psycopg2.connect(os.getenv("DATABASE_URL"))
cur = conn.cursor()
cur.execute("SELECT * FROM users;")
print(cur.fetchall())
cur.close()
conn.close()
```

### Error Handling
The app handles:
- Database connection failures
- Duplicate email registrations
- Wrong password attempts
- SQL errors
- API connection errors

## 📦 Dependencies

```
streamlit==1.55.0
requests==2.33.1
psycopg2-binary==2.9.11
bcrypt==5.0.0
pydantic==2.12.5
```

## 🔄 Database Transactions

All database operations use proper transaction handling:
- `conn.commit()` after successful INSERT/UPDATE
- `conn.rollback()` on errors
- Cursor closed in finally block
- Connection closed after use

## 💡 Best Practices Implemented

✅ Connection pooling with `@st.cache_resource`
✅ Parameterized queries for all SQL statements
✅ Proper error handling with user-friendly messages
✅ Secure password hashing with bcrypt
✅ Clean function separation
✅ Comprehensive documentation
✅ Session-based authentication
✅ Foreign key relationships with cascade delete

## 🐛 Troubleshooting

### "Database connection failed"
- Check `.env` file contains correct DATABASE_URL
- Verify Supabase database is accessible
- Ensure psycopg2 is installed: `pip install psycopg2-binary`

### "Email already registered"
- User exists; use different email or login

### "Incorrect password"
- Verify password is correct
- Password is case-sensitive

### Streamlit cached connection issues
- Use `st.cache_resource.clear()` to reset cache
- Or restart Streamlit: Ctrl+C and rerun

## 📞 Support

For issues:
1. Check error messages in terminal
2. Verify database connection
3. Ensure all packages installed
4. Check .env file configuration

---

**Created**: April 2026
**Status**: Production Ready
