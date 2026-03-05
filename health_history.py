import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np
from auth import auth
from offline_storage import offline_storage

def health_history_page():
    """Display comprehensive health history page"""
    st.markdown('<h2 class="sub-header">📊 Health History</h2>', unsafe_allow_html=True)
    
    username = st.session_state.get('current_user')
    if not username:
        st.error("Please login to view your health history")
        return
    
    # Get health history
    health_history = auth.get_health_history(username)
    
    if not health_history:
        st.info("No health assessments yet. Complete your first assessment to see your history here!")
        
        if st.button("🚀 Start Your First Assessment", type="primary", use_container_width=True):
            st.session_state.current_page = "form"
            st.rerun()
        return
    
    # Convert to DataFrame
    df = pd.DataFrame(health_history)
    df['datetime'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values('datetime')
    
    # Overview section
    overview_section(df)
    
    # Detailed analytics
    st.markdown("---")
    analytics_section(df)
    
    # Risk progression
    st.markdown("---")
    risk_progression_section(df)
    
    # Recommendations based on trends
    st.markdown("---")
    trend_recommendations_section(df)

def overview_section(df):
    """Display overview statistics"""
    st.markdown("### 📈 Health Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_assessments = len(df)
        st.metric("Total Assessments", total_assessments)
    
    with col2:
        if len(df) > 1:
            days_tracked = (df['datetime'].max() - df['datetime'].min()).days
            st.metric("Days Tracked", days_tracked)
        else:
            st.metric("Days Tracked", 1)
    
    with col3:
        if 'systolic' in df.columns:
            avg_systolic = df['systolic'].mean()
            st.metric("Avg Systolic", f"{avg_systolic:.0f} mmHg")
    
    with col4:
        if 'diastolic' in df.columns:
            avg_diastolic = df['diastolic'].mean()
            st.metric("Avg Diastolic", f"{avg_diastolic:.0f} mmHg")
    
    # Latest vs First comparison
    if len(df) > 1:
        st.markdown("#### 📊 Progress Since First Assessment")
        
        first = df.iloc[0]
        latest = df.iloc[-1]
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if 'systolic' in df.columns:
                systolic_change = latest['systolic'] - first['systolic']
                delta_color = "normal" if systolic_change <= 0 else "inverse"
                st.metric("Systolic Change", f"{systolic_change:+.0f} mmHg", delta_color=delta_color)
        
        with col2:
            if 'diastolic' in df.columns:
                diastolic_change = latest['diastolic'] - first['diastolic']
                delta_color = "normal" if diastolic_change <= 0 else "inverse"
                st.metric("Diastolic Change", f"{diastolic_change:+.0f} mmHg", delta_color=delta_color)
        
        with col3:
            if 'bmi' in df.columns:
                bmi_change = latest['bmi'] - first['bmi']
                delta_color = "normal" if bmi_change <= 0 else "inverse"
                st.metric("BMI Change", f"{bmi_change:+.1f}", delta_color=delta_color)

def analytics_section(df):
    """Display detailed analytics"""
    st.markdown("### 📊 Detailed Analytics")
    
    tab1, tab2, tab3 = st.tabs(["📈 Trends", "🎯 Risk Distribution", "📋 Correlations"])
    
    with tab1:
        trends_analysis(df)
    
    with tab2:
        risk_distribution_analysis(df)
    
    with tab3:
        correlations_analysis(df)

def trends_analysis(df):
    """Analyze health trends over time"""
    st.markdown("#### 📈 Health Trends Over Time")
    
    # Blood pressure trend
    if 'systolic' in df.columns and 'diastolic' in df.columns:
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=df['datetime'],
            y=df['systolic'],
            mode='lines+markers',
            name='Systolic BP',
            line=dict(color='red', width=3),
            hovertemplate='<b>%{fullData.name}</b><br>Date: %{x}<br>Value: %{y} mmHg<extra></extra>'
        ))
        
        fig.add_trace(go.Scatter(
            x=df['datetime'],
            y=df['diastolic'],
            mode='lines+markers',
            name='Diastolic BP',
            line=dict(color='blue', width=3),
            hovertemplate='<b>%{fullData.name}</b><br>Date: %{x}<br>Value: %{y} mmHg<extra></extra>'
        ))
        
        # Add reference lines
        fig.add_hline(y=120, line_dash="dash", line_color="lightcoral", 
                     annotation_text="Normal Systolic (120)")
        fig.add_hline(y=80, line_dash="dash", line_color="lightblue", 
                     annotation_text="Normal Diastolic (80)")
        
        fig.update_layout(
            title="Blood Pressure Trends",
            xaxis_title="Date",
            yaxis_title="Blood Pressure (mmHg)",
            height=400,
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # BMI trend
    if 'bmi' in df.columns:
        fig = px.line(df, x='datetime', y='bmi', markers=True,
                     title="BMI Trend Over Time")
        
        # Add BMI categories
        fig.add_hline(y=18.5, line_dash="dash", line_color="blue", 
                     annotation_text="Underweight (18.5)")
        fig.add_hline(y=25, line_dash="dash", line_color="orange", 
                     annotation_text="Overweight (25)")
        fig.add_hline(y=30, line_dash="dash", line_color="red", 
                     annotation_text="Obese (30)")
        
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    # Lifestyle factors trend
    lifestyle_cols = ['smoking', 'alcohol', 'physical_activity', 'salt_intake']
    available_lifestyle = [col for col in lifestyle_cols if col in df.columns]
    
    if available_lifestyle:
        st.markdown("##### 🏃 Lifestyle Factors Trend")
        
        fig = go.Figure()
        
        for factor in available_lifestyle:
            fig.add_trace(go.Scatter(
                x=df['datetime'],
                y=df[factor],
                mode='lines+markers',
                name=factor.replace('_', ' ').title(),
                hovertemplate='<b>%{fullData.name}</b><br>Date: %{x}<br>Value: %{y}<extra></extra>'
            ))
        
        fig.update_layout(
            title="Lifestyle Factors Over Time",
            xaxis_title="Date",
            yaxis_title="Score",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)

def risk_distribution_analysis(df):
    """Analyze risk distribution"""
    st.markdown("#### 🎯 Risk Distribution Analysis")
    
    # Create risk categories if not present
    if 'prediction' not in df.columns and 'systolic' in df.columns and 'diastolic' in df.columns:
        df['prediction'] = df.apply(calculate_risk_score, axis=1)
    
    if 'prediction' in df.columns:
        # Risk distribution pie chart
        risk_counts = df['prediction'].value_counts()
        risk_labels = {0: 'Normal', 1: 'Pre-Hypertension', 2: 'Stage 1', 3: 'Stage 2'}
        risk_counts.index = risk_counts.index.map(risk_labels)
        
        fig = px.pie(values=risk_counts.values, names=risk_counts.index,
                    title="Risk Distribution")
        st.plotly_chart(fig, use_container_width=True)
        
        # Risk timeline
        st.markdown("##### 📅 Risk Timeline")
        
        df['risk_label'] = df['prediction'].map(risk_labels)
        
        fig = px.scatter(df, x='datetime', y='risk_label', color='risk_label',
                        title="Risk Assessment Timeline",
                        category_orders={'risk_label': ['Normal', 'Pre-Hypertension', 'Stage 1', 'Stage 2']})
        
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)

def correlations_analysis(df):
    """Analyze correlations between factors"""
    st.markdown("#### 📋 Factor Correlations")
    
    # Select numeric columns for correlation
    numeric_cols = ['age', 'bmi', 'systolic', 'diastolic', 'smoking', 'alcohol', 
                   'physical_activity', 'salt_intake']
    available_numeric = [col for col in numeric_cols if col in df.columns]
    
    if len(available_numeric) >= 2:
        # Correlation matrix
        corr_matrix = df[available_numeric].corr()
        
        fig = px.imshow(corr_matrix, 
                       title="Correlation Matrix",
                       color_continuous_scale="RdBu",
                       aspect="auto")
        
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
        
        # Key insights
        st.markdown("##### 🔍 Key Insights")
        
        # Find strongest correlations
        corr_pairs = []
        for i in range(len(corr_matrix.columns)):
            for j in range(i+1, len(corr_matrix.columns)):
                col1, col2 = corr_matrix.columns[i], corr_matrix.columns[j]
                corr_value = corr_matrix.iloc[i, j]
                if abs(corr_value) > 0.3:  # Only show meaningful correlations
                    corr_pairs.append((col1, col2, corr_value))
        
        # Sort by absolute correlation
        corr_pairs.sort(key=lambda x: abs(x[2]), reverse=True)
        
        if corr_pairs:
            for col1, col2, corr_value in corr_pairs[:5]:  # Show top 5
                if corr_value > 0:
                    st.write(f"• **{col1.title()}** and **{col2.title()}** are positively correlated ({corr_value:.2f})")
                else:
                    st.write(f"• **{col1.title()}** and **{col2.title()}** are negatively correlated ({corr_value:.2f})")
        else:
            st.info("No strong correlations found in your data")

def risk_progression_section(df):
    """Display risk progression analysis"""
    st.markdown("### 🎯 Risk Progression Analysis")
    
    if 'prediction' not in df.columns:
        df['prediction'] = df.apply(calculate_risk_score, axis=1)
    
    # Risk progression over time
    risk_labels = {0: 'Normal', 1: 'Pre-Hypertension', 2: 'Stage 1', 3: 'Stage 2'}
    df['risk_label'] = df['prediction'].map(risk_labels)
    
    fig = px.line(df, x='datetime', y='prediction', markers=True,
                 title="Risk Score Progression",
                 labels={'prediction': 'Risk Level', 'datetime': 'Date'})
    
    fig.update_yaxes(ticktext=list(risk_labels.values()), 
                    tickvals=list(risk_labels.keys()))
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)
    
    # Risk improvement analysis
    if len(df) > 1:
        first_risk = df.iloc[0]['prediction']
        latest_risk = df.iloc[-1]['prediction']
        
        if latest_risk < first_risk:
            st.success("🎉 Great job! Your risk level has improved over time!")
        elif latest_risk > first_risk:
            st.warning("⚠️ Your risk level has increased. Consider reviewing your lifestyle factors.")
        else:
            st.info("📊 Your risk level has remained stable.")

def trend_recommendations_section(df):
    """Provide recommendations based on trends"""
    st.markdown("### 💡 Personalized Recommendations")
    
    if len(df) < 2:
        st.info("Complete more assessments to get trend-based recommendations.")
        return
    
    # Analyze trends
    recommendations = []
    
    # Blood pressure trend
    if 'systolic' in df.columns:
        systolic_trend = np.polyfit(range(len(df)), df['systolic'], 1)[0]
        if systolic_trend > 0.5:
            recommendations.append("📈 Your systolic blood pressure is trending upward. Consider reducing salt intake and increasing physical activity.")
        elif systolic_trend < -0.5:
            recommendations.append("📉 Excellent! Your systolic blood pressure is trending downward. Keep up the good work!")
    
    # BMI trend
    if 'bmi' in df.columns:
        bmi_trend = np.polyfit(range(len(df)), df['bmi'], 1)[0]
        if bmi_trend > 0.1:
            recommendations.append("⚖️ Your BMI is trending upward. Focus on diet and exercise to maintain a healthy weight.")
        elif bmi_trend < -0.1:
            recommendations.append("🏃 Great progress! Your BMI is trending in a healthy direction.")
    
    # Lifestyle factors
    if 'physical_activity' in df.columns:
        activity_trend = np.polyfit(range(len(df)), df['physical_activity'], 1)[0]
        if activity_trend < -0.1:
            recommendations.append("🏃 Your physical activity level is decreasing. Try to incorporate more exercise into your routine.")
    
    # Display recommendations
    if recommendations:
        for i, rec in enumerate(recommendations, 1):
            st.write(f"{i}. {rec}")
    else:
        st.success("🎉 Your health metrics are relatively stable. Continue maintaining your current healthy habits!")

def calculate_risk_score(row):
    """Calculate risk score based on health metrics"""
    risk_score = 0
    
    # Age factor
    if row.get('age', 0) >= 60:
        risk_score += 3
    elif row.get('age', 0) >= 45:
        risk_score += 2
    elif row.get('age', 0) >= 30:
        risk_score += 1
    
    # BMI factor
    bmi = row.get('bmi', 0)
    if bmi >= 30:
        risk_score += 3
    elif bmi >= 25:
        risk_score += 2
    elif bmi < 18.5:
        risk_score += 1
    
    # Blood pressure factor
    systolic = row.get('systolic', 0)
    diastolic = row.get('diastolic', 0)
    if systolic >= 160 or diastolic >= 100:
        risk_score += 4
    elif systolic >= 140 or diastolic >= 90:
        risk_score += 3
    elif systolic >= 130 or diastolic >= 85:
        risk_score += 2
    elif systolic >= 120 or diastolic >= 80:
        risk_score += 1
    
    # Lifestyle factors
    risk_score += row.get('smoking', 0) * 2
    risk_score += (3 - row.get('physical_activity', 1)) * 1
    risk_score += row.get('alcohol', 0) * 1
    risk_score += row.get('salt_intake', 0) * 1
    
    # Determine stage
    if risk_score >= 8:
        return 3  # Stage 2
    elif risk_score >= 6:
        return 2  # Stage 1
    elif risk_score >= 3:
        return 1  # Pre-Hypertension
    else:
        return 0  # Normal
