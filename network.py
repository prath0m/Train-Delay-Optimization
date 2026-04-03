from enums import TrainType

STATIONS = [
    "Karjat_Hold_Point", "Station_C", "Station_J", "Station_A",
    "Lonavala_Hold_Point", "Junction_Z", "Station_B", "Station_H",
    "H_Loop", "Junction_X", "Station_G", "Station_D", "Junction_Y"
]

TRACKS = [
    # Main line: Karjat to Station C
    {"from": "Karjat_Hold_Point", "to": "Station_C", "length_km": 8, "tracks": 2,
     "min_travel_time": 8, "gradient": "level", "electrified": True, "bottleneck": False},

    # Section 1: Station C → Station J (12 km) → Station A (18 km), double track, level
    {"from": "Station_C", "to": "Station_J", "length_km": 12, "tracks": 2,
     "min_travel_time": 10, "gradient": "level", "electrified": True, "bottleneck": False},
    {"from": "Station_J", "to": "Station_A", "length_km": 18, "tracks": 2,
     "min_travel_time": 15, "gradient": "level", "electrified": True, "bottleneck": False},

    # Section 2: CRITICAL BOTTLENECK - steep climb (Bhor Ghat), single track
    {"from": "Station_A", "to": "Lonavala_Hold_Point", "length_km": 25, "tracks": 1,
     "min_travel_time": 45, "gradient": "steep_climb", "electrified": True, "bottleneck": True,
     "crossing_loops": 2, "max_hourly_capacity": 4},

    # Section 3: CRITICAL BOTTLENECK - bridged single-track section to Junction Z
    {"from": "Lonavala_Hold_Point", "to": "Junction_Z", "length_km": 7, "tracks": 1,
     "min_travel_time": 12, "gradient": "steep_climb", "electrified": True, "bottleneck": True,
     "crossing_loops": 3, "max_hourly_capacity": 6,
     "notes": "Bridged section - highest priority for capacity"},

    # Section 4: Junction Z to Station B (freight branch, 13 km double track)
    {"from": "Junction_Z", "to": "Station_B", "length_km": 13, "tracks": 2,
     "min_travel_time": 11, "gradient": "level", "electrified": True, "bottleneck": False},

    # Section 5: Junction Z to Station H (9 km double track, main through route)
    {"from": "Junction_Z", "to": "Station_H", "length_km": 9, "tracks": 2,
     "min_travel_time": 8, "gradient": "level", "electrified": True, "bottleneck": False},

    # Section 6: Station H siding - H Loop (crossing loop, single track)
    {"from": "Station_H", "to": "H_Loop", "length_km": 2, "tracks": 1,
     "min_travel_time": 4, "gradient": "level", "electrified": True, "bottleneck": True,
     "crossing_loops": 4, "max_hourly_capacity": 4,
     "notes": "Crossing loop at Station H"},

    # Section 7: Station H to Junction X (6 km double track)
    {"from": "Station_H", "to": "Junction_X", "length_km": 6, "tracks": 2,
     "min_travel_time": 6, "gradient": "level", "electrified": True, "bottleneck": False},

    # Section 8: Down branch - Junction X to Station G (11 km double track)
    {"from": "Junction_X", "to": "Station_G", "length_km": 11, "tracks": 2,
     "min_travel_time": 9, "gradient": "level", "electrified": True, "bottleneck": False},

    # Section 9: Up branch - Junction X to Station D (9 km double track)
    {"from": "Junction_X", "to": "Station_D", "length_km": 9, "tracks": 2,
     "min_travel_time": 8, "gradient": "level", "electrified": True, "bottleneck": False},

    # Section 10: Station D to Junction Y (7 km double track)
    {"from": "Station_D", "to": "Junction_Y", "length_km": 7, "tracks": 2,
     "min_travel_time": 7, "gradient": "level", "electrified": True, "bottleneck": False},
]

TRAINS = [
    # Premium trains (highest priority)
    {"id": "12301_Howrah_Rajdhani", "type": TrainType.SUPERFAST, "priority": 5.0,
     "route": ["Station_C", "Station_J", "Station_A", "Lonavala_Hold_Point", "Junction_Z", "Station_B"],
     "scheduled_departure": 300, "passenger_load": 1.0, "coaches": 18},

    {"id": "22301_Shatabdi_Express", "type": TrainType.SUPERFAST, "priority": 4.5,
     "route": ["Station_C", "Station_J", "Station_A", "Lonavala_Hold_Point", "Junction_Z"],
     "scheduled_departure": 360, "passenger_load": 0.9, "coaches": 16},

    # Express trains
    {"id": "11301_Udyan_Express", "type": TrainType.EXPRESS, "priority": 4.0,
     "route": ["Station_C", "Station_J", "Station_A", "Lonavala_Hold_Point", "Junction_Z", "Station_H", "Junction_X"],
     "scheduled_departure": 420, "passenger_load": 1.1, "coaches": 22},

    {"id": "17301_Mumbai_Mail", "type": TrainType.MAIL_EXPRESS, "priority": 3.5,
     "route": ["Station_B", "Junction_Z", "Lonavala_Hold_Point", "Station_A", "Station_J", "Station_C"],
     "scheduled_departure": 480, "passenger_load": 1.2, "coaches": 20},

    # Passenger trains
    {"id": "51301_Local_Passenger", "type": TrainType.PASSENGER, "priority": 2.0,
     "route": ["Station_C", "Station_J", "Station_A", "Lonavala_Hold_Point"],
     "scheduled_departure": 390, "passenger_load": 1.4, "coaches": 12},

    {"id": "59301_Mixed_Passenger", "type": TrainType.PASSENGER, "priority": 1.8,
     "route": ["Junction_Z", "Station_H", "Junction_X", "Station_G"],
     "scheduled_departure": 450, "passenger_load": 1.3, "coaches": 10},

    # Freight trains
    {"id": "56301_Container_Freight", "type": TrainType.FREIGHT, "priority": 1.5,
     "route": ["Karjat_Hold_Point", "Station_C", "Station_J", "Station_A"],
     "scheduled_departure": 240, "freight_wagons": 45, "commodity": "containers"},

    {"id": "52301_Coal_Goods", "type": TrainType.GOODS, "priority": 1.0,
     "route": ["Karjat_Hold_Point", "Station_C", "Station_J"],
     "scheduled_departure": 180, "freight_wagons": 58, "commodity": "coal"},
]

STATION_CONFIG = {
    "Karjat_Hold_Point": {
        "type": "freight_terminal", "platforms": 2, "loops": 4, "freight_yards": 4,
        "crew_change": False, "maintenance_depot": False, "water_column": True,
        "dwell_times": {"superfast": 0, "express": 0, "passenger": 0, "freight": 20, "goods": 25},
        "notes": "Freight entry point"
    },
    "Station_C": {
        "type": "major_junction", "platforms": 6, "loops": 4, "freight_yards": 3,
        "crew_change": True, "maintenance_depot": True, "water_column": True,
        "dwell_times": {"superfast": 3, "express": 4, "passenger": 6, "freight": 15, "mail_express": 4},
        "notes": "Major hub - prioritize through traffic"
    },
    "Station_A": {
        "type": "intermediate_major", "platforms": 4, "loops": 3, "freight_yards": 2,
        "crew_change": False, "maintenance_depot": False, "water_column": True,
        "dwell_times": {"superfast": 2, "express": 3, "passenger": 4, "freight": 10, "mail_express": 2},
        "notes": "Intermediate stop"
    },
    "Station_J": {
        "type": "grade_change_point", "platforms": 3, "loops": 3, "freight_yards": 1,
        "crew_change": True, "maintenance_depot": False, "water_column": True,
        "dwell_times": {"superfast": 5, "express": 6, "passenger": 8, "freight": 20, "mail_express": 6},
        "notes": "Last station before steep climb - critical for speed control"
    },
    "Lonavala_Hold_Point": {
        "type": "crossing_station", "platforms": 2, "loops": 8, "freight_yards": 1,
        "crew_change": True, "maintenance_depot": False, "water_column": True,
        "dwell_times": {"superfast": 4, "express": 5, "passenger": 7, "freight": 28, "mail_express": 5},
        "crossing_capacity": 6, "notes": "Critical bottleneck - optimize for crossing coordination"
    },
    "Junction_Z": {
        "type": "major_junction", "platforms": 8, "loops": 6, "freight_yards": 4,
        "crew_change": True, "maintenance_depot": True, "water_column": True,
        "dwell_times": {"superfast": 4, "express": 5, "passenger": 7, "freight": 18, "mail_express": 5},
        "notes": "Major distribution hub - excellent capacity"
    },
    "Station_B": {
        "type": "intermediate_junction", "platforms": 4, "loops": 3, "freight_yards": 2,
        "crew_change": False, "maintenance_depot": False, "water_column": True,
        "dwell_times": {"superfast": 2, "express": 3, "passenger": 5, "freight": 12, "mail_express": 3}
    },
    "Station_H": {
        "type": "through_station", "platforms": 3, "loops": 4, "freight_yards": 1,
        "crew_change": False, "maintenance_depot": False, "water_column": True,
        "dwell_times": {"superfast": 2, "express": 3, "passenger": 5, "freight": 12, "mail_express": 3},
        "notes": "Station H with H_Loop crossing loop siding"
    },
    "H_Loop": {
        "type": "crossing_loop", "platforms": 1, "loops": 4, "freight_yards": 0,
        "crew_change": False, "maintenance_depot": False, "water_column": False,
        "dwell_times": {"superfast": 2, "express": 3, "passenger": 4, "freight": 10, "mail_express": 2},
        "notes": "Crossing loop siding at Station H"
    },
    "Junction_X": {
        "type": "branch_junction", "platforms": 3, "loops": 2, "freight_yards": 1,
        "crew_change": False, "maintenance_depot": False, "water_column": False,
        "dwell_times": {"superfast": 2, "express": 3, "passenger": 4, "freight": 10, "mail_express": 2}
    },
    "Station_G": {
        "type": "branch_station", "platforms": 2, "loops": 2, "freight_yards": 0,
        "crew_change": False, "maintenance_depot": False, "water_column": False,
        "dwell_times": {"superfast": 1, "express": 2, "passenger": 3, "freight": 8, "mail_express": 2}
    },
    "Station_D": {
        "type": "terminal_station", "platforms": 3, "loops": 2, "freight_yards": 1,
        "crew_change": False, "maintenance_depot": False, "water_column": False,
        "dwell_times": {"superfast": 3, "express": 4, "passenger": 6, "freight": 12, "mail_express": 4}
    },
    "Junction_Y": {
        "type": "interchange", "platforms": 2, "loops": 2, "freight_yards": 1,
        "crew_change": False, "maintenance_depot": False, "water_column": False,
        "dwell_times": {"superfast": 2, "express": 3, "passenger": 4, "freight": 10, "mail_express": 2}
    }
}
