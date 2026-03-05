import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import joblib
import warnings
import json
from datetime import datetime

# Import new modules
from auth import auth, login_page, register_page, check_authentication, logout_user
from offline_storage import offline_storage, show_offline_status
from profile import profile_page
from health_history import health_history_page
from advanced_features import (
    lifestyle_risk_analysis_page, 
    future_risk_prediction_page, 
    personalized_health_plan_page,
    ai_health_assistant
)

warnings.filterwarnings('ignore')

# Page configuration
st.set_page_config(
    page_title="HyperGuard AI",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #2c3e50;
        text-align: center;
        margin-bottom: 2rem;
    }
    .risk-low {
        color: #27ae60;
        font-weight: bold;
    }
    .risk-medium {
        color: #f39c12;
        font-weight: bold;
    }
    .risk-high {
        color: #e74c3c;
        font-weight: bold;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #1f77b4;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Title and description
def landing_section():
    st.markdown('<h1 class="main-header">🏥 HyperGuard AI</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">AI-Powered Hypertension Risk Prediction System</p>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div style="text-align: center; padding: 2rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    border-radius: 15px; color: white; margin-bottom: 2rem;">
            <h3>🤖 Advanced Machine Learning for Health</h3>
            <p>Our AI system analyzes your health parameters to predict hypertension risk with high accuracy. 
            Get personalized health recommendations based on your unique profile.</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🚀 Start Risk Check", type="primary", use_container_width=True):
            st.session_state.current_page = "form"
            st.rerun()

# Health data input form
def health_data_form():
    st.markdown('<h2 class="sub-header">📋 Enter Your Health Data</h2>', unsafe_allow_html=True)
    
    with st.form("health_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            age = st.number_input("🎂 Age", min_value=18, max_value=100, value=35, help="Enter your age in years")
            weight = st.number_input("⚖️ Weight (kg)", min_value=30.0, max_value=200.0, value=70.0, step=0.1)
            height = st.number_input("📏 Height (cm)", min_value=100.0, max_value=250.0, value=170.0, step=0.1)
            systolic = st.number_input("💉 Systolic BP (mmHg)", min_value=80, max_value=200, value=120)
            
        with col2:
            diastolic = st.number_input("💉 Diastolic BP (mmHg)", min_value=40, max_value=130, value=80)
            smoking = st.selectbox("🚬 Smoking", ["No", "Yes"], help="Do you smoke?")
            alcohol = st.selectbox("🍷 Alcohol Consumption", ["None", "Occasional", "Regular", "Heavy"])
            physical_activity = st.selectbox("🏃 Physical Activity", ["Low", "Moderate", "High", "Very High"])
            salt_intake = st.selectbox("🧂 Salt Intake", ["Low", "Moderate", "High"])
        
        # Calculate BMI
        height_m = height / 100
        bmi = weight / (height_m ** 2)
        
        st.markdown(f"**📊 Calculated BMI: {bmi:.1f}**")
        
        # Submit button
        submitted = st.form_submit_button("🔮 Predict Hypertension Risk", type="primary", use_container_width=True)
        
        if submitted:
            # Store data in session state
            st.session_state.health_data = {
                'age': age,
                'weight': weight,
                'height': height,
                'bmi': bmi,
                'systolic': systolic,
                'diastolic': diastolic,
                'smoking': 1 if smoking == "Yes" else 0,
                'alcohol': {"None": 0, "Occasional": 1, "Regular": 2, "Heavy": 3}[alcohol],
                'physical_activity': {"Low": 0, "Moderate": 1, "High": 2, "Very High": 3}[physical_activity],
                'salt_intake': {"Low": 0, "Moderate": 1, "High": 2}[salt_intake]
            }
            
            # Save to user's health history
            username = st.session_state.get('current_user')
            if username:
                auth.add_health_record(username, st.session_state.health_data)
            
            st.session_state.current_page = "results"
            st.rerun()

# Load or create model
def get_model():
    try:
        model = joblib.load('hypertension_model.pkl')
        scaler = joblib.load('scaler.pkl')
    except:
        # Create a simple model if file doesn't exist
        model = create_simple_model()
        scaler = StandardScaler()
    return model, scaler

def create_simple_model():
    # Create a simple rule-based model for demonstration
    class SimpleHypertensionModel:
        def predict(self, X):
            predictions = []
            for _, row in X.iterrows():
                age, bmi, systolic, diastolic, smoking, alcohol, activity, salt = row
                
                # Simple rule-based prediction
                risk_score = 0
                
                # Age factor
                if age >= 60:
                    risk_score += 3
                elif age >= 45:
                    risk_score += 2
                elif age >= 30:
                    risk_score += 1
                
                # BMI factor
                if bmi >= 30:
                    risk_score += 3
                elif bmi >= 25:
                    risk_score += 2
                elif bmi < 18.5:
                    risk_score += 1
                
                # Blood pressure factor (most important)
                if systolic >= 160 or diastolic >= 100:
                    risk_score += 4
                elif systolic >= 140 or diastolic >= 90:
                    risk_score += 3
                elif systolic >= 130 or diastolic >= 85:
                    risk_score += 2
                elif systolic >= 120 or diastolic >= 80:
                    risk_score += 1
                
                # Lifestyle factors
                risk_score += smoking * 2
                risk_score += (3 - activity) * 1
                risk_score += alcohol * 1
                risk_score += salt * 1
                
                # Determine stage
                if risk_score >= 8:
                    predictions.append(3)  # Stage 2
                elif risk_score >= 6:
                    predictions.append(2)  # Stage 1
                elif risk_score >= 3:
                    predictions.append(1)  # Pre-Hypertension
                else:
                    predictions.append(0)  # Normal
            
            return np.array(predictions)
    
    return SimpleHypertensionModel()

# Prediction function
def predict_hypertension():
    if 'health_data' not in st.session_state:
        st.warning("Please enter your health data first!")
        return
    
    model, scaler = get_model()
    
    # Prepare data
    data = st.session_state.health_data
    features = pd.DataFrame([[
        data['age'], data['bmi'], data['systolic'], data['diastolic'],
        data['smoking'], data['alcohol'], data['physical_activity'], data['salt_intake']
    ]], columns=['age', 'bmi', 'systolic', 'diastolic', 'smoking', 'alcohol', 'physical_activity', 'salt_intake'])
    
    # Make prediction
    try:
        prediction = model.predict(features)[0]
        
        # Define stages and risk level for offline storage
        stages = ["Normal", "Pre-Hypertension", "Stage 1 Hypertension", "Stage 2 Hypertension"]
        
        if prediction == 0:
            risk_level = "Low Risk"
        elif prediction == 1:
            risk_level = "Moderate Risk"
        else:
            risk_level = "High Risk"
        
        # Save assessment to offline storage
        username = st.session_state.get('current_user')
        if username:
            prediction_result = {
                'prediction': prediction,
                'stage': stages[prediction],
                'risk_level': risk_level,
                'recommendations': get_recommendations(prediction, data)
            }
            offline_storage.save_health_assessment(data, prediction_result, username)
        
        display_results(prediction, data)
    except Exception as e:
        st.error(f"Prediction error: {e}")

# Display results
def display_results(prediction, data):
    stages = ["Normal", "Pre-Hypertension", "Stage 1 Hypertension", "Stage 2 Hypertension"]
    stage = stages[prediction]
    
    # Risk level
    if prediction == 0:
        risk_class = "risk-low"
        risk_level = "Low Risk"
        emoji = "✅"
    elif prediction == 1:
        risk_class = "risk-medium"
        risk_level = "Moderate Risk"
        emoji = "⚠️"
    else:
        risk_class = "risk-high"
        risk_level = "High Risk"
        emoji = "🚨"
    
    st.markdown(f'<h2 class="sub-header">{emoji} Prediction Results</h2>', unsafe_allow_html=True)
    
    # Main result
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(f"""
        <div class="metric-card" style="text-align: center;">
            <h3>Hypertension Stage</h3>
            <h2>{stage}</h2>
            <p class="{risk_class}">{risk_level}</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Health metrics
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        <div class="metric-card">
            <h4>📊 Your Health Metrics</h4>
        </div>
        """, unsafe_allow_html=True)
        st.write(f"**Age:** {data['age']} years")
        st.write(f"**BMI:** {data['bmi']:.1f}")
        st.write(f"**Blood Pressure:** {data['systolic']}/{data['diastolic']} mmHg")
        st.write(f"**Smoking:** {'Yes' if data['smoking'] else 'No'}")
    
    with col2:
        st.markdown("""
        <div class="metric-card">
            <h4>💡 Health Recommendations</h4>
        </div>
        """, unsafe_allow_html=True)
        
        recommendations = get_recommendations(prediction, data)
        for rec in recommendations:
            st.write(f"• {rec}")
    
    # Visualization
    st.markdown('<h3>📈 Blood Pressure Risk Chart</h3>', unsafe_allow_html=True)
    create_bp_chart(data['systolic'], data['diastolic'], prediction)
    
    # Action buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 New Assessment", use_container_width=True):
            st.session_state.current_page = "form"
            st.rerun()
    
    with col2:
        if st.button("🏠 Back to Home", use_container_width=True):
            st.session_state.current_page = "landing"
            st.rerun()

def get_recommendations(prediction, data):
    recommendations = []
    
    if prediction == 0:
        recommendations.extend([
            "Continue maintaining healthy lifestyle",
            "Regular health check-ups every 2 years",
            "Maintain balanced diet and regular exercise"
        ])
    elif prediction == 1:
        recommendations.extend([
            "Reduce salt intake to less than 5g per day",
            "Increase physical activity to 150 minutes per week",
            "Maintain healthy weight",
            "Limit alcohol consumption",
            "Regular BP monitoring"
        ])
    else:
        recommendations.extend([
            "Consult healthcare provider immediately",
            "Follow prescribed medication regimen",
            "Strict dietary modifications required",
            "Daily blood pressure monitoring",
            "Regular medical follow-ups"
        ])
    
    # Specific recommendations based on data
    if data['bmi'] >= 25:
        recommendations.append("Weight management through diet and exercise")
    
    if data['smoking'] == 1:
        recommendations.append("Quit smoking - seek professional help")
    
    if data['physical_activity'] < 2:
        recommendations.append("Increase physical activity gradually")
    
    return recommendations[:6]  # Limit to 6 recommendations

def create_bp_chart(systolic, diastolic, prediction):
    # Create BP categories chart
    categories = ['Normal', 'Elevated', 'Stage 1', 'Stage 2']
    colors = ['#27ae60', '#f39c12', '#e67e22', '#e74c3c']
    
    fig = go.Figure()
    
    # Add reference ranges
    fig.add_shape(type="rect", x0=-0.5, x1=0.5, y0=0, y1=120/120, 
                  fillcolor="rgba(39, 174, 96, 0.2)", line=dict(color="#27ae60"))
    fig.add_shape(type="rect", x0=0.5, x1=1.5, y0=0, y1=129/120, 
                  fillcolor="rgba(243, 156, 18, 0.2)", line=dict(color="#f39c12"))
    fig.add_shape(type="rect", x0=1.5, x1=2.5, y0=0, y1=139/120, 
                  fillcolor="rgba(230, 126, 34, 0.2)", line=dict(color="#e67e22"))
    fig.add_shape(type="rect", x0=2.5, x1=3.5, y0=0, y1=180/120, 
                  fillcolor="rgba(231, 76, 60, 0.2)", line=dict(color="#e74c3c"))
    
    # Add user's BP
    fig.add_trace(go.Scatter(
        x=[prediction],
        y=[systolic/120],
        mode='markers',
        marker=dict(size=20, color='red', symbol='diamond'),
        name=f'Your BP: {systolic}/{diastolic}'
    ))
    
    fig.update_layout(
        title="Blood Pressure Classification",
        xaxis_title="Hypertension Stage",
        yaxis_title="Systolic BP (normalized)",
        height=400,
        showlegend=True
    )
    
    st.plotly_chart(fig, use_container_width=True)

# Main app logic
def main():
    # Initialize session state
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'login'
    
    # Check authentication
    is_authenticated = check_authentication()
    
    # Display pages based on authentication and current page
    if not is_authenticated:
        if st.session_state.current_page == 'login':
            login_page()
        elif st.session_state.current_page == 'register':
            register_page()
        else:
            st.session_state.current_page = 'login'
            login_page()
    else:
        # User is authenticated - show main app
        show_authenticated_app()

def show_authenticated_app():
    """Show the main app for authenticated users"""
    username = st.session_state.get('current_user', 'User')
    
    # Navigation
    st.sidebar.title(f"🏥 HyperGuard AI")
    st.sidebar.markdown(f"**Welcome, {username}!**")
    
    # Offline status indicator
    with st.sidebar:
        show_offline_status()
    
    st.sidebar.markdown("---")
    
    # Sidebar navigation
    if st.sidebar.button("🏠 Home", use_container_width=True):
        st.session_state.current_page = 'landing'
        st.rerun()
    
    if st.sidebar.button("📋 Health Assessment", use_container_width=True):
        st.session_state.current_page = 'form'
        st.rerun()
    
    if st.sidebar.button("📊 Health History", use_container_width=True):
        st.session_state.current_page = 'history'
        st.rerun()
    
    if st.sidebar.button("👤 My Profile", use_container_width=True):
        st.session_state.current_page = 'profile'
        st.rerun()
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("**🔬 Advanced Features**")
    
    if st.sidebar.button("🔍 Risk Analysis", use_container_width=True):
        st.session_state.current_page = 'risk_analysis'
        st.rerun()
    
    if st.sidebar.button("🔮 Future Prediction", use_container_width=True):
        st.session_state.current_page = 'future_prediction'
        st.rerun()
    
    if st.sidebar.button("📋 Health Plan", use_container_width=True):
        st.session_state.current_page = 'health_plan'
        st.rerun()
    
    if st.sidebar.button("🤖 AI Assistant", use_container_width=True):
        st.session_state.current_page = 'ai_assistant'
        st.rerun()
    
    if 'health_data' in st.session_state and st.sidebar.button("🎯 Latest Results", use_container_width=True):
        st.session_state.current_page = 'results'
        st.rerun()
    
    st.sidebar.markdown("---")
    
    if st.sidebar.button("🚪 Logout", use_container_width=True):
        logout_user()
    
    # Main content
    if st.session_state.current_page == 'landing':
        landing_section()
    elif st.session_state.current_page == 'form':
        health_data_form()
    elif st.session_state.current_page == 'results':
        predict_hypertension()
    elif st.session_state.current_page == 'history':
        health_history_page()
    elif st.session_state.current_page == 'profile':
        profile_page()
    elif st.session_state.current_page == 'risk_analysis':
        lifestyle_risk_analysis_page()
    elif st.session_state.current_page == 'future_prediction':
        future_risk_prediction_page()
    elif st.session_state.current_page == 'health_plan':
        personalized_health_plan_page()
    elif st.session_state.current_page == 'ai_assistant':
        ai_health_assistant()
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666;'>
        <p>🏥 HyperGuard AI - Your Health Companion | 
        <small>This is for educational purposes only. Always consult healthcare professionals.</small></p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
