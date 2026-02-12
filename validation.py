"""
Input validation and thresholds for Sleep Disorder prediction.
Defines acceptable ranges for all input parameters.
"""

# Input parameter thresholds and validation rules
PARAMETER_THRESHOLDS = {
    'Age': {
        'min': 18,
        'max': 100,
        'type': 'int',
        'unit': 'years',
        'description': 'Patient age in years',
        'warning_low': 20,
        'warning_high': 80
    },
    'Sleep Duration': {
        'min': 0.0,
        'max': 24.0,
        'type': 'float',
        'unit': 'hours',
        'description': 'Average hours of sleep per night',
        'warning_low': 5.0,
        'warning_high': 10.0,
        'optimal_min': 7.0,
        'optimal_max': 9.0
    },
    'Quality of Sleep': {
        'min': 1,
        'max': 10,
        'type': 'int',
        'unit': 'scale',
        'description': 'Sleep quality rating (1-10)',
        'warning_low': 4,
        'warning_high': None,
        'optimal_min': 7
    },
    'Physical Activity Level': {
        'min': 0,
        'max': 180,
        'type': 'int',
        'unit': 'minutes/day',
        'description': 'Daily physical activity in minutes',
        'warning_low': 30,
        'warning_high': 120,
        'optimal_min': 30,
        'optimal_max': 60
    },
    'Stress Level': {
        'min': 1,
        'max': 10,
        'type': 'int',
        'unit': 'scale',
        'description': 'Stress level rating (1-10)',
        'warning_low': None,
        'warning_high': 7,
        'optimal_max': 5
    },
    'Heart Rate': {
        'min': 40,
        'max': 200,
        'type': 'int',
        'unit': 'bpm',
        'description': 'Resting heart rate in beats per minute',
        'warning_low': 50,
        'warning_high': 100,
        'optimal_min': 60,
        'optimal_max': 80
    },
    'Daily Steps': {
        'min': 0,
        'max': 50000,
        'type': 'int',
        'unit': 'steps',
        'description': 'Number of steps per day',
        'warning_low': 5000,
        'warning_high': 20000,
        'optimal_min': 8000,
        'optimal_max': 12000
    },
    'Gender_Encoded': {
        'min': 0,
        'max': 1,
        'type': 'int',
        'unit': 'encoded',
        'description': 'Gender (0: Female, 1: Male)',
        'options': {0: 'Female', 1: 'Male'}
    },
    'BMI_Encoded': {
        'min': 0,
        'max': 3,
        'type': 'int',
        'unit': 'encoded',
        'description': 'BMI Category',
        'options': {
            0: 'Normal',
            1: 'Normal Weight',
            2: 'Obese',
            3: 'Overweight'
        }
    },
    'BP_Systolic': {
        'min': 70,
        'max': 200,
        'type': 'int',
        'unit': 'mmHg',
        'description': 'Systolic blood pressure',
        'warning_low': 90,
        'warning_high': 140,
        'optimal_min': 90,
        'optimal_max': 120
    },
    'BP_Diastolic': {
        'min': 40,
        'max': 130,
        'type': 'int',
        'unit': 'mmHg',
        'description': 'Diastolic blood pressure',
        'warning_low': 60,
        'warning_high': 90,
        'optimal_min': 60,
        'optimal_max': 80
    }
}


def validate_parameter(param_name, value):
    """
    Validate a single parameter value.
    
    Args:
        param_name: Name of the parameter
        value: Value to validate
        
    Returns:
        Tuple of (is_valid: bool, message: str, warnings: list)
    """
    if param_name not in PARAMETER_THRESHOLDS:
        return False, f"Unknown parameter: {param_name}", []
    
    threshold = PARAMETER_THRESHOLDS[param_name]
    warnings = []
    
    # Type conversion and validation
    try:
        if threshold['type'] == 'int':
            value = int(value)
        elif threshold['type'] == 'float':
            value = float(value)
    except (ValueError, TypeError):
        return False, f"{param_name} must be a {threshold['type']}", []
    
    # Range validation
    if value < threshold['min'] or value > threshold['max']:
        return False, f"{param_name} must be between {threshold['min']} and {threshold['max']} {threshold['unit']}", []
    
    # Warning checks
    if 'warning_low' in threshold and threshold['warning_low'] is not None:
        if value < threshold['warning_low']:
            warnings.append(f"{param_name} is below recommended minimum ({threshold['warning_low']} {threshold['unit']})")
    
    if 'warning_high' in threshold and threshold['warning_high'] is not None:
        if value > threshold['warning_high']:
            warnings.append(f"{param_name} is above recommended maximum ({threshold['warning_high']} {threshold['unit']})")
    
    # Optimal range checks
    if 'optimal_min' in threshold and value < threshold['optimal_min']:
        warnings.append(f"💡 Optimal {param_name} is ≥ {threshold['optimal_min']} {threshold['unit']}")
    
    if 'optimal_max' in threshold and value > threshold['optimal_max']:
        warnings.append(f"💡 Optimal {param_name} is ≤ {threshold['optimal_max']} {threshold['unit']}")
    
    return True, "Valid", warnings


def validate_all_parameters(data):
    """
    Validate all input parameters.
    
    Args:
        data: Dictionary of parameter names and values
        
    Returns:
        Tuple of (is_valid: bool, errors: dict, warnings: dict)
    """
    errors = {}
    all_warnings = {}
    
    # Check for missing parameters
    for param_name in PARAMETER_THRESHOLDS.keys():
        if param_name not in data:
            errors[param_name] = f"Missing required parameter: {param_name}"
    
    # Validate each parameter
    for param_name, value in data.items():
        is_valid, message, warnings = validate_parameter(param_name, value)
        
        if not is_valid:
            errors[param_name] = message
        
        if warnings:
            all_warnings[param_name] = warnings
    
    is_valid = len(errors) == 0
    
    return is_valid, errors, all_warnings


def get_risk_assessment(data):
    """
    Assess overall risk based on input parameters.
    
    Args:
        data: Dictionary of parameter names and values
        
    Returns:
        Dictionary with risk assessment
    """
    risk_factors = []
    risk_score = 0
    
    # Sleep Duration
    if data.get('Sleep Duration', 0) < 6:
        risk_factors.append("Insufficient sleep duration (<6 hours)")
        risk_score += 2
    elif data.get('Sleep Duration', 0) < 7:
        risk_factors.append("Below optimal sleep duration")
        risk_score += 1
    
    # Quality of Sleep
    if data.get('Quality of Sleep', 10) < 5:
        risk_factors.append("Poor sleep quality")
        risk_score += 2
    elif data.get('Quality of Sleep', 10) < 7:
        risk_factors.append("Below average sleep quality")
        risk_score += 1
    
    # Stress Level
    if data.get('Stress Level', 0) > 7:
        risk_factors.append("High stress level")
        risk_score += 2
    elif data.get('Stress Level', 0) > 5:
        risk_factors.append("Elevated stress level")
        risk_score += 1
    
    # Physical Activity
    if data.get('Physical Activity Level', 0) < 30:
        risk_factors.append("Insufficient physical activity")
        risk_score += 1
    
    # BMI
    if data.get('BMI_Encoded', 0) in [2, 3]:  # Obese or Overweight
        risk_factors.append("Elevated BMI")
        risk_score += 1
    
    # Blood Pressure
    if data.get('BP_Systolic', 0) > 140 or data.get('BP_Diastolic', 0) > 90:
        risk_factors.append("Elevated blood pressure")
        risk_score += 2
    elif data.get('BP_Systolic', 0) > 130 or data.get('BP_Diastolic', 0) > 85:
        risk_factors.append("Pre-hypertension")
        risk_score += 1
    
    # Heart Rate
    if data.get('Heart Rate', 0) > 100:
        risk_factors.append("Elevated resting heart rate")
        risk_score += 1
    
    # Daily Steps
    if data.get('Daily Steps', 0) < 5000:
        risk_factors.append("Low daily activity (steps)")
        risk_score += 1
    
    # Determine risk level
    if risk_score >= 6:
        risk_level = "High"
        risk_color = "danger"
    elif risk_score >= 3:
        risk_level = "Moderate"
        risk_color = "warning"
    else:
        risk_level = "Low"
        risk_color = "success"
    
    return {
        'risk_level': risk_level,
        'risk_score': risk_score,
        'risk_color': risk_color,
        'risk_factors': risk_factors,
        'total_factors': len(risk_factors)
    }


def get_recommendations(data):
    """
    Generate health recommendations based on input parameters.
    
    Args:
        data: Dictionary of parameter names and values
        
    Returns:
        List of recommendations
    """
    recommendations = []
    
    # Sleep Duration
    if data.get('Sleep Duration', 0) < 7:
        recommendations.append({
            'category': 'Sleep',
            'icon': '😴',
            'title': 'Increase Sleep Duration',
            'description': 'Aim for 7-9 hours of sleep per night for optimal health.'
        })
    
    # Quality of Sleep
    if data.get('Quality of Sleep', 10) < 7:
        recommendations.append({
            'category': 'Sleep',
            'icon': '🛏️',
            'title': 'Improve Sleep Quality',
            'description': 'Establish a consistent sleep schedule and create a relaxing bedtime routine.'
        })
    
    # Stress Level
    if data.get('Stress Level', 0) > 5:
        recommendations.append({
            'category': 'Mental Health',
            'icon': '🧘',
            'title': 'Manage Stress',
            'description': 'Practice relaxation techniques like meditation, yoga, or deep breathing exercises.'
        })
    
    # Physical Activity
    if data.get('Physical Activity Level', 0) < 30:
        recommendations.append({
            'category': 'Exercise',
            'icon': '🏃',
            'title': 'Increase Physical Activity',
            'description': 'Aim for at least 30 minutes of moderate exercise daily.'
        })
    
    # Daily Steps
    if data.get('Daily Steps', 0) < 8000:
        recommendations.append({
            'category': 'Exercise',
            'icon': '👟',
            'title': 'Increase Daily Steps',
            'description': 'Target 8,000-10,000 steps per day for better cardiovascular health.'
        })
    
    # BMI
    if data.get('BMI_Encoded', 0) in [2, 3]:
        recommendations.append({
            'category': 'Nutrition',
            'icon': '🥗',
            'title': 'Weight Management',
            'description': 'Consult a healthcare provider about healthy weight management strategies.'
        })
    
    # Blood Pressure
    if data.get('BP_Systolic', 0) > 130 or data.get('BP_Diastolic', 0) > 85:
        recommendations.append({
            'category': 'Health',
            'icon': '❤️',
            'title': 'Monitor Blood Pressure',
            'description': 'Consult a healthcare provider about your blood pressure. Reduce sodium intake and increase physical activity.'
        })
    
    # Heart Rate
    if data.get('Heart Rate', 0) > 90:
        recommendations.append({
            'category': 'Health',
            'icon': '💓',
            'title': 'Improve Cardiovascular Health',
            'description': 'Regular aerobic exercise can help lower resting heart rate.'
        })
    
    return recommendations


if __name__ == "__main__":
    """Test validation functionality."""
    print("Testing validation...")
    
    # Test data
    test_data = {
        'Age': 35,
        'Sleep Duration': 6.5,
        'Quality of Sleep': 6,
        'Physical Activity Level': 45,
        'Stress Level': 7,
        'Heart Rate': 75,
        'Daily Steps': 5000,
        'Gender_Encoded': 1,
        'BMI_Encoded': 2,
        'BP_Systolic': 135,
        'BP_Diastolic': 88
    }
    
    # Validate all
    is_valid, errors, warnings = validate_all_parameters(test_data)
    print(f"\nValidation: {'Valid' if is_valid else 'Invalid'}")
    
    if errors:
        print("\nErrors:")
        for param, error in errors.items():
            print(f"  - {param}: {error}")
    
    if warnings:
        print("\nWarnings:")
        for param, warning_list in warnings.items():
            print(f"  {param}:")
            for warning in warning_list:
                print(f"    {warning}")
    
    # Risk assessment
    risk = get_risk_assessment(test_data)
    print(f"\nRisk Assessment:")
    print(f"  Level: {risk['risk_level']}")
    print(f"  Score: {risk['risk_score']}")
    print(f"  Factors: {risk['total_factors']}")
    for factor in risk['risk_factors']:
        print(f"    - {factor}")
    
    # Recommendations
    recs = get_recommendations(test_data)
    print(f"\nRecommendations ({len(recs)}):")
    for rec in recs:
        print(f"  {rec['icon']} {rec['title']}")
        print(f"     {rec['description']}")
