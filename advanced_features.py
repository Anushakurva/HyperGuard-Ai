import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
import warnings
from auth import auth
from offline_storage import offline_storage

warnings.filterwarnings('ignore')

class AdvancedHealthAnalyzer:
    def __init__(self):
        self.risk_factors = {
            'age': {'weight': 0.3, 'optimal': '25-45'},
            'bmi': {'weight': 0.25, 'optimal': '18.5-24.9'},
            'systolic': {'weight': 0.2, 'optimal': '<120'},
            'diastolic': {'weight': 0.2, 'optimal': '<80'},
            'smoking': {'weight': 0.15, 'optimal': 'No'},
            'alcohol': {'weight': 0.1, 'optimal': 'None'},
            'physical_activity': {'weight': 0.15, 'optimal': 'High'},
            'salt_intake': {'weight': 0.1, 'optimal': 'Low'}
        }
    
    def calculate_lifestyle_risk_score(self, health_data):
        """Calculate comprehensive lifestyle risk score"""
        risk_score = 0
        risk_factors = []
        
        # Age risk
        age = health_data.get('age', 0)
        if age >= 60:
            risk_score += 30
            risk_factors.append("High age risk (60+)")
        elif age >= 45:
            risk_score += 20
            risk_factors.append("Moderate age risk (45-59)")
        elif age >= 30:
            risk_score += 10
            risk_factors.append("Low age risk (30-44)")
        
        # BMI risk
        bmi = health_data.get('bmi', 0)
        if bmi >= 30:
            risk_score += 25
            risk_factors.append("Obesity (BMI ≥30)")
        elif bmi >= 25:
            risk_score += 15
            risk_factors.append("Overweight (BMI 25-29.9)")
        elif bmi < 18.5:
            risk_score += 10
            risk_factors.append("Underweight (BMI <18.5)")
        
        # Blood pressure risk
        systolic = health_data.get('systolic', 0)
        diastolic = health_data.get('diastolic', 0)
        
        if systolic >= 160 or diastolic >= 100:
            risk_score += 40
            risk_factors.append("Stage 2 Hypertension")
        elif systolic >= 140 or diastolic >= 90:
            risk_score += 30
            risk_factors.append("Stage 1 Hypertension")
        elif systolic >= 130 or diastolic >= 85:
            risk_score += 20
            risk_factors.append("Elevated Blood Pressure")
        elif systolic >= 120 or diastolic >= 80:
            risk_score += 10
            risk_factors.append("Normal High Blood Pressure")
        
        # Lifestyle risks
        if health_data.get('smoking', 0) == 1:
            risk_score += 20
            risk_factors.append("Smoking")
        
        alcohol_score = health_data.get('alcohol', 0)
        if alcohol_score >= 3:
            risk_score += 15
            risk_factors.append("Heavy alcohol consumption")
        elif alcohol_score >= 2:
            risk_score += 10
            risk_factors.append("Regular alcohol consumption")
        elif alcohol_score >= 1:
            risk_score += 5
            risk_factors.append("Occasional alcohol consumption")
        
        activity_score = health_data.get('physical_activity', 0)
        if activity_score <= 1:
            risk_score += 15
            risk_factors.append("Low physical activity")
        elif activity_score == 2:
            risk_score += 5
            risk_factors.append("Moderate physical activity")
        
        salt_score = health_data.get('salt_intake', 0)
        if salt_score >= 2:
            risk_score += 10
            risk_factors.append("High salt intake")
        elif salt_score == 1:
            risk_score += 5
            risk_factors.append("Moderate salt intake")
        
        return {
            'total_score': min(risk_score, 100),
            'risk_level': self._get_risk_level(risk_score),
            'risk_factors': risk_factors
        }
    
    def _get_risk_level(self, score):
        if score >= 70:
            return "Very High Risk"
        elif score >= 50:
            return "High Risk"
        elif score >= 30:
            return "Moderate Risk"
        elif score >= 15:
            return "Low Risk"
        else:
            return "Very Low Risk"
    
    def predict_future_risk(self, username, months_ahead=12):
        """Predict future hypertension risk based on trends"""
        health_history = auth.get_health_history(username)
        
        if len(health_history) < 3:
            return {
                "error": f"Need at least 3 health assessments for future prediction. You currently have {len(health_history)} assessment(s). Complete {3 - len(health_history)} more assessment(s) to unlock this feature.",
                "current_count": len(health_history),
                "needed_count": 3
            }
        
        # Convert to DataFrame
        df = pd.DataFrame(health_history)
        df['datetime'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('datetime')
        
        # Calculate trends
        predictions = []
        
        for factor in ['systolic', 'diastolic', 'bmi']:
            if factor in df.columns:
                # Simple linear regression for trend prediction
                X = np.arange(len(df)).reshape(-1, 1)
                y = df[factor].values
                
                model = LinearRegression()
                model.fit(X, y)
                
                # Predict future values
                future_X = np.array([[len(df)], [len(df) + months_ahead//3]])
                future_values = model.predict(future_X)
                
                predictions.append({
                    'factor': factor,
                    'current': future_values[0],
                    'future': future_values[1],
                    'trend': 'increasing' if future_values[1] > future_values[0] else 'decreasing'
                })
        
        # Calculate future risk score
        future_data = {
            'age': df['age'].iloc[-1] + (months_ahead // 12),
            'bmi': predictions[2]['future'] if len(predictions) > 2 else df['bmi'].iloc[-1],
            'systolic': predictions[0]['future'] if len(predictions) > 0 else df['systolic'].iloc[-1],
            'diastolic': predictions[1]['future'] if len(predictions) > 1 else df['diastolic'].iloc[-1],
            'smoking': df['smoking'].iloc[-1],
            'alcohol': df['alcohol'].iloc[-1],
            'physical_activity': df['physical_activity'].iloc[-1],
            'salt_intake': df['salt_intake'].iloc[-1]
        }
        
        future_risk = self.calculate_lifestyle_risk_score(future_data)
        
        return {
            'predictions': predictions,
            'future_risk': future_risk,
            'months_ahead': months_ahead,
            'recommendations': self._generate_future_recommendations(predictions, future_risk)
        }
    
    def _generate_future_recommendations(self, predictions, future_risk):
        """Generate recommendations based on future predictions"""
        recommendations = []
        
        for pred in predictions:
            if pred['trend'] == 'increasing':
                if pred['factor'] == 'systolic':
                    recommendations.append("🩺 Your systolic BP is trending upward - consider reducing salt intake and increasing exercise")
                elif pred['factor'] == 'diastolic':
                    recommendations.append("🩺 Your diastolic BP is trending upward - stress management and meditation may help")
                elif pred['factor'] == 'bmi':
                    recommendations.append("⚖️ Your BMI is increasing - focus on diet and portion control")
        
        if future_risk['risk_level'] in ['High Risk', 'Very High Risk']:
            recommendations.append("⚠️ Your future risk is high - consult a healthcare provider soon")
            recommendations.append("🏥 Consider regular medical check-ups and monitoring")
        
        return recommendations
    
    def generate_personalized_health_plan(self, health_data, risk_analysis):
        """Generate personalized health plan based on current data and risks"""
        plan = {
            'immediate_actions': [],
            'weekly_goals': [],
            'monthly_targets': [],
            'lifestyle_changes': []
        }
        
        # Immediate actions based on risk factors
        if health_data.get('systolic', 0) >= 140 or health_data.get('diastolic', 0) >= 90:
            plan['immediate_actions'].append("🩺 Schedule a doctor's appointment this week")
            plan['immediate_actions'].append("📊 Start daily blood pressure monitoring")
        
        if health_data.get('bmi', 0) >= 30:
            plan['immediate_actions'].append("⚖️ Consult a nutritionist for weight management")
        
        # Weekly goals
        if health_data.get('physical_activity', 0) < 2:
            plan['weekly_goals'].append("🏃 Aim for 150 minutes of moderate exercise per week")
            plan['weekly_goals'].append("🚶 Start with 30-minute walks, 5 days a week")
        
        if health_data.get('smoking', 0) == 1:
            plan['weekly_goals'].append("🚭 Set a quit date within the next 2 weeks")
            plan['weekly_goals'].append("📞 Call smoking cessation helpline")
        
        # Monthly targets
        if health_data.get('systolic', 0) >= 130:
            plan['monthly_targets'].append("🩺 Reduce systolic BP by 5-10 mmHg")
        
        if health_data.get('bmi', 0) >= 25:
            plan['monthly_targets'].append("⚖️ Lose 1-2 kg of body weight")
        
        plan['monthly_targets'].append("📈 Complete 4 health assessments")
        plan['monthly_targets'].append("🥗 Follow a balanced diet plan")
        
        # Lifestyle changes
        if health_data.get('salt_intake', 0) >= 2:
            plan['lifestyle_changes'].append("🧂 Reduce salt intake to less than 5g per day")
            plan['lifestyle_changes'].append("🥒 Choose fresh foods over processed foods")
        
        if health_data.get('alcohol', 0) >= 2:
            plan['lifestyle_changes'].append("🍷 Limit alcohol to 1 drink per day")
            plan['lifestyle_changes'].append("💧 Have alcohol-free days each week")
        
        plan['lifestyle_changes'].append("😴 Get 7-8 hours of quality sleep")
        plan['lifestyle_changes'].append("🧘 Practice stress management techniques")
        plan['lifestyle_changes'].append("🥗 Eat more fruits and vegetables")
        
        return plan

# Initialize analyzer
analyzer = AdvancedHealthAnalyzer()

def lifestyle_risk_analysis_page():
    """Display comprehensive lifestyle risk analysis"""
    st.markdown('<h2 class="sub-header">🔍 Lifestyle Risk Analysis</h2>', unsafe_allow_html=True)
    
    username = st.session_state.get('current_user')
    if not username:
        st.error("Please login to access this feature")
        return
    
    # Get latest health data
    health_history = auth.get_health_history(username)
    if not health_history:
        st.info("No health data available. Complete a health assessment first.")
        return
    
    latest_data = health_history[-1]
    
    # Calculate comprehensive risk analysis
    risk_analysis = analyzer.calculate_lifestyle_risk_score(latest_data)
    
    # Display risk score with visual
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Risk score gauge
        fig = go.Figure(go.Indicator(
            mode = "gauge+number+delta",
            value = risk_analysis['total_score'],
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': f"Risk Score: {risk_analysis['risk_level']}", 'font': {'size': 24}},
            delta = {'reference': 50},
            gauge = {
                'axis': {'range': [None, 100]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 30], 'color': "lightgreen"},
                    {'range': [30, 50], 'color': "yellow"},
                    {'range': [50, 70], 'color': "orange"},
                    {'range': [70, 100], 'color': "red"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 70
                }
            }
        ))
        
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    # Risk factors breakdown
    st.markdown("### 🎯 Risk Factors Breakdown")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Identified Risk Factors:**")
        for i, factor in enumerate(risk_analysis['risk_factors'], 1):
            st.write(f"{i}. {factor}")
    
    with col2:
        # Factor contribution chart
        factor_data = []
        for factor, config in analyzer.risk_factors.items():
            if factor in latest_data:
                value = latest_data[factor]
                if factor in ['age', 'bmi', 'systolic', 'diastolic']:
                    # Normalize for display
                    if factor == 'age':
                        normalized = min(value / 80 * 100, 100)
                    elif factor == 'bmi':
                        normalized = min(value / 35 * 100, 100)
                    elif factor == 'systolic':
                        normalized = min(value / 180 * 100, 100)
                    elif factor == 'diastolic':
                        normalized = min(value / 120 * 100, 100)
                else:
                    normalized = value * 25  # Scale lifestyle factors
                
                factor_data.append({
                    'Factor': factor.replace('_', ' ').title(),
                    'Contribution': normalized * config['weight'],
                    'Optimal': config['optimal']
                })
        
        if factor_data:
            factor_df = pd.DataFrame(factor_data)
            fig = px.bar(factor_df, x='Factor', y='Contribution', 
                        title="Risk Factor Contributions",
                        color='Contribution',
                        color_continuous_scale='Reds')
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)

def future_risk_prediction_page():
    """Display future risk prediction"""
    st.markdown('<h2 class="sub-header">🔮 Future Risk Prediction</h2>', unsafe_allow_html=True)
    
    username = st.session_state.get('current_user')
    if not username:
        st.error("Please login to access this feature")
        return
    
    # Check current assessment count
    health_history = auth.get_health_history(username)
    current_count = len(health_history)
    
    # Status indicator
    if current_count < 3:
        st.warning(f"📊 **Assessment Status:** {current_count}/3 completed")
        st.markdown(f"⏳ **Progress:** Complete {3 - current_count} more assessment(s) to unlock future predictions")
        st.markdown("---")
    else:
        st.success(f"📊 **Assessment Status:** {current_count}/3 completed ✅")
        st.markdown("🎉 **Future predictions are now available!**")
        st.markdown("---")
    
    # Time horizon selection
    months_ahead = st.selectbox("📅 Prediction Horizon", 
                              options=[3, 6, 12, 24], 
                              index=2,
                              help="Predict risk for how many months ahead?")
    
    if st.button("🔮 Generate Future Prediction", type="primary"):
        with st.spinner("Analyzing trends and predicting future risks..."):
            prediction_result = analyzer.predict_future_risk(username, months_ahead)
            
            if "error" in prediction_result:
                st.error(prediction_result["error"])
                
                # Show helpful guidance
                if "current_count" in prediction_result:
                    current = prediction_result["current_count"]
                    needed = prediction_result["needed_count"]
                    remaining = needed - current
                    
                    st.markdown("### 📋 How to Unlock Future Predictions")
                    st.markdown(f"You need **{remaining} more** health assessment(s) to access this feature.")
                    
                    st.markdown("**Why 3 assessments?**")
                    st.write("• Analyze trends in your health metrics over time")
                    st.write("• Identify patterns in blood pressure changes")
                    st.write("• Provide accurate future risk predictions")
                    st.write("• Generate personalized recommendations")
                    
                    if st.button("🚀 Complete Health Assessment", type="primary"):
                        st.session_state.current_page = "form"
                        st.rerun()
                
                return
            
            # Display current vs future comparison
            st.markdown("### 📊 Current vs Future Risk Comparison")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Current Status**")
                current_health = auth.get_health_history(username)[-1]
                st.write(f"🩺 Systolic: {current_health.get('systolic', 'N/A')}")
                st.write(f"🩺 Diastolic: {current_health.get('diastolic', 'N/A')}")
                st.write(f"⚖️ BMI: {current_health.get('bmi', 'N/A'):.1f}")
            
            with col2:
                st.markdown("**Predicted Future**")
                for pred in prediction_result['predictions']:
                    if pred['factor'] == 'systolic':
                        st.write(f"🩺 Systolic: {pred['future']:.1f} {pred['trend']}")
                    elif pred['factor'] == 'diastolic':
                        st.write(f"🩺 Diastolic: {pred['future']:.1f} {pred['trend']}")
                    elif pred['factor'] == 'bmi':
                        st.write(f"⚖️ BMI: {pred['future']:.1f} {pred['trend']}")
            
            # Future risk level
            future_risk = prediction_result['future_risk']
            risk_emoji = "🚨" if "Very High" in future_risk['risk_level'] else "⚠️" if "High" in future_risk['risk_level'] else "✅"
            
            st.markdown(f"### {risk_emoji} Predicted Risk Level: {future_risk['risk_level']}")
            st.write(f"**Risk Score:** {future_risk['total_score']}/100")
            
            # Recommendations
            if prediction_result['recommendations']:
                st.markdown("### 💡 Future Risk Recommendations")
                for rec in prediction_result['recommendations']:
                    st.write(f"• {rec}")

def personalized_health_plan_page():
    """Display personalized health plan"""
    st.markdown('<h2 class="sub-header">📋 Personalized Health Plan</h2>', unsafe_allow_html=True)
    
    username = st.session_state.get('current_user')
    if not username:
        st.error("Please login to access this feature")
        return
    
    # Get latest health data
    health_history = auth.get_health_history(username)
    if not health_history:
        st.info("No health data available. Complete a health assessment first.")
        return
    
    latest_data = health_history[-1]
    risk_analysis = analyzer.calculate_lifestyle_risk_score(latest_data)
    
    # Generate personalized plan
    health_plan = analyzer.generate_personalized_health_plan(latest_data, risk_analysis)
    
    # Display plan in organized sections
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🚨 Immediate Actions")
        for action in health_plan['immediate_actions']:
            st.write(f"• {action}")
        
        st.markdown("### 🎯 Weekly Goals")
        for goal in health_plan['weekly_goals']:
            st.write(f"• {goal}")
    
    with col2:
        st.markdown("### 📅 Monthly Targets")
        for target in health_plan['monthly_targets']:
            st.write(f"• {target}")
        
        st.markdown("### 🌟 Lifestyle Changes")
        for change in health_plan['lifestyle_changes']:
            st.write(f"• {change}")
    
    # Progress tracking
    st.markdown("### 📈 Progress Tracking")
    
    if st.button("📊 Generate Progress Report", type="primary"):
        # Calculate progress metrics
        if len(health_history) > 1:
            first_data = health_history[0]
            latest_data = health_history[-1]
            
            progress_metrics = {
                'systolic_change': latest_data.get('systolic', 0) - first_data.get('systolic', 0),
                'diastolic_change': latest_data.get('diastolic', 0) - first_data.get('diastolic', 0),
                'bmi_change': latest_data.get('bmi', 0) - first_data.get('bmi', 0),
                'assessments_completed': len(health_history)
            }
            
            st.markdown("**Your Progress So Far:**")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                delta_color = "normal" if progress_metrics['systolic_change'] <= 0 else "inverse"
                st.metric("Systolic Change", f"{progress_metrics['systolic_change']:+.0f} mmHg", delta_color=delta_color)
            
            with col2:
                delta_color = "normal" if progress_metrics['diastolic_change'] <= 0 else "inverse"
                st.metric("Diastolic Change", f"{progress_metrics['diastolic_change']:+.0f} mmHg", delta_color=delta_color)
            
            with col3:
                delta_color = "normal" if progress_metrics['bmi_change'] <= 0 else "inverse"
                st.metric("BMI Change", f"{progress_metrics['bmi_change']:+.1f}", delta_color=delta_color)
            
            st.metric("Assessments Completed", progress_metrics['assessments_completed'])
        else:
            st.info("Complete more assessments to track your progress")

def ai_health_assistant():
    """AI Health Assistant Chat Interface"""
    st.markdown('<h2 class="sub-header">🤖 AI Health Assistant</h2>', unsafe_allow_html=True)
    
    username = st.session_state.get('current_user')
    if not username:
        st.error("Please login to access this feature")
        return
    
    # Get user's health data for context
    health_history = auth.get_health_history(username)
    
    # Initialize chat history
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    # Display chat history
    chat_container = st.container()
    with chat_container:
        for message in st.session_state.chat_history:
            if message['role'] == 'user':
                st.markdown(f"**👤 You:** {message['content']}")
            else:
                st.markdown(f"**🤖 AI Assistant:** {message['content']}")
    
    # Chat input
    user_input = st.text_input("Ask me anything about your health...", key="user_input")
    
    if st.button("💬 Send Message") and user_input:
        # Add user message
        st.session_state.chat_history.append({'role': 'user', 'content': user_input})
        
        # Generate AI response based on health context
        ai_response = generate_ai_response(user_input, health_history)
        st.session_state.chat_history.append({'role': 'assistant', 'content': ai_response})
        
        st.rerun()
    
    # Quick action buttons
    st.markdown("### ⚡ Quick Actions")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("💡 Health Tips"):
            tip = generate_health_tip(health_history)
            st.session_state.chat_history.append({'role': 'assistant', 'content': f"💡 Health Tip: {tip}"})
            st.rerun()
    
    with col2:
        if st.button("📊 Risk Analysis"):
            if health_history:
                latest_data = health_history[-1]
                risk_analysis = analyzer.calculate_lifestyle_risk_score(latest_data)
                response = f"Based on your latest assessment, your risk level is {risk_analysis['risk_level']} with a score of {risk_analysis['total_score']}/100. Main risk factors: {', '.join(risk_analysis['risk_factors'][:3])}."
                st.session_state.chat_history.append({'role': 'assistant', 'content': response})
                st.rerun()
    
    with col3:
        if st.button("🎯 Recommendations"):
            if health_history:
                latest_data = health_history[-1]
                risk_analysis = analyzer.calculate_lifestyle_risk_score(latest_data)
                health_plan = analyzer.generate_personalized_health_plan(latest_data, risk_analysis)
                response = f"Here are your top 3 recommendations: {'; '.join(health_plan['immediate_actions'][:3])}"
                st.session_state.chat_history.append({'role': 'assistant', 'content': response})
                st.rerun()
    
    # Clear chat button
    if st.button("🗑️ Clear Chat History"):
        st.session_state.chat_history = []
        st.rerun()

def generate_ai_response(user_input, health_history):
    """Generate AI response based on user input and health context"""
    input_lower = user_input.lower()
    
    # Basic rule-based responses
    if any(word in input_lower for word in ['blood pressure', 'bp', 'hypertension']):
        if health_history:
            latest_data = health_history[-1]
            systolic = latest_data.get('systolic', 'N/A')
            diastolic = latest_data.get('diastolic', 'N/A')
            return f"Based on your latest reading, your blood pressure is {systolic}/{diastolic} mmHg. {'This is in the normal range.' if systolic < 120 and diastolic < 80 else 'You should monitor this closely and consult a healthcare provider.'}"
        else:
            return "I don't have your blood pressure data yet. Please complete a health assessment first."
    
    elif any(word in input_lower for word in ['bmi', 'weight', 'obese']):
        if health_history:
            latest_data = health_history[-1]
            bmi = latest_data.get('bmi', 0)
            if bmi < 18.5:
                return f"Your BMI is {bmi:.1f}, which is considered underweight. Consider consulting a healthcare provider for healthy weight gain strategies."
            elif bmi < 25:
                return f"Your BMI is {bmi:.1f}, which is in the healthy range. Keep up the good work!"
            elif bmi < 30:
                return f"Your BMI is {bmi:.1f}, which is considered overweight. Focus on diet and exercise to reach a healthier weight."
            else:
                return f"Your BMI is {bmi:.1f}, which is in the obese range. It's important to work with healthcare providers on a comprehensive weight management plan."
        else:
            return "I don't have your BMI data yet. Please complete a health assessment first."
    
    elif any(word in input_lower for word in ['exercise', 'activity', 'workout']):
        return "Regular physical activity is crucial for heart health. Aim for at least 150 minutes of moderate-intensity exercise per week, such as brisk walking, swimming, or cycling. Start slow and gradually increase intensity."
    
    elif any(word in input_lower for word in ['diet', 'food', 'eat', 'nutrition']):
        return "A heart-healthy diet includes: plenty of fruits and vegetables, whole grains, lean proteins, and low-fat dairy. Limit sodium, saturated fats, and added sugars. The DASH diet is specifically recommended for blood pressure management."
    
    elif any(word in input_lower for word in ['stress', 'anxiety', 'mental health']):
        return "Chronic stress can contribute to high blood pressure. Try stress management techniques like deep breathing, meditation, yoga, or regular physical activity. Ensure you're getting 7-8 hours of quality sleep each night."
    
    elif any(word in input_lower for word in ['smoking', 'quit smoking']):
        return "Quitting smoking is one of the best things you can do for your heart health. Within 20 minutes of quitting, your blood pressure and heart rate recover. Consider nicotine replacement therapy, counseling, or support groups to help you quit successfully."
    
    else:
        return "I'm here to help with your health questions! You can ask me about blood pressure, BMI, exercise, diet, stress management, or other health topics. For specific medical advice, always consult with your healthcare provider."

def generate_health_tip(health_history):
    """Generate personalized health tip"""
    tips = [
        "Drink plenty of water throughout the day to stay hydrated and support overall health.",
        "Take the stairs instead of the elevator when possible to increase daily activity.",
        "Practice deep breathing for 5 minutes daily to help manage stress and blood pressure.",
        "Choose whole grains over refined grains for better heart health.",
        "Aim for 7-8 hours of quality sleep each night for optimal health.",
        "Add one extra serving of vegetables to your daily meals.",
        "Take a 10-minute walk after meals to help with digestion and blood sugar control.",
        "Practice portion control by using smaller plates for your meals.",
        "Limit processed foods which are often high in sodium and unhealthy fats.",
        "Stand up and stretch every hour if you have a sedentary job."
    ]
    
    if health_history:
        latest_data = health_history[-1]
        
        # Personalized tips based on data
        if latest_data.get('systolic', 0) >= 130:
            return "Since your blood pressure is elevated, try reducing sodium intake to less than 2,300mg per day."
        
        if latest_data.get('physical_activity', 0) < 2:
            return "Start with just 10 minutes of walking daily and gradually increase to reach the recommended 150 minutes per week."
        
        if latest_data.get('bmi', 0) >= 25:
            return "Focus on portion control and eating more vegetables to help with weight management."
    
    return np.random.choice(tips)
