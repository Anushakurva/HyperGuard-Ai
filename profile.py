import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import pandas as pd
import json
from auth import auth
from offline_storage import offline_storage

def profile_page():
    """Display user profile page"""
    st.markdown('<h2 class="sub-header">👤 My Profile</h2>', unsafe_allow_html=True)
    
    username = st.session_state.get('current_user')
    if not username:
        st.error("Please login to view your profile")
        return
    
    user = auth.get_user(username)
    if not user:
        st.error("User not found")
        return
    
    # Profile tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Personal Info", "📊 Health History", "⚙️ Preferences", "💾 Data Management"])
    
    with tab1:
        personal_info_section(user, username)
    
    with tab2:
        health_history_section(username)
    
    with tab3:
        preferences_section(username)
    
    with tab4:
        data_management_section(username)

def personal_info_section(user, username):
    """Personal information section"""
    st.markdown("### 📋 Personal Information")
    
    with st.form("profile_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            full_name = st.text_input("Full Name", value=user.get("full_name", ""))
            email = st.text_input("Email", value=user.get("email", ""))
            phone = st.text_input("Phone", value=user.get("profile", {}).get("phone", ""))
        
        with col2:
            age_str = str(user.get("profile", {}).get("age", "25")).strip()
            try:
                age_value = int(age_str) if age_str and age_str.isdigit() else 25
            except (ValueError, TypeError):
                age_value = 25
            age = st.number_input("Age", min_value=1, max_value=120, value=age_value)
            
            gender_options = ["Select", "Male", "Female", "Other"]
            gender = user.get("profile", {}).get("gender", "Select")
            gender_index = gender_options.index(gender) if gender in gender_options else 0
            gender = st.selectbox("Gender", gender_options, index=gender_index)
            
            address = st.text_area("Address", value=user.get("profile", {}).get("address", ""))
        
        if st.form_submit_button("💾 Save Profile", type="primary"):
            profile_data = {
                "full_name": full_name,
                "email": email,
                "phone": phone,
                "age": str(age),
                "gender": gender,
                "address": address
            }
            
            # Update user profile
            user["full_name"] = full_name
            user["email"] = email
            user["profile"].update({
                "phone": phone,
                "age": str(age),
                "gender": gender,
                "address": address
            })
            
            if auth.update_user_profile(username, profile_data):
                st.success("✅ Profile updated successfully!")
                st.rerun()
            else:
                st.error("❌ Failed to update profile")
    
    # Account statistics
    st.markdown("### 📊 Account Statistics")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Member Since", 
                 datetime.fromisoformat(user["created_at"]).strftime("%B %d, %Y"))
    
    with col2:
        health_history = auth.get_health_history(username)
        st.metric("Health Assessments", len(health_history))
    
    with col3:
        cache_size = offline_storage.get_cache_size(username)
        st.metric("Cache Size", f"{cache_size / 1024:.1f} KB")

def health_history_section(username):
    """Health history section"""
    st.markdown("### 📊 Health History")
    
    # Get health history from auth system
    health_history = auth.get_health_history(username)
    
    if not health_history:
        st.info("No health assessments yet. Complete your first assessment to see your history here!")
        return
    
    # Convert to DataFrame for easier manipulation
    df = pd.DataFrame(health_history)
    
    # Summary statistics
    st.markdown("#### 📈 Summary Statistics")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        avg_systolic = df['systolic'].mean() if 'systolic' in df.columns else 0
        st.metric("Avg Systolic", f"{avg_systolic:.0f} mmHg")
    
    with col2:
        avg_diastolic = df['diastolic'].mean() if 'diastolic' in df.columns else 0
        st.metric("Avg Diastolic", f"{avg_diastolic:.0f} mmHg")
    
    with col3:
        avg_bmi = df['bmi'].mean() if 'bmi' in df.columns else 0
        st.metric("Avg BMI", f"{avg_bmi:.1f}")
    
    with col4:
        latest_assessment = df['timestamp'].max() if 'timestamp' in df.columns else "N/A"
        if latest_assessment != "N/A":
            latest_assessment = datetime.fromisoformat(latest_assessment).strftime("%b %d, %Y")
        st.metric("Latest Assessment", latest_assessment)
    
    # Blood pressure trend chart
    if 'systolic' in df.columns and 'diastolic' in df.columns:
        st.markdown("#### 📈 Blood Pressure Trend")
        
        # Sort by timestamp
        df['datetime'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('datetime')
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=df['datetime'],
            y=df['systolic'],
            mode='lines+markers',
            name='Systolic',
            line=dict(color='red', width=3)
        ))
        
        fig.add_trace(go.Scatter(
            x=df['datetime'],
            y=df['diastolic'],
            mode='lines+markers',
            name='Diastolic',
            line=dict(color='blue', width=3)
        ))
        
        # Add reference lines
        fig.add_hline(y=120, line_dash="dash", line_color="lightcoral", annotation_text="Normal Systolic")
        fig.add_hline(y=80, line_dash="dash", line_color="lightblue", annotation_text="Normal Diastolic")
        
        fig.update_layout(
            title="Blood Pressure Over Time",
            xaxis_title="Date",
            yaxis_title="Blood Pressure (mmHg)",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Detailed history table
    st.markdown("#### 📋 Detailed History")
    
    # Format data for display
    display_df = df.copy()
    if 'timestamp' in display_df.columns:
        display_df['Date'] = pd.to_datetime(display_df['timestamp']).dt.strftime('%Y-%m-%d %H:%M')
    
    # Select columns to display
    display_columns = ['Date', 'age', 'bmi', 'systolic', 'diastolic', 'smoking', 'alcohol', 'physical_activity']
    available_columns = [col for col in display_columns if col in display_df.columns]
    
    if available_columns:
        st.dataframe(display_df[available_columns], use_container_width=True)
    
    # Export history
    if st.button("📥 Export Health History"):
        csv = display_df[available_columns].to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name=f"health_history_{username}_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )

def preferences_section(username):
    """User preferences section"""
    st.markdown("### ⚙️ Preferences")
    
    # Load existing preferences
    preferences = offline_storage.load_user_preferences(username) or {}
    
    with st.form("preferences_form"):
        st.markdown("#### 🔔 Notifications")
        email_notifications = st.checkbox("Email Notifications", 
                                        value=preferences.get("email_notifications", True))
        assessment_reminders = st.checkbox("Assessment Reminders", 
                                        value=preferences.get("assessment_reminders", True))
        health_tips = st.checkbox("Health Tips", 
                                value=preferences.get("health_tips", True))
        
        st.markdown("#### 🎨 Display Preferences")
        theme_options = ["Light", "Dark"]
        theme = preferences.get("theme", "Light")
        theme_index = theme_options.index(theme) if theme in theme_options else 0
        theme = st.selectbox("Theme", theme_options, index=theme_index)
        
        language_options = ["English", "Spanish", "French"]
        language = preferences.get("language", "English")
        language_index = language_options.index(language) if language in language_options else 0
        language = st.selectbox("Language", language_options, index=language_index)
        
        st.markdown("#### 📊 Data & Privacy")
        data_sharing = st.checkbox("Share anonymous data for research", 
                                 value=preferences.get("data_sharing", False))
        auto_backup = st.checkbox("Automatic backup", 
                                value=preferences.get("auto_backup", True))
        
        if st.form_submit_button("💾 Save Preferences", type="primary"):
            new_preferences = {
                "email_notifications": email_notifications,
                "assessment_reminders": assessment_reminders,
                "health_tips": health_tips,
                "theme": theme,
                "language": language,
                "data_sharing": data_sharing,
                "auto_backup": auto_backup,
                "updated_at": datetime.now().isoformat()
            }
            
            if offline_storage.save_user_preferences(new_preferences, username):
                st.success("✅ Preferences saved successfully!")
                st.rerun()
            else:
                st.error("❌ Failed to save preferences")

def data_management_section(username):
    """Data management section"""
    st.markdown("### 💾 Data Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📤 Export Data")
        st.info("Export all your data for backup or migration")
        
        if st.button("📥 Export All Data", type="primary"):
            export_data = offline_storage.export_data(username)
            if export_data:
                json_data = json.dumps(export_data, indent=2)
                st.download_button(
                    label="Download JSON File",
                    data=json_data,
                    file_name=f"hyperguard_data_{username}_{datetime.now().strftime('%Y%m%d')}.json",
                    mime="application/json"
                )
            else:
                st.error("Failed to export data")
    
    with col2:
        st.markdown("#### 📥 Import Data")
        st.info("Import data from a previous backup")
        
        uploaded_file = st.file_uploader("Choose a JSON file", type=['json'])
        
        if uploaded_file is not None:
            try:
                import_data = json.loads(uploaded_file.read().decode('utf-8'))
                
                if st.button("📥 Import Data", type="primary"):
                    if offline_storage.import_data(import_data, username):
                        st.success("✅ Data imported successfully!")
                        st.rerun()
                    else:
                        st.error("❌ Failed to import data")
            except Exception as e:
                st.error(f"Invalid file format: {e}")
    
    st.markdown("---")
    
    # Cache management
    st.markdown("#### 🗑️ Cache Management")
    
    cache_size = offline_storage.get_cache_size(username)
    st.write(f"Current cache size: {cache_size / 1024:.1f} KB")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🗑️ Clear Cache", type="secondary"):
            if offline_storage.clear_cache(username):
                st.success("✅ Cache cleared successfully!")
                st.rerun()
            else:
                st.error("❌ Failed to clear cache")
    
    with col2:
        if st.button("🔄 Sync with Server", type="secondary"):
            st.info("Sync functionality will be available in future updates!")
    
    # Danger zone
    st.markdown("#### ⚠️ Danger Zone")
    st.warning("These actions are irreversible!")
    
    if st.button("🗑️ Delete All Data", type="secondary"):
        if st.session_state.get('confirm_delete'):
            # Actually delete data
            if offline_storage.clear_cache(username):
                st.success("✅ All data deleted successfully!")
                st.rerun()
            else:
                st.error("❌ Failed to delete data")
        else:
            st.session_state.confirm_delete = True
            st.error("⚠️ Click again to confirm deletion of all your data!")
            st.rerun()
