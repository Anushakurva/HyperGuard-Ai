import json
import os
from datetime import datetime
from typing import Dict, List, Optional
import streamlit as st
import numpy as np

class OfflineStorage:
    def __init__(self):
        self.cache_dir = "offline_cache"
        self.ensure_cache_directory()
    
    def convert_numpy_types(self, obj):
        """Convert numpy types to JSON serializable types"""
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, dict):
            return {key: self.convert_numpy_types(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self.convert_numpy_types(item) for item in obj]
        else:
            return obj
    
    def ensure_cache_directory(self):
        """Ensure cache directory exists"""
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
    
    def save_to_cache(self, key: str, data: Dict, username: str = None) -> bool:
        """Save data to offline cache"""
        try:
            filename = f"{key}.json"
            if username:
                filename = f"{username}_{filename}"
            
            filepath = os.path.join(self.cache_dir, filename)
            
            # Convert numpy types to JSON serializable types
            serializable_data = self.convert_numpy_types(data)
            
            cache_data = {
                "data": serializable_data,
                "timestamp": datetime.now().isoformat(),
                "username": username
            }
            
            with open(filepath, 'w') as f:
                json.dump(cache_data, f, indent=2)
            
            return True
        except Exception as e:
            st.error(f"Failed to save to cache: {e}")
            return False
    
    def load_from_cache(self, key: str, username: str = None) -> Optional[Dict]:
        """Load data from offline cache"""
        try:
            filename = f"{key}.json"
            if username:
                filename = f"{username}_{filename}"
            
            filepath = os.path.join(self.cache_dir, filename)
            
            if not os.path.exists(filepath):
                return None
            
            with open(filepath, 'r') as f:
                cache_data = json.load(f)
            
            return cache_data.get("data")
        except Exception as e:
            st.error(f"Failed to load from cache: {e}")
            return None
    
    def save_health_assessment(self, health_data: Dict, prediction_result: Dict, username: str) -> bool:
        """Save health assessment to offline storage"""
        assessment_data = {
            "health_data": health_data,
            "prediction": prediction_result,
            "assessment_id": f"assessment_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        }
        
        return self.save_to_cache("health_assessment", assessment_data, username)
    
    def get_health_assessments(self, username: str) -> List[Dict]:
        """Get all health assessments for a user"""
        assessments = []
        
        try:
            # List all cache files for the user
            for filename in os.listdir(self.cache_dir):
                if filename.startswith(f"{username}_health_assessment_") and filename.endswith(".json"):
                    filepath = os.path.join(self.cache_dir, filename)
                    with open(filepath, 'r') as f:
                        cache_data = json.load(f)
                        assessments.append(cache_data.get("data"))
        except Exception as e:
            st.error(f"Failed to load assessments: {e}")
        
        return sorted(assessments, key=lambda x: x.get("timestamp", ""), reverse=True)
    
    def save_user_preferences(self, preferences: Dict, username: str) -> bool:
        """Save user preferences to offline storage"""
        return self.save_to_cache("preferences", preferences, username)
    
    def load_user_preferences(self, username: str) -> Optional[Dict]:
        """Load user preferences from offline storage"""
        return self.load_from_cache("preferences", username)
    
    def export_data(self, username: str) -> Optional[Dict]:
        """Export all user data for backup"""
        try:
            export_data = {
                "username": username,
                "export_date": datetime.now().isoformat(),
                "preferences": self.load_user_preferences(username),
                "health_assessments": self.get_health_assessments(username)
            }
            
            return export_data
        except Exception as e:
            st.error(f"Failed to export data: {e}")
            return None
    
    def import_data(self, import_data: Dict, username: str) -> bool:
        """Import user data from backup"""
        try:
            if import_data.get("username") != username:
                st.error("Import data is for a different user")
                return False
            
            # Import preferences
            if "preferences" in import_data:
                self.save_user_preferences(import_data["preferences"], username)
            
            # Import health assessments
            if "health_assessments" in import_data:
                for assessment in import_data["health_assessments"]:
                    self.save_health_assessment(
                        assessment.get("health_data", {}),
                        assessment.get("prediction", {}),
                        username
                    )
            
            return True
        except Exception as e:
            st.error(f"Failed to import data: {e}")
            return False
    
    def clear_cache(self, username: str = None) -> bool:
        """Clear offline cache"""
        try:
            if username:
                # Clear only user's cache files
                for filename in os.listdir(self.cache_dir):
                    if filename.startswith(f"{username}_"):
                        os.remove(os.path.join(self.cache_dir, filename))
            else:
                # Clear all cache
                for filename in os.listdir(self.cache_dir):
                    os.remove(os.path.join(self.cache_dir, filename))
            
            return True
        except Exception as e:
            st.error(f"Failed to clear cache: {e}")
            return False
    
    def get_cache_size(self, username: str = None) -> int:
        """Get cache size in bytes"""
        total_size = 0
        
        try:
            for filename in os.listdir(self.cache_dir):
                if username is None or filename.startswith(f"{username}_"):
                    filepath = os.path.join(self.cache_dir, filename)
                    total_size += os.path.getsize(filepath)
        except:
            pass
        
        return total_size

# Initialize offline storage
offline_storage = OfflineStorage()

def sync_with_server():
    """Sync offline data with server (placeholder for future implementation)"""
    if st.button("🔄 Sync with Server", help="Sync your offline data with the server"):
        st.info("Sync functionality will be available in future updates!")
        return False
    return False

def show_offline_status():
    """Display offline status indicator"""
    is_online = True  # Placeholder for actual online detection
    
    if is_online:
        st.success("🟢 Online Mode")
    else:
        st.warning("🟡 Offline Mode - Data saved locally")
    
    return is_online
