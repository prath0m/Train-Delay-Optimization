MAINTENANCE_PRESETS = {
    0: {
        "name": "No Maintenance",
        "description": "No maintenance blocks - all tracks fully operational",
        "blocks": []
    },
    1: {
        "name": "Light Maintenance (Night)",
        "description": "Minor track work during night hours (1AM-5AM)",
        "blocks": [
            {
                "section": "Station_J_to_Station_A",
                "type": "inspection",
                "start_time": 60,
                "end_time": 300,
                "speed_limit": 0.7,
                "single_line_working": False,
                "delay_minutes": 5
            }
        ]
    },
    2: {
        "name": "Track Renewal (Station A - Station J)",
        "description": "Major track work on Station A to Station J section",
        "blocks": [
            {
                "section": "Station_J_to_Station_A",
                "type": "track_renewal",
                "start_time": 120,
                "end_time": 360,
                "speed_limit": 0.3,
                "single_line_working": True,
                "delay_minutes": 15
            }
        ]
    },
    3: {
        "name": "Signaling Maintenance (Junction X - Station G)",
        "description": "Signaling system upgrade on branch line",
        "blocks": [
            {
                "section": "Junction_X_to_Station_G",
                "type": "signaling_maintenance",
                "start_time": 60,
                "end_time": 300,
                "speed_limit": 0.5,
                "single_line_working": False,
                "delay_minutes": 10
            }
        ]
    },
    4: {
        "name": "Bottleneck Section Maintenance (Lonavala)",
        "description": "Critical maintenance on steep climb section",
        "blocks": [
            {
                "section": "Station_A_to_Lonavala_Hold_Point",
                "type": "bridge_inspection",
                "start_time": 0,
                "end_time": 240,
                "speed_limit": 0.4,
                "single_line_working": True,
                "delay_minutes": 20
            }
        ]
    },
    5: {
        "name": "Multiple Blocks (Heavy Maintenance)",
        "description": "Multiple sections under maintenance simultaneously",
        "blocks": [
            {
                "section": "Station_J_to_Station_A",
                "type": "track_renewal",
                "start_time": 120,
                "end_time": 360,
                "speed_limit": 0.3,
                "single_line_working": True,
                "delay_minutes": 15
            },
            {
                "section": "Junction_X_to_Station_G",
                "type": "signaling_maintenance",
                "start_time": 60,
                "end_time": 300,
                "speed_limit": 0.5,
                "single_line_working": False,
                "delay_minutes": 10
            }
        ]
    },
    6: {
        "name": "Full Day Block (Emergency Repair)",
        "description": "Emergency repair requiring extended block on main line",
        "blocks": [
            {
                "section": "Lonavala_Hold_Point_to_Junction_Z",
                "type": "emergency_repair",
                "start_time": 0,
                "end_time": 1440,
                "speed_limit": 0.2,
                "single_line_working": True,
                "delay_minutes": 30
            }
        ]
    }
}
