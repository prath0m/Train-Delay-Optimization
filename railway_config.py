# Enhanced Railway Configuration
# This file contains all the configurable parameters for the train delay optimization system

import json
from datetime import datetime, timedelta
from typing import Dict, List

# ============================================================================
# WEATHER SCENARIOS CONFIGURATION
# ============================================================================

MONSOON_SEASON_CONFIG = {
    "name": "Heavy Monsoon Season",
    "duration": "June-September", 
    "affected_sections": {
        "Station_J_Lonavala_Hold_Point": {
            "condition": "heavy_rain",
            "speed_reduction": 0.4,  # 40% speed reduction
            "delay_factor": 2.0,
            "visibility_km": 1.5,
            "risk_level": "high"
        },
        "Lonavala_Hold_Point_Junction_Z": {
            "condition": "heavy_rain", 
            "speed_reduction": 0.3,
            "delay_factor": 1.8,
            "visibility_km": 2.0,
            "risk_level": "high"
        }
    }
}

WINTER_FOG_CONFIG = {
    "name": "Winter Fog Season",
    "duration": "December-February",
    "peak_hours": "05:00-09:00",  # Morning fog
    "affected_sections": {
        "Station_A_Station_J": {
            "condition": "fog",
            "speed_reduction": 0.5,  # 50% speed reduction
            "delay_factor": 2.5,
            "visibility_km": 0.2,
            "risk_level": "critical"
        },
        "Junction_Z_Station_B": {
            "condition": "fog",
            "speed_reduction": 0.4,
            "delay_factor": 2.0,
            "visibility_km": 0.5,
            "risk_level": "high"
        }
    }
}

SUMMER_HEAT_CONFIG = {
    "name": "Extreme Summer Heat",
    "duration": "April-May",
    "peak_hours": "11:00-16:00",
    "affected_sections": {
        # Heat affects all sections but especially single track climbs
        "Station_J_Lonavala_Hold_Point": {
            "condition": "extreme_heat",
            "speed_reduction": 0.2,  # Rail expansion issues
            "delay_factor": 1.3,
            "visibility_km": 8.0,
            "risk_level": "medium"
        }
    }
}

# ============================================================================
# MAINTENANCE AND CONSTRUCTION SCHEDULES  
# ============================================================================

ANNUAL_MAINTENANCE_SCHEDULE = {
    "major_overhauls": [
        {
            "section": "Station_A_Station_J",
            "type": "track_renewal", 
            "duration_days": 15,
            "preferred_months": ["March", "April"],
            "daily_block_hours": "23:00-05:00",
            "speed_restriction": 0.3,
            "requires_single_line": True,
            "priority": "critical"
        },
        {
            "section": "Lonavala_Hold_Point_Junction_Z", 
            "type": "signaling_upgrade",
            "duration_days": 10,
            "preferred_months": ["November", "December"],
            "daily_block_hours": "01:00-05:00",
            "speed_restriction": 0.5,
            "requires_single_line": False,
            "priority": "high"
        }
    ],
    
    "routine_maintenance": [
        {
            "frequency": "weekly",
            "sections": ["all_single_track"],
            "duration_hours": 4,
            "preferred_time": "02:00-06:00",
            "speed_restriction": 0.6,
            "description": "Track inspection and minor repairs"
        },
        {
            "frequency": "monthly", 
            "sections": ["Junction_X", "Junction_Z", "Junction_Y"],
            "duration_hours": 6,
            "preferred_time": "22:00-04:00", 
            "speed_restriction": 0.4,
            "description": "Points and crossings maintenance"
        }
    ]
}

EMERGENCY_WORKS = {
    "landslide_prone_areas": [
        {
            "section": "Station_J_Lonavala_Hold_Point",
            "risk_season": "monsoon",
            "probability": 0.15,  # 15% chance during monsoon
            "typical_duration_hours": 8,
            "closure_required": True,
            "alternate_route": None  # No alternate route available
        }
    ],
    
    "bridge_inspections": [
        {
            "location": "between_Junction_Z_Station_B",
            "frequency": "quarterly",
            "duration_hours": 2,
            "speed_restriction": 0.2,  # Very slow for safety
            "advance_notice_days": 7
        }
    ]
}

# ============================================================================
# TRAIN OPERATION RULES (Indian Railways Specific)
# ============================================================================

INDIAN_RAILWAY_OPERATING_RULES = {
    "train_priorities": {
        "rajdhani_shatabdi": {"priority": 5.0, "overtaking_rights": "absolute"},
        "mail_express": {"priority": 4.0, "overtaking_rights": "conditional"},
        "passenger": {"priority": 2.0, "overtaking_rights": "limited"},
        "freight": {"priority": 1.5, "overtaking_rights": "none"},
        "goods": {"priority": 1.0, "overtaking_rights": "none"}
    },
    
    "crossing_rules": {
        "single_track_precedence": [
            "Up trains have precedence over Down trains at even-numbered loops",
            "Down trains have precedence over Up trains at odd-numbered loops",
            "Higher priority trains override normal precedence"
        ],
        "minimum_crossing_time": 5,  # Minutes between conflicting movements
        "loop_occupation_time": {
            "passenger": 10,  # Minutes
            "freight": 15,
            "goods": 20
        }
    },
    
    "speed_restrictions": {
        "curves": {
            "sharp_curve": 0.4,  # 40% of normal speed
            "moderate_curve": 0.7,
            "slight_curve": 0.9
        },
        "gradients": {
            "steep_climb": {"passenger": 0.8, "freight": 0.6, "goods": 0.5},
            "moderate_climb": {"passenger": 0.9, "freight": 0.8, "goods": 0.7},
            "descent": {"passenger": 0.9, "freight": 0.7, "goods": 0.6}  # Freight slower on descent for safety
        },
        "weather_based": {
            "heavy_rain": 0.5,
            "fog_low_visibility": 0.3,
            "extreme_heat": 0.8,
            "strong_winds": 0.7
        }
    }
}

# ============================================================================
# STATION CHARACTERISTICS AND FACILITIES
# ============================================================================

ENHANCED_STATION_CONFIG = {
    "Station_C": {
        "type": "major_junction", 
        "platforms": 6,
        "loops": 4,
        "freight_sidings": 2,
        "maintenance_depot": True,
        "crew_change_point": True,
        "average_dwell_time": {"express": 3, "passenger": 5, "freight": 12},
        "facilities": ["refreshment", "medical", "diesel_loco_shed"]
    },
    
    "Station_A": {
        "type": "intermediate_major",
        "platforms": 4, 
        "loops": 3,
        "freight_sidings": 1,
        "maintenance_depot": False,
        "crew_change_point": False,
        "average_dwell_time": {"express": 2, "passenger": 3, "freight": 8},
        "facilities": ["refreshment", "booking_office"]
    },
    
    "Station_J": {
        "type": "grade_separation_point",
        "platforms": 3,
        "loops": 2, 
        "freight_sidings": 1,
        "maintenance_depot": False,
        "crew_change_point": True,  # Before steep section
        "average_dwell_time": {"express": 5, "passenger": 7, "freight": 15},
        "facilities": ["crew_rest", "inspection_pit"],
        "notes": "Last station before Bhor Ghats climb"
    },
    
    "Lonavala_Hold_Point": {
        "type": "crossing_station",
        "platforms": 2,
        "loops": 6,  # Multiple crossing loops for single track section
        "freight_sidings": 0,
        "maintenance_depot": False, 
        "crew_change_point": True,
        "average_dwell_time": {"express": 3, "passenger": 5, "freight": 20},
        "facilities": ["crew_rest", "water_column"],
        "crossing_capacity": 4,  # Can handle 4 trains simultaneously
        "notes": "Critical crossing point in Bhor Ghats"
    },
    
    "Junction_Z": {
        "type": "major_junction",
        "platforms": 8,
        "loops": 5,
        "freight_sidings": 3,
        "maintenance_depot": True,
        "crew_change_point": True,
        "average_dwell_time": {"express": 4, "passenger": 6, "freight": 18},
        "facilities": ["major_depot", "electric_loco_shed", "coaching_yard"],
        "notes": "Major operational hub"
    },
    
    "Junction_X": {
        "type": "junction",
        "platforms": 5,
        "loops": 3,
        "freight_sidings": 2,
        "maintenance_depot": False,
        "crew_change_point": False,
        "average_dwell_time": {"express": 2, "passenger": 4, "freight": 10},
        "facilities": ["inspection_pit", "fueling"]
    },
    
    "Station_G": {
        "type": "intermediate",
        "platforms": 2,
        "loops": 2,
        "freight_sidings": 1,
        "maintenance_depot": False,
        "crew_change_point": False,
        "average_dwell_time": {"express": 1, "passenger": 2, "freight": 5},
        "facilities": ["basic"]
    },
    
    "H_Loop": {
        "type": "crossing_loop",
        "platforms": 1,
        "loops": 3,
        "freight_sidings": 0,
        "maintenance_depot": False,
        "crew_change_point": False,
        "average_dwell_time": {"express": 0, "passenger": 1, "freight": 8},
        "facilities": ["basic"],
        "notes": "Primarily for crossing operations"
    }
}

# ============================================================================
# TRAFFIC PATTERNS AND DEMAND
# ============================================================================

TRAFFIC_PATTERNS = {
    "peak_hours": {
        "morning": {
            "time_range": "06:00-10:00",
            "passenger_load_factor": 1.4,  # 40% overcrowding
            "freight_restrictions": True,  # Limited freight movement
            "priority_adjustment": {"passenger": 1.2, "express": 1.3}
        },
        "evening": {
            "time_range": "17:00-21:00", 
            "passenger_load_factor": 1.3,
            "freight_restrictions": True,
            "priority_adjustment": {"passenger": 1.2, "express": 1.3}
        }
    },
    
    "freight_corridors": {
        "preferred_hours": "22:00-06:00",  # Night operations
        "restricted_hours": "07:00-10:00,17:00-20:00",  # Peak passenger hours
        "maximum_length": {"goods": 58, "freight": 24},  # Coach/wagon limits
        "speed_limits": {"loaded": 0.6, "empty": 0.8}  # Relative to passenger trains
    },
    
    "seasonal_variations": {
        "festival_season": {
            "months": ["October", "November", "March"],
            "passenger_increase": 1.6,  # 60% more passengers
            "additional_trains": 3,
            "priority_boost": {"passenger": 1.5}
        },
        "harvest_season": {
            "months": ["April", "May", "October", "November"],
            "freight_increase": 1.4,  # 40% more freight traffic
            "commodity_types": ["grain", "sugarcane", "cotton"]
        }
    }
}

# ============================================================================
# DISRUPTION SCENARIOS
# ============================================================================

COMMON_DISRUPTION_SCENARIOS = {
    "equipment_failures": [
        {
            "type": "locomotive_failure",
            "probability": 0.08,  # 8% chance per day
            "typical_locations": ["steep_gradients", "Station_J"],
            "resolution_time": {"best": 30, "typical": 90, "worst": 240},  # Minutes
            "backup_options": ["rescue_loco", "push_pull_operation"]
        },
        {
            "type": "overhead_equipment_failure", 
            "probability": 0.05,
            "affects": "electric_trains_only",
            "resolution_time": {"best": 45, "typical": 120, "worst": 360},
            "backup_options": ["diesel_rescue", "bus_service"]
        }
    ],
    
    "signal_and_telecom": [
        {
            "type": "signal_failure",
            "probability": 0.06,
            "locations": ["Junction_Z", "Junction_X", "Junction_Y"],
            "resolution_time": {"best": 15, "typical": 45, "worst": 180},
            "fallback_method": "paper_line_clear_system",
            "additional_delay": 10  # Minutes per movement
        },
        {
            "type": "communication_failure",
            "probability": 0.04,
            "affects": "entire_section",
            "resolution_time": {"best": 20, "typical": 60, "worst": 240},
            "fallback_method": "written_authorities"
        }
    ],
    
    "external_factors": [
        {
            "type": "level_crossing_accident",
            "probability": 0.03,
            "typical_delay": 120,  # 2 hours
            "investigation_required": True,
            "affects": "single_track_sections"
        },
        {
            "type": "protest_rail_roko", 
            "probability": 0.02,
            "typical_duration": 240,  # 4 hours
            "unpredictable": True,
            "affects": "passenger_trains_primarily"
        }
    ]
}

# ============================================================================
# OPTIMIZATION PARAMETERS
# ============================================================================

OPTIMIZATION_CONFIG = {
    "solver_settings": {
        "max_time_seconds": 600,  # 10 minutes
        "num_workers": 8,
        "presolve": True,
        "search_strategy": "automatic"
    },
    
    "objective_weights": {
        "delay_minimization": 1.0,
        "passenger_satisfaction": 2.0,  # Higher weight for passenger trains
        "resource_utilization": 0.5,
        "energy_efficiency": 0.3,
        "punctuality_bonus": 1.5  # Reward for on-time performance
    },
    
    "constraints_tolerance": {
        "minimum_headway": 3,  # Minutes between trains
        "platform_occupation": 2,  # Minutes buffer
        "crew_rest_minimum": 8,  # Hours
        "fuel_depot_capacity": 0.9  # 90% utilization max
    },
    
    "performance_targets": {
        "punctuality_target": 0.85,  # 85% on-time performance
        "max_acceptable_delay": 30,   # Minutes
        "passenger_train_priority": "strict",
        "freight_efficiency": 0.75    # 75% planned speed
    }
}

# ============================================================================
# HELPER FUNCTIONS FOR CONFIGURATION
# ============================================================================

def get_weather_for_date(date: datetime):
    """Get weather configuration based on date"""
    month = date.strftime("%B")
    
    if month in ["June", "July", "August", "September"]:
        return MONSOON_SEASON_CONFIG
    elif month in ["December", "January", "February"]:
        return WINTER_FOG_CONFIG  
    elif month in ["April", "May"]:
        return SUMMER_HEAT_CONFIG
    else:
        return {"name": "Normal Weather", "affected_sections": {}}

def get_maintenance_schedule(date: datetime):
    """Get applicable maintenance works for date"""
    month = date.strftime("%B")
    day_of_week = date.weekday()
    
    applicable_works = []
    
    # Check major overhauls
    for work in ANNUAL_MAINTENANCE_SCHEDULE["major_overhauls"]:
        if month in work["preferred_months"]:
            applicable_works.append(work)
    
    # Check routine maintenance
    for work in ANNUAL_MAINTENANCE_SCHEDULE["routine_maintenance"]:
        if work["frequency"] == "weekly":
            applicable_works.append(work)
        elif work["frequency"] == "monthly" and date.day <= 7:  # First week of month
            applicable_works.append(work)
    
    return applicable_works

def get_traffic_pattern(date: datetime, time_of_day: str):
    """Get traffic pattern based on date and time"""
    hour = int(time_of_day.split(":")[0])
    month = date.strftime("%B")
    
    # Check if it's peak hours
    is_morning_peak = 6 <= hour <= 10
    is_evening_peak = 17 <= hour <= 21
    
    pattern = {"load_factor": 1.0, "restrictions": [], "priority_adjustments": {}}
    
    if is_morning_peak:
        pattern.update(TRAFFIC_PATTERNS["peak_hours"]["morning"])
    elif is_evening_peak:
        pattern.update(TRAFFIC_PATTERNS["peak_hours"]["evening"])
    
    # Check seasonal variations
    if month in TRAFFIC_PATTERNS["seasonal_variations"]["festival_season"]["months"]:
        festival_config = TRAFFIC_PATTERNS["seasonal_variations"]["festival_season"]
        pattern["load_factor"] *= festival_config["passenger_increase"]
    
    return pattern

def export_config_to_json(filename: str):
    """Export all configuration to JSON file"""
    config_data = {
        "weather_scenarios": {
            "monsoon": MONSOON_SEASON_CONFIG,
            "winter_fog": WINTER_FOG_CONFIG, 
            "summer_heat": SUMMER_HEAT_CONFIG
        },
        "maintenance_schedule": ANNUAL_MAINTENANCE_SCHEDULE,
        "emergency_works": EMERGENCY_WORKS,
        "operating_rules": INDIAN_RAILWAY_OPERATING_RULES,
        "station_config": ENHANCED_STATION_CONFIG,
        "traffic_patterns": TRAFFIC_PATTERNS,
        "disruption_scenarios": COMMON_DISRUPTION_SCENARIOS,
        "optimization_config": OPTIMIZATION_CONFIG
    }
    
    with open(filename, 'w') as f:
        json.dump(config_data, f, indent=2, default=str)
    
    print(f"Configuration exported to {filename}")

# Example usage
if __name__ == "__main__":
    # Example: Get configuration for a specific date
    test_date = datetime(2024, 7, 15)  # Monsoon season
    weather = get_weather_for_date(test_date)
    maintenance = get_maintenance_schedule(test_date)
    traffic = get_traffic_pattern(test_date, "08:30")
    
    print(f"Date: {test_date.strftime('%B %d, %Y')}")
    print(f"Weather: {weather['name']}")
    print(f"Maintenance works: {len(maintenance)}")
    print(f"Traffic pattern: Peak hours with {traffic.get('passenger_load_factor', 1.0)}x load")
    
    # Export configuration
    export_config_to_json("railway_config.json")