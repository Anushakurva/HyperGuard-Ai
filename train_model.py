import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, accuracy_score
import joblib

def generate_synthetic_data(n_samples=1000):
    """Generate synthetic hypertension data for training"""
    np.random.seed(42)
    
    data = []
    
    for i in range(n_samples):
        # Generate age
        age = np.random.randint(18, 80)
        
        # Generate BMI based on age distribution
        if age < 30:
            bmi = np.random.normal(24, 4)
        elif age < 50:
            bmi = np.random.normal(27, 5)
        else:
            bmi = np.random.normal(28, 5)
        
        bmi = np.clip(bmi, 16, 40)
        
        # Generate blood pressure based on age and BMI
        base_systolic = 90 + age * 0.5 + (bmi - 22) * 2
        base_diastolic = 60 + age * 0.3 + (bmi - 22) * 1.5
        
        # Add random variation
        systolic = np.clip(base_systolic + np.random.normal(0, 10), 80, 200)
        diastolic = np.clip(base_diastolic + np.random.normal(0, 8), 40, 130)
        
        # Lifestyle factors
        smoking = np.random.choice([0, 1], p=[0.7, 0.3])
        alcohol = np.random.choice([0, 1, 2, 3], p=[0.3, 0.4, 0.2, 0.1])
        physical_activity = np.random.choice([0, 1, 2, 3], p=[0.2, 0.3, 0.3, 0.2])
        salt_intake = np.random.choice([0, 1, 2], p=[0.3, 0.4, 0.3])
        
        # Determine hypertension stage based on blood pressure
        if systolic >= 160 or diastolic >= 100:
            stage = 3  # Stage 2
        elif systolic >= 140 or diastolic >= 90:
            stage = 2  # Stage 1
        elif systolic >= 130 or diastolic >= 85:
            stage = 1  # Pre-Hypertension
        else:
            stage = 0  # Normal
        
        # Adjust stage based on lifestyle factors
        lifestyle_factor = smoking * 1 + (3 - physical_activity) * 0.5 + alcohol * 0.3 + salt_intake * 0.3
        
        if lifestyle_factor > 2 and stage < 2:
            stage = min(stage + 1, 3)
        
        data.append([age, bmi, systolic, diastolic, smoking, alcohol, physical_activity, salt_intake, stage])
    
    df = pd.DataFrame(data, columns=[
        'age', 'bmi', 'systolic', 'diastolic', 'smoking', 'alcohol', 'physical_activity', 'salt_intake', 'stage'
    ])
    
    return df

def train_model():
    """Train the hypertension prediction model"""
    print("🏥 HyperGuard AI - Model Training")
    print("=" * 50)
    
    # Generate synthetic data
    print("📊 Generating synthetic training data...")
    df = generate_synthetic_data(2000)
    
    # Prepare features and target
    features = ['age', 'bmi', 'systolic', 'diastolic', 'smoking', 'alcohol', 'physical_activity', 'salt_intake']
    X = df[features]
    y = df['stage']
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Train model
    print("🤖 Training Random Forest model...")
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        random_state=42,
        class_weight='balanced'
    )
    
    model.fit(X_train_scaled, y_train)
    
    # Evaluate model
    y_pred = model.predict(X_test_scaled)
    accuracy = accuracy_score(y_test, y_pred)
    
    print(f"\n✅ Model trained successfully!")
    print(f"📈 Accuracy: {accuracy:.3f}")
    
    # Feature importance
    feature_importance = pd.DataFrame({
        'feature': features,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    print("\n🎯 Feature Importance:")
    for _, row in feature_importance.iterrows():
        print(f"  {row['feature']}: {row['importance']:.3f}")
    
    # Classification report
    print("\n📋 Classification Report:")
    stage_names = ['Normal', 'Pre-Hypertension', 'Stage 1', 'Stage 2']
    print(classification_report(y_test, y_pred, target_names=stage_names))
    
    # Save model and scaler
    joblib.dump(model, 'hypertension_model.pkl')
    joblib.dump(scaler, 'scaler.pkl')
    
    print("\n💾 Model saved as 'hypertension_model.pkl'")
    print("💾 Scaler saved as 'scaler.pkl'")
    
    # Save sample data for reference
    df.to_csv('sample_data.csv', index=False)
    print("💾 Sample data saved as 'sample_data.csv'")
    
    return model, scaler

def test_model():
    """Test the trained model with sample inputs"""
    try:
        model = joblib.load('hypertension_model.pkl')
        scaler = joblib.load('scaler.pkl')
        
        # Test cases
        test_cases = [
            # [age, bmi, systolic, diastolic, smoking, alcohol, physical_activity, salt_intake]
            [25, 22.5, 115, 75, 0, 0, 3, 0],  # Healthy young person
            [45, 28.5, 135, 88, 1, 2, 1, 2],  # Middle-aged with risk factors
            [65, 32.0, 155, 95, 1, 3, 0, 2],  # Older person with high risk
            [35, 24.0, 125, 82, 0, 1, 2, 1],  # Moderate risk
        ]
        
        stage_names = ['Normal', 'Pre-Hypertension', 'Stage 1', 'Stage 2']
        
        print("\n🧪 Testing Model with Sample Cases:")
        print("-" * 50)
        
        for i, test_case in enumerate(test_cases, 1):
            features = np.array([test_case])
            features_scaled = scaler.transform(features)
            prediction = model.predict(features_scaled)[0]
            
            print(f"Case {i}: Age={test_case[0]}, BMI={test_case[1]}, BP={test_case[2]}/{test_case[3]}")
            print(f"  Prediction: {stage_names[prediction]}")
            print()
        
        print("✅ Model testing completed!")
        
    except FileNotFoundError:
        print("❌ Model files not found. Please run train_model() first.")

if __name__ == "__main__":
    # Train the model
    model, scaler = train_model()
    
    # Test the model
    test_model()
