# Gemini AI Integration - Insurance Recommendations

## ✅ Implementation Complete

Added comprehensive Gemini AI-powered insurance recommendation feature to your Streamlit app.

---

## 🔧 Setup & Dependencies

### Environment Variables
```bash
# .env file
DATABASE_URL=postgresql://...
GEMINI_API_KEY=your_gemini_api_key_here
```

### Dependencies Added
```txt
google-generativeai==0.8.3
```

### Installation
```bash
pip install google-generativeai
```

---

## 🤖 Gemini Configuration

### Setup Code
```python
import google.generativeai as genai

# Load API key from environment
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Configure and initialize model
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel("gemini-pro")
else:
    gemini_model = None
```

---

## 🎯 Core Function: `generate_recommendation(data)`

### Input Parameters
```python
data = {
    "age": int,        # User's age
    "bmi": float,      # Body Mass Index
    "smoker": str,     # "yes" or "no"
    "city": str,       # User's city
    "region": str,     # User's region
    "charges": float   # Predicted insurance charges
}
```

### Output Format
```json
{
  "risk_level": "Low|Medium|High",
  "tips": [
    "First actionable tip to reduce cost",
    "Second actionable tip to reduce cost",
    "Third actionable tip to reduce cost"
  ],
  "plans": [
    {
      "name": "Plan Type 1",
      "reason": "Brief reason why this suits the user"
    },
    {
      "name": "Plan Type 2",
      "reason": "Brief reason why this suits the user"
    },
    {
      "name": "Plan Type 3",
      "reason": "Brief reason why this suits the user"
    }
  ]
}
```

### Error Handling
- Returns `{"error": "message"}` on API failure
- Gracefully handles JSON parsing errors
- Validates response structure

---

## 🎨 UI Integration

### Risk Level Display
```python
# Uses st.metric() with color-coded indicators
st.metric(
    label="Risk Assessment",
    value=f"{risk_color} {ai_recommendation['risk_level']}"
)
```

### AI Tips Display
```python
# Uses st.success() for each tip
for i, tip in enumerate(ai_recommendation["tips"], 1):
    st.success(f"**{i}.** {tip}")
```

### Plan Recommendations
```python
# Uses st.columns(3) with custom styled cards
col1, col2, col3 = st.columns(3)

for i, plan in enumerate(ai_recommendation["plans"]):
    with [col1, col2, col3][i]:
        # Custom HTML card with plan name and reason
```

---

## 📋 Prompt Engineering

### Structured Prompt Template
The function builds a comprehensive prompt that includes:
- User data context (age, BMI, smoking, location, charges)
- Specific JSON format requirements
- Guidelines for risk assessment
- Instructions for actionable tips
- Requirements for generic plan types

### Response Processing
- Strips markdown code blocks if present
- Parses JSON response
- Validates required keys and array lengths
- Handles parsing failures gracefully

---

## 🔄 Integration Flow

1. **User submits prediction form**
2. **API calculates charges**
3. **Data stored in database**
4. **Results displayed**
5. **AI recommendation called** ← *New step*
6. **Gemini generates personalized advice**
7. **Results displayed in structured UI**

---

## 🛡️ Error Handling

### API Key Missing
```python
if not gemini_model:
    return {"error": "Gemini API key not configured"}
```

### API Call Failure
```python
except Exception as e:
    return {"error": f"AI recommendation failed: {str(e)}"}
```

### JSON Parsing Error
```python
except json.JSONDecodeError as e:
    return {"error": f"Failed to parse AI response: {str(e)}"}
```

### UI Fallback
```python
if "error" in ai_recommendation:
    st.warning(f"⚠️ AI Recommendations unavailable: {ai_recommendation['error']}")
```

---

## 🎨 Visual Design

### Risk Level Colors
- 🟢 **Low**: Green indicator
- 🟡 **Medium**: Yellow indicator
- 🔴 **High**: Red indicator

### Plan Cards
- Gradient background (`#f8fafc` to `#e2e8f0`)
- Rounded corners (12px)
- Border styling
- Centered text layout
- Subtle shadow effects

### Layout Structure
```
📊 Prediction Results
├── 💰 Charges Display
├── 💡 Basic Tips
├── 🤖 AI Recommendations
│   ├── 📈 Risk Level (st.metric)
│   ├── 💡 AI Tips (st.success)
│   └── 🏆 Top 3 Plans (st.columns with cards)
└── 📊 Detailed Summary
```

---

## 🚀 Usage

### Run the App
```bash
cd /Users/karanbayas/Documents/FAST_API
source myenv/bin/activate
streamlit run ui/ui.py
```

### Test the Feature
1. Sign up/Login
2. Fill prediction form
3. Submit to get prediction
4. View AI recommendations below the basic tips

---

## 📈 Benefits

✅ **Personalized Advice**: AI considers user's specific profile
✅ **Actionable Tips**: Specific ways to reduce insurance costs
✅ **Risk Assessment**: Clear risk level indication
✅ **Plan Recommendations**: Top 3 suitable plan types
✅ **Error Resilient**: Graceful fallbacks if AI fails
✅ **Clean UI**: Attractive, structured presentation
✅ **Fast Integration**: Minimal code changes required

---

## 🔧 Customization

### Modify Prompt
Edit the prompt template in `generate_recommendation()` to:
- Change risk assessment criteria
- Add more user data fields
- Modify tip generation guidelines
- Adjust plan recommendation focus

### Change UI Styling
Update the HTML card styling in the plan display section to match your app's theme.

### Add More Features
Extend the function to include:
- Historical data analysis
- Comparative plan analysis
- Regional insurance insights

---

## 📝 Notes

- Gemini API calls are made synchronously (may take 2-5 seconds)
- Response caching could be added for performance
- API key should be kept secure (environment variables)
- Error messages are user-friendly but technical details logged
- JSON parsing is strict to ensure consistent output format

---

**Integration Date:** April 17, 2026  
**Status:** ✅ Production Ready  
**AI Model:** Gemini Pro  
**Response Format:** Structured JSON
