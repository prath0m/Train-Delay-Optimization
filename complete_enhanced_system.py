from ortools.sat.python import cp_model
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import json
from enum import Enum

class WeatherCondition(Enum):
    CLEAR = "clear"
    LIGHT_RAIN = "light_rain"
    HEAVY_RAIN = "heavy_rain"
    FOG = "fog"
    EXTREME_HEAT = "extreme_heat"

class TrainType(Enum):
    SUPERFAST = "superfast"
    EXPRESS = "express"
    MAIL_EXPRESS = "mail_express"
    PASSENGER = "passenger"
    FREIGHT = "freight"
    GOODS = "goods"

class EnhancedIndianRailwayOptimizer:
    
    def __init__(self, scenario_date: datetime = None, custom_delay_factor: float = 1.0):
        self.model = cp_model.CpModel()
        self.scenario_date = scenario_date or datetime.now()
        self.custom_delay_factor = max(0.0, min(custom_delay_factor, 2.0))  # Clamp between 0 and 2
        
        self.stations = [
            "Karjat_Hold_Point", "Station_C", "Station_A", "Station_J",
            "Lonavala_Hold_Point", "Junction_Z", "Station_B", "Junction_X", 
            "Station_G", "H_Loop", "Station_D", "Junction_Y"
        ]
        
        self.tracks = [
            {"from": "Station_C", "to": "Station_A", "length_km": 18, "tracks": 2, 
             "min_travel_time": 15, "gradient": "level", "electrified": True},
            {"from": "Station_A", "to": "Station_J", "length_km": 19, "tracks": 2,
             "min_travel_time": 16, "gradient": "level", "electrified": True},
            
            {"from": "Station_J", "to": "Lonavala_Hold_Point", "length_km": 25, "tracks": 1,
             "min_travel_time": 45, "gradient": "steep_climb", "electrified": True},
            {"from": "Lonavala_Hold_Point", "to": "Junction_Z", "length_km": 8, "tracks": 1,
             "min_travel_time": 12, "gradient": "steep_climb", "electrified": True},
            
            # Junction and branch sections
            {"from": "Junction_Z", "to": "Station_B", "length_km": 15, "tracks": 2,
             "min_travel_time": 12, "gradient": "level", "electrified": True},
            {"from": "Station_B", "to": "Junction_X", "length_km": 9, "tracks": 2,
             "min_travel_time": 8, "gradient": "level", "electrified": True},
            {"from": "Junction_X", "to": "Station_G", "length_km": 11, "tracks": 2,
             "min_travel_time": 9, "gradient": "level", "electrified": True},
            
            # Loop and branch lines
            {"from": "Station_G", "to": "H_Loop", "length_km": 7, "tracks": 1,
             "min_travel_time": 10, "gradient": "level", "electrified": True},
            {"from": "H_Loop", "to": "Station_D", "length_km": 14, "tracks": 2,
             "min_travel_time": 11, "gradient": "level", "electrified": True},
            
            # Freight connection
            {"from": "Karjat_Hold_Point", "to": "Station_C", "length_km": 12, "tracks": 2,
             "min_travel_time": 20, "gradient": "level", "electrified": True},
        ]
        
        self.trains = [
            # Premium trains (highest priority)
            {"id": "12301_Howrah_Rajdhani", "type": TrainType.SUPERFAST, "priority": 5.0,
             "route": ["Station_C", "Station_A", "Station_J", "Lonavala_Hold_Point", "Junction_Z", "Station_B"],
             "scheduled_departure": 300, "passenger_load": 1.0, "coaches": 18},
             
            {"id": "22301_Shatabdi_Express", "type": TrainType.SUPERFAST, "priority": 4.5,
             "route": ["Station_C", "Station_A", "Station_J", "Lonavala_Hold_Point", "Junction_Z"],
             "scheduled_departure": 360, "passenger_load": 0.9, "coaches": 16},
            
            # Express trains
            {"id": "11301_Udyan_Express", "type": TrainType.EXPRESS, "priority": 4.0,
             "route": ["Station_C", "Station_A", "Station_J", "Lonavala_Hold_Point", "Junction_Z", "Station_B", "Junction_X"],
             "scheduled_departure": 420, "passenger_load": 1.1, "coaches": 22},
             
            {"id": "17301_Mumbai_Mail", "type": TrainType.MAIL_EXPRESS, "priority": 3.5,
             "route": ["Station_B", "Junction_Z", "Lonavala_Hold_Point", "Station_J", "Station_A", "Station_C"],
             "scheduled_departure": 480, "passenger_load": 1.2, "coaches": 20},
            
            # Passenger trains
            {"id": "51301_Local_Passenger", "type": TrainType.PASSENGER, "priority": 2.0,
             "route": ["Station_C", "Station_A", "Station_J", "Lonavala_Hold_Point"],
             "scheduled_departure": 390, "passenger_load": 1.4, "coaches": 12},
             
            {"id": "59301_Mixed_Passenger", "type": TrainType.PASSENGER, "priority": 1.8,
             "route": ["Junction_Z", "Station_B", "Junction_X", "Station_G"],
             "scheduled_departure": 450, "passenger_load": 1.3, "coaches": 10},
            
            # Freight trains
            {"id": "56301_Container_Freight", "type": TrainType.FREIGHT, "priority": 1.5,
             "route": ["Karjat_Hold_Point", "Station_C", "Station_A", "Station_J"],
             "scheduled_departure": 240, "freight_wagons": 45, "commodity": "containers"},
             
            {"id": "52301_Coal_Goods", "type": TrainType.GOODS, "priority": 1.0,
             "route": ["Karjat_Hold_Point", "Station_C", "Station_A"],
             "scheduled_departure": 180, "freight_wagons": 58, "commodity": "coal"}
        ]
        
        # Station characteristics and facilities
        self.station_config = {
            "Station_C": {
                "type": "major_junction", "platforms": 6, "loops": 4, "freight_yards": 2,
                "crew_change": True, "maintenance_depot": True, "water_column": True,
                "dwell_times": {"superfast": 3, "express": 4, "passenger": 6, "freight": 15}
            },
            "Station_A": {
                "type": "intermediate_major", "platforms": 4, "loops": 3, "freight_yards": 1,
                "crew_change": False, "maintenance_depot": False, "water_column": True,
                "dwell_times": {"superfast": 2, "express": 3, "passenger": 4, "freight": 10}
            },
            "Station_J": {
                "type": "grade_change_point", "platforms": 3, "loops": 2, "freight_yards": 1,
                "crew_change": True, "maintenance_depot": False, "water_column": True,
                "dwell_times": {"superfast": 5, "express": 6, "passenger": 8, "freight": 20},
                "notes": "Last station before steep climb"
            },
            "Lonavala_Hold_Point": {
                "type": "crossing_station", "platforms": 2, "loops": 6, "freight_yards": 0,
                "crew_change": True, "maintenance_depot": False, "water_column": True,
                "dwell_times": {"superfast": 3, "express": 4, "passenger": 6, "freight": 25},
                "crossing_capacity": 4, "notes": "Critical crossing point"
            },
            "Junction_Z": {
                "type": "major_junction", "platforms": 8, "loops": 5, "freight_yards": 3,
                "crew_change": True, "maintenance_depot": True, "water_column": True,
                "dwell_times": {"superfast": 4, "express": 5, "passenger": 7, "freight": 18}
            }
        }
        
        self.weather_scenarios = self._get_weather_scenario()
        self.maintenance_blocks = self._get_maintenance_blocks()
        self.operational_constraints = self._get_operational_constraints()
        
        # Model variables
        self.time_vars = {}
        self.delay_vars = {}
        self.assignment_vars = {}
        self.intervals = {}
        
    def _get_weather_scenario(self) -> Dict:

        month = self.scenario_date.month
        
        if month in [6, 7, 8, 9]:  # Monsoon season
            return {
                "season": "monsoon",
                "conditions": {
                    "Station_J_to_Lonavala_Hold_Point": {
                        "condition": WeatherCondition.HEAVY_RAIN,
                        "speed_reduction": 0.4 * self.custom_delay_factor,
                        "additional_time": int(20 * self.custom_delay_factor),
                        "visibility": "poor"
                    },
                    "Lonavala_Hold_Point_to_Junction_Z": {
                        "condition": WeatherCondition.HEAVY_RAIN,
                        "speed_reduction": 0.3 * self.custom_delay_factor,
                        "additional_time": int(8 * self.custom_delay_factor),
                        "visibility": "poor"
                    }
                }
            }
        elif month in [12, 1, 2]:  # Winter fog season
            return {
                "season": "winter",
                "conditions": {
                    "Station_A_to_Station_J": {
                        "condition": WeatherCondition.FOG,
                        "speed_reduction": 0.5 * self.custom_delay_factor,
                        "additional_time": int(15 * self.custom_delay_factor),
                        "visibility": "very_poor"
                    },
                    "Junction_Z_to_Station_B": {
                        "condition": WeatherCondition.FOG,
                        "speed_reduction": 0.4 * self.custom_delay_factor,
                        "additional_time": int(10 * self.custom_delay_factor),
                        "visibility": "poor"
                    }
                }
            }
        elif month in [4, 5]:  # Summer heat
            return {
                "season": "summer",
                "conditions": {
                    "Station_J_to_Lonavala_Hold_Point": {
                        "condition": WeatherCondition.EXTREME_HEAT,
                        "speed_reduction": 0.2 * self.custom_delay_factor,
                        "additional_time": int(10 * self.custom_delay_factor),
                        "visibility": "good"
                    }
                }
            }
        else:
            return {"season": "normal", "conditions": {}}
    
    def _get_maintenance_blocks(self) -> List[Dict]:

        return [
            {
                "section": "Station_A_to_Station_J",
                "type": "track_renewal",
                "start_time": 120,  # 2:00 AM
                "end_time": 360,    # 6:00 AM
                "speed_limit": 0.3 * self.custom_delay_factor,
                "single_line_working": True
            },
            {
                "section": "Junction_X_to_Station_G", 
                "type": "signaling_maintenance",
                "start_time": 60,   # 1:00 AM
                "end_time": 300,    # 5:00 AM
                "speed_limit": 0.5 * self.custom_delay_factor,
                "single_line_working": False
            }
        ]
    
    def _get_operational_constraints(self) -> Dict:

        return {
            "priority_rules": {
                "superfast": {"can_overtake": ["express", "passenger", "freight", "goods"]},
                "express": {"can_overtake": ["passenger", "freight", "goods"]},
                "passenger": {"can_overtake": ["freight", "goods"]},
                "freight": {"can_overtake": ["goods"]},
                "goods": {"can_overtake": []}
            },
            "crossing_rules": {
                "minimum_separation": 5,  # 5 minutes between trains
                "single_track_precedence": "priority_based"
            },
            "freight_restrictions": {
                "peak_hours": ["07:00-10:00", "17:00-20:00"],
                "restricted_sections": ["Station_C_to_Station_A", "Junction_Z_to_Station_B"]
            },
            "crew_constraints": {
                "maximum_duty_hours": 8 * 60,  # 8 hours in minutes
                "minimum_rest_time": 30,       # 30 minutes for crew change
                "crew_change_stations": ["Station_C", "Station_J", "Junction_Z"]
            }
        }
    
    def initialize_model_variables(self):

        horizon = 36 * 60  # 36 hours in minutes (extended for higher delays)
        
        for train in self.trains:
            train_id = train["id"]
            
            # Time variables
            self.time_vars[train_id] = {}
            self.time_vars[train_id]["arrival"] = {}
            self.time_vars[train_id]["departure"] = {}
            self.time_vars[train_id]["dwell"] = {}
            
            # Delay variables with detailed breakdown
            self.delay_vars[train_id] = {}
            self.delay_vars[train_id]["weather"] = {}
            self.delay_vars[train_id]["maintenance"] = {}
            self.delay_vars[train_id]["congestion"] = {}
            self.delay_vars[train_id]["operational"] = {}
            
            # Assignment variables
            self.assignment_vars[train_id] = {}
            
            for station in train["route"]:
                # Time variables
                self.time_vars[train_id]["arrival"][station] = self.model.NewIntVar(
                    0, horizon, f"arr_{train_id}_{station}")
                self.time_vars[train_id]["departure"][station] = self.model.NewIntVar(
                    0, horizon, f"dep_{train_id}_{station}")
                self.time_vars[train_id]["dwell"][station] = self.model.NewIntVar(
                    0, 60, f"dwell_{train_id}_{station}")
                
                # Delay components
                for delay_type in ["weather", "maintenance", "congestion", "operational"]:
                    self.delay_vars[train_id][delay_type][station] = self.model.NewIntVar(
                        0, 180, f"{delay_type}_delay_{train_id}_{station}")
                
                # Platform assignment (where applicable)
                if station in self.station_config:
                    max_platforms = (self.station_config[station]["platforms"] + 
                                   self.station_config[station]["loops"])
                    self.assignment_vars[train_id][station] = self.model.NewIntVar(
                        1, max_platforms, f"platform_{train_id}_{station}")
    
    def add_basic_operational_constraints(self):

        for train in self.trains:
            train_id = train["id"]
            route = train["route"]
            
            scheduled_dep = train.get("scheduled_departure", 480)  # Default 8:00 AM
            first_station = route[0]
            
            initial_delay = self.model.NewIntVar(0, 120, f"initial_delay_{train_id}")
            self.model.Add(
                self.time_vars[train_id]["departure"][first_station] == 
                scheduled_dep + initial_delay
            )
            
            for i in range(len(route) - 1):
                from_station = route[i]
                to_station = route[i + 1]
                
                track = self.find_track(from_station, to_station)
                if track is None:
                    continue
                
                base_time = track["min_travel_time"]
                
                section_key = f"{from_station}_to_{to_station}"
                weather_conditions = self.weather_scenarios.get("conditions", {})
                
                # Calculate MINIMUM travel time INCLUDING weather delays
                min_travel_time = base_time
                weather_additional = 0
                
                if section_key in weather_conditions:
                    weather_additional = int(weather_conditions[section_key]["additional_time"] * self.custom_delay_factor)
                    # Priority trains get 50% reduction in weather impact
                    if train["type"] in [TrainType.SUPERFAST, TrainType.EXPRESS]:
                        weather_additional = int(weather_additional * 0.5)
                    # ENFORCE weather delays by adding to minimum time
                    min_travel_time = base_time + weather_additional
                
                # Allow some flexibility for operational variations
                if train["type"] in [TrainType.FREIGHT, TrainType.GOODS]:
                    flexibility_multiplier = 1.3  # Minimal flex for freight (was 2.0)
                else:
                    flexibility_multiplier = 1.1  # Minimal flex for passenger trains (was 1.5)
                
                max_travel_time = int(min_travel_time * flexibility_multiplier) + 10  # Only 10 min buffer (was 60)
                
                # Travel time variable with weather-adjusted minimum
                actual_travel_time = self.model.NewIntVar(
                    min_travel_time, max_travel_time, 
                    f"travel_{train_id}_{from_station}_{to_station}")
                
                # CRITICAL: Enforce minimum travel time includes weather delays
                self.model.Add(actual_travel_time >= min_travel_time)
                
                self.model.Add(
                    self.time_vars[train_id]["arrival"][to_station] ==
                    self.time_vars[train_id]["departure"][from_station] + actual_travel_time
                )
                
                if i > 0:  # Not the first station
                    min_dwell = self._get_minimum_dwell_time(train, from_station)
                    self.model.Add(self.time_vars[train_id]["dwell"][from_station] >= min_dwell)
                    
                    self.model.Add(
                        self.time_vars[train_id]["departure"][from_station] ==
                        self.time_vars[train_id]["arrival"][from_station] + 
                        self.time_vars[train_id]["dwell"][from_station]
                    )
    
    def _get_minimum_dwell_time(self, train, station: str) -> int:
        
        if station not in self.station_config:
            return 1  # Minimum 1 minute
        
        station_info = self.station_config[station]
        train_type_key = train["type"].value
        
        base_dwell = station_info["dwell_times"].get(train_type_key, 3)
        
        if station_info.get("crew_change", False):
            base_dwell += 5
        
        if train.get("coaches", 12) > 16 and station_info.get("water_column", False):
            base_dwell += 3
        
        return base_dwell
    
    def add_weather_impact_constraints(self):
        
        conditions = self.weather_scenarios.get("conditions", {})
        
        for train in self.trains:
            train_id = train["id"]
            route = train["route"]
            
            for i in range(len(route) - 1):
                from_station = route[i]
                to_station = route[i + 1]
                section_key = f"{from_station}_to_{to_station}"
                
                if section_key in conditions:
                    weather_delay = int(conditions[section_key]["additional_time"] * self.custom_delay_factor)
                    
                    if train["type"] in [TrainType.SUPERFAST, TrainType.EXPRESS]:
                        weather_delay = int(weather_delay * 0.5)
                    
                    self.model.Add(
                        self.delay_vars[train_id]["weather"][to_station] == weather_delay
                    )
                else:
                    self.model.Add(
                        self.delay_vars[train_id]["weather"][to_station] == 0
                    )
            
            if route:
                self.model.Add(
                    self.delay_vars[train_id]["weather"][route[0]] == 0
                )
    
    def add_maintenance_constraints(self):

        for train in self.trains:
            train_id = train["id"]
            for station in train["route"]:
                self.model.Add(
                    self.delay_vars[train_id]["maintenance"][station] == 0
                )
    
    def add_single_track_constraints(self):

        single_tracks = [track for track in self.tracks if track["tracks"] == 1]
        
        for track in single_tracks:
            from_station = track["from"]
            to_station = track["to"]
            
            intervals = []
            
            for train in self.trains:
                train_id = train["id"]
                route = train["route"]
                
                if from_station in route and to_station in route:
                    from_idx = route.index(from_station)
                    to_idx = route.index(to_station)
                    
                    if abs(to_idx - from_idx) == 1: 
                       
                        buffer_time = 5
                        
                        if from_idx < to_idx:  # Forward direction
                            start_time = self.time_vars[train_id]["departure"][from_station]
                            end_time = self.time_vars[train_id]["arrival"][to_station]
                            
                            buffered_end = self.model.NewIntVar(
                                0, 36 * 60, f"buffered_end_{train_id}_{from_station}_{to_station}"
                            )
                            self.model.Add(buffered_end == end_time + buffer_time)
                            
                            duration = self.model.NewIntVar(
                                track["min_travel_time"], track["min_travel_time"] * 5,
                                f"duration_{train_id}_{from_station}_{to_station}"
                            )
                            self.model.Add(duration == end_time - start_time + buffer_time)
                            
                            interval = self.model.NewIntervalVar(
                                start_time,
                                duration,
                                buffered_end,
                                f"single_track_{train_id}_{from_station}_{to_station}"
                            )
                        else:  # Reverse direction
                            start_time = self.time_vars[train_id]["departure"][to_station]
                            end_time = self.time_vars[train_id]["arrival"][from_station]
                            
                            buffered_end = self.model.NewIntVar(
                                0, 36 * 60, f"buffered_end_{train_id}_{to_station}_{from_station}"
                            )
                            self.model.Add(buffered_end == end_time + buffer_time)
                            
                            duration = self.model.NewIntVar(
                                track["min_travel_time"], track["min_travel_time"] * 5,
                                f"duration_{train_id}_{to_station}_{from_station}"
                            )
                            self.model.Add(duration == end_time - start_time + buffer_time)
                            
                            interval = self.model.NewIntervalVar(
                                start_time,
                                duration,
                                buffered_end,
                                f"single_track_{train_id}_{to_station}_{from_station}"
                            )
                        
                        intervals.append((interval, train))
            
            # No overlap constraint with priority ordering
            if intervals:
                # Add no-overlap for the interval variables
                interval_vars = [interval for interval, _ in intervals]
                self.model.AddNoOverlap(interval_vars)
                
                # Add priority-based ordering constraints
                # Higher priority trains should not wait for lower priority trains
                trains_on_track = [train for _, train in intervals]
                for i, train1 in enumerate(trains_on_track):
                    for j, train2 in enumerate(trains_on_track):
                        if i >= j:
                            continue
                        
                        # If train1 has higher priority than train2
                        if train1["priority"] > train2["priority"]:
                            # Get the relevant stations for both trains
                            train1_route = train1["route"]
                            train2_route = train2["route"]
                            
                            # Check if trains are moving in the same direction on this section
                            train1_from_idx = train1_route.index(from_station) if from_station in train1_route else -1
                            train1_to_idx = train1_route.index(to_station) if to_station in train1_route else -1
                            train2_from_idx = train2_route.index(from_station) if from_station in train2_route else -1
                            train2_to_idx = train2_route.index(to_station) if to_station in train2_route else -1
                            
                            # Both trains use this section in forward direction
                            if (train1_from_idx >= 0 and train1_to_idx == train1_from_idx + 1 and
                                train2_from_idx >= 0 and train2_to_idx == train2_from_idx + 1):
                                
                                # Higher priority train should depart first or much later
                                # Create a choice: either train1 goes first, or train2 goes WAY ahead
                                priority_order = self.model.NewBoolVar(
                                    f"priority_order_{train1['id']}_{train2['id']}_{from_station}_{to_station}"
                                )
                                
                                min_separation = 10  # Minimum separation in minutes
                                large_gap = 120  # If lower priority goes first, high priority waits long
                                
                                # If priority_order is true: train1 departs before train2 with min separation
                                self.model.Add(
                                    self.time_vars[train1["id"]]["departure"][from_station] + min_separation <=
                                    self.time_vars[train2["id"]]["departure"][from_station]
                                ).OnlyEnforceIf(priority_order)
                                
                                # If priority_order is false: train2 must finish WAY before train1 starts
                                # This discourages the solver from making high-priority trains wait
                                self.model.Add(
                                    self.time_vars[train2["id"]]["arrival"][to_station] + large_gap <=
                                    self.time_vars[train1["id"]]["departure"][from_station]
                                ).OnlyEnforceIf(priority_order.Not())
    
    def add_priority_constraints(self):

        priority_rules = self.operational_constraints["priority_rules"]
        
        for station in self.stations:
            if station not in self.station_config:
                continue
            
            station_trains = [t for t in self.trains if station in t["route"]]
            
            if len(station_trains) < 2:
                continue
            
            # Sort trains by priority (highest first)
            station_trains_sorted = sorted(station_trains, key=lambda t: t["priority"], reverse=True)
            
            for i, train1 in enumerate(station_trains_sorted):
                for train2 in station_trains_sorted[i+1:]:
                    # train1 has higher priority than train2
                    priority_diff = train1["priority"] - train2["priority"]
                    
                    # If priority difference is significant (>= 0.5), enforce strict ordering
                    if priority_diff >= 0.5:
                        # Create a boolean: does train1 depart before train2?
                        train1_first = self.model.NewBoolVar(
                            f"priority_order_{train1['id']}_before_{train2['id']}_{station}"
                        )
                        
                        min_sep = self.operational_constraints["crossing_rules"]["minimum_separation"]
                        large_gap = 90  # If lower-priority train goes first, high-priority waits 90 min
                        
                        # If train1 goes first (preferred): train1 departs at least min_sep before train2
                        self.model.Add(
                            self.time_vars[train1["id"]]["departure"][station] + min_sep <=
                            self.time_vars[train2["id"]]["departure"][station]
                        ).OnlyEnforceIf(train1_first)
                        
                        # If train2 goes first (discouraged): train2 must finish and leave WAY before train1
                        self.model.Add(
                            self.time_vars[train2["id"]]["departure"][station] + large_gap <=
                            self.time_vars[train1["id"]]["arrival"][station]
                        ).OnlyEnforceIf(train1_first.Not())
            
            # Original overtaking rules (still useful for same-priority trains)
            for i, train1 in enumerate(station_trains):
                for train2 in station_trains[i+1:]:
                    type1 = train1["type"].value
                    type2 = train2["type"].value
                    
                    if type2 in priority_rules.get(type1, {}).get("can_overtake", []):
                        overtake = self.model.NewBoolVar(f"overtake_{train1['id']}_{train2['id']}_{station}")
                        
                        min_sep = self.operational_constraints["crossing_rules"]["minimum_separation"]
                        
                        self.model.Add(
                            self.time_vars[train1["id"]]["departure"][station] + min_sep <=
                            self.time_vars[train2["id"]]["departure"][station]
                        ).OnlyEnforceIf(overtake)
    
    def add_no_waiting_for_lower_priority_constraints(self):
        """Prevent higher-priority trains from being delayed by lower-priority trains"""
        
        for station in self.stations:
            if station not in self.station_config:
                continue
            
            station_trains = [t for t in self.trains if station in t["route"]]
            
            # Sort by priority
            station_trains_sorted = sorted(station_trains, key=lambda t: t["priority"], reverse=True)
            
            for i, train_high in enumerate(station_trains_sorted):
                for train_low in station_trains_sorted[i+1:]:
                    # train_high has HIGHER priority than train_low
                    if train_high["priority"] <= train_low["priority"]:
                        continue
                    
                    # Get the route indices to check if they overlap
                    if station not in train_high["route"] or station not in train_low["route"]:
                        continue
                    
                    high_idx = train_high["route"].index(station)
                    low_idx = train_low["route"].index(station)
                    
                    # Only if both trains pass through the same station
                    if high_idx < 0 or low_idx < 0:
                        continue
                    
                    # High-priority train should depart before low-priority train
                    # OR depart much later (not wait for it)
                    choice_var = self.model.NewBoolVar(
                        f"high_departs_first_{train_high['id']}_{train_low['id']}_{station}"
                    )
                    
                    # Option 1: High-priority departs before low-priority (preferred)
                    self.model.Add(
                        self.time_vars[train_high["id"]]["departure"][station] <=
                        self.time_vars[train_low["id"]]["departure"][station]
                    ).OnlyEnforceIf(choice_var)
                    
                    # Option 2: High-priority departs MUCH later (not waiting)
                    # This effectively makes Option 1 preferred
                    large_separation = 120
                    self.model.Add(
                        self.time_vars[train_high["id"]]["departure"][station] >=
                        self.time_vars[train_low["id"]]["departure"][station] + large_separation
                    ).OnlyEnforceIf(choice_var.Not())
    
    def add_platform_capacity_constraints(self):

        for station, config in self.station_config.items():
            total_capacity = config["platforms"] + config["loops"]
            
            station_trains = [t for t in self.trains if station in t["route"]]
            
            if len(station_trains) <= total_capacity:
                continue  # No capacity issues
            
            intervals = []
            demands = []
            
            for train in station_trains:
                train_id = train["id"]
                
                interval = self.model.NewIntervalVar(
                    self.time_vars[train_id]["arrival"][station],
                    self.time_vars[train_id]["dwell"][station],
                    self.time_vars[train_id]["departure"][station],
                    f"platform_occupation_{train_id}_{station}"
                )
                
                intervals.append(interval)
                demands.append(1)  # Each train needs 1 platform/loop
            
            self.model.AddCumulative(intervals, demands, total_capacity)
    
    def add_freight_restrictions(self):

        restrictions = self.operational_constraints["freight_restrictions"]
        
        for train in self.trains:
            if train["type"] not in [TrainType.FREIGHT, TrainType.GOODS]:
                continue
                
            train_id = train["id"]
            
            for peak_period in restrictions["peak_hours"]:
                start_time, end_time = peak_period.split("-")
                start_minutes = self._time_to_minutes(start_time)
                end_minutes = self._time_to_minutes(end_time)
                
                for station in train["route"]:
                    restriction_violation = self.model.NewBoolVar(
                        f"freight_restriction_{train_id}_{station}_{peak_period}"
                    )
                    
                    dep_time = self.time_vars[train_id]["departure"][station]
                    
                    self.model.Add(dep_time >= start_minutes).OnlyEnforceIf(restriction_violation)
                    self.model.Add(dep_time <= end_minutes).OnlyEnforceIf(restriction_violation)
                    
                    self.model.Add(
                        self.delay_vars[train_id]["operational"][station] >= 45
                    ).OnlyEnforceIf(restriction_violation)
    
    def _time_to_minutes(self, time_str: str) -> int:

        hours, minutes = map(int, time_str.split(":"))
        return hours * 60 + minutes
    
    def set_optimization_objective(self):

        delay_penalty = 0
        punctuality_bonus = 0
        operational_efficiency = 0
        dwell_penalty = 0  # NEW: Penalty for excessive dwell times
        
        for train in self.trains:
            train_id = train["id"]
            priority = train["priority"]
            
            for station in train["route"]:
                total_delay = sum([
                    self.delay_vars[train_id][delay_type][station]
                    for delay_type in ["weather", "maintenance", "congestion", "operational"]
                ])
                
                if train["type"] == TrainType.SUPERFAST:
                    weight = 100  # MUCH higher penalty for Rajdhani/Shatabdi delays
                elif train["type"] == TrainType.EXPRESS:
                    weight = 50  # High penalty for Express delays
                elif train["type"] == TrainType.PASSENGER:
                    weight = 20  # Medium penalty for Passenger delays
                else:
                    weight = 5  # Lower penalty for Freight delays
                
                # Use exponential scaling based on priority to heavily favor high-priority trains
                delay_penalty += total_delay * int(priority * priority * weight * 100)
                
                # NEW: Penalize excessive dwell times (extra waits)
                min_dwell = self._get_minimum_dwell_time(train, station)
                actual_dwell = self.time_vars[train_id]["dwell"][station]
                extra_dwell = self.model.NewIntVar(0, 480, f"extra_dwell_{train_id}_{station}")
                self.model.Add(extra_dwell >= actual_dwell - min_dwell)
                # Higher priority trains get exponential penalty for waiting
                dwell_penalty += extra_dwell * int(priority * priority * 50)
        
        for train in self.trains:
            train_id = train["id"]
            
            final_station = train["route"][-1]
            scheduled_arrival = train.get("scheduled_departure", 480) + 120  # Assume 2-hour journey
            actual_arrival = self.time_vars[train_id]["arrival"][final_station]
            
            on_time = self.model.NewBoolVar(f"on_time_{train_id}")
            
            self.model.Add(actual_arrival <= scheduled_arrival + 5).OnlyEnforceIf(on_time)
            self.model.Add(actual_arrival > scheduled_arrival + 5).OnlyEnforceIf(on_time.Not())
            
            punctuality_bonus += on_time * int(train["priority"] * 1000)
        
        for station in self.station_config:
            station_trains = [t for t in self.trains if station in t["route"]]
            
            for i in range(len(station_trains) - 1):
                train1_id = station_trains[i]["id"]
                train2_id = station_trains[i + 1]["id"]
                
                gap = self.model.NewIntVar(0, 480, f"platform_gap_{train1_id}_{train2_id}_{station}")
                
                self.model.Add(
                    gap >= self.time_vars[train2_id]["arrival"][station] -
                    self.time_vars[train1_id]["departure"][station]
                )
                
                operational_efficiency += gap * 5  # Small penalty for large gaps
        
        # Combine objectives
        total_objective = (
            delay_penalty +           # Minimize delays (positive)
            dwell_penalty +           # Minimize excessive dwell/waiting (positive)
            operational_efficiency -  # Minimize inefficiency (positive)  
            punctuality_bonus        # Maximize punctuality (subtract to maximize)
        )
        
        self.model.Minimize(total_objective)
    
    def solve_optimization(self) -> Dict:

        print("\n" + "=" * 60)
        print("Enhanced Indian Railway Delay Optimization")
        print(f"Scenario Date: {self.scenario_date.strftime('%B %d, %Y')}")
        print(f"Weather Season: {self.weather_scenarios['season'].title()}")
        print(f"Maintenance Blocks: {len(self.maintenance_blocks)}")
        print("=" * 60)
        
        print("\nBuilding comprehensive optimization model...")
        
        # Build model step by step
        self.initialize_model_variables()
        print("   [OK] Variables initialized")
        
        self.add_basic_operational_constraints()
        print("   [OK] Basic operational constraints")
        
        self.add_weather_impact_constraints()
        print("   [OK] Weather impact constraints")
        
        self.add_maintenance_constraints()
        print("   [OK] Maintenance constraints")
        
        self.add_single_track_constraints()
        print("   [OK] Single track constraints")
        
        self.add_priority_constraints()
        print("   [OK] Priority and overtaking rules")
        
        self.add_no_waiting_for_lower_priority_constraints()
        print("   [OK] No waiting for lower priority constraints")
        
        self.add_platform_capacity_constraints()
        print("   [OK] Platform capacity constraints")
        
        self.add_freight_restrictions()
        print("   [OK] Freight movement restrictions")
        
        self.set_optimization_objective()
        print("   [OK] Multi-objective function set")
        
        print("\nSolving optimization problem...")
        
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = 600.0  # 10 minutes for complex scenarios
        solver.parameters.num_search_workers = 8
        solver.parameters.log_search_progress = False  # Reduce console spam
        solver.parameters.linearization_level = 2  # More aggressive linearization
        
        status = solver.Solve(self.model)
        
        return self._extract_solution(solver, status)
    
    def _extract_solution(self, solver, status) -> Dict:

        solution = {
            "status": solver.StatusName(status),
            "solve_time": solver.WallTime(),
            "objective_value": solver.ObjectiveValue() if status in [cp_model.OPTIMAL, cp_model.FEASIBLE] else None,
            "train_schedules": {},
            "performance_metrics": {},
            "operational_insights": {},
            "recommendations": []
        }
        
        if status not in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
            error_msg = "No feasible solution found"
            error_msg += f"\n\nThe optimization could not find a valid schedule with delay factor {self.custom_delay_factor}.\n"
            error_msg += "   Possible reasons:\n"
            error_msg += "   - Network capacity constraints (single-track bottlenecks)\n"
            error_msg += "   - Too many trains scheduled in overlapping time windows\n"
            error_msg += "   - Try adjusting train schedules or adding more crossing loops\n"
            error_msg += f"\n   Solver status: {solver.StatusName(status)}"
            solution["error"] = error_msg
            return solution

        total_system_delay = 0
        on_time_trains = 0
        
        for train in self.trains:
            train_id = train["id"]
            train_schedule = {}
            train_delays = {}
            
            total_train_delay = 0
            
            for station in train["route"]:
                arrival = solver.Value(self.time_vars[train_id]["arrival"][station])
                departure = solver.Value(self.time_vars[train_id]["departure"][station])
                dwell = solver.Value(self.time_vars[train_id]["dwell"][station])
                
                train_schedule[station] = {
                    "arrival": self._format_time(arrival),
                    "departure": self._format_time(departure),
                    "dwell_minutes": dwell
                }
                
                # Extract delay breakdown
                delays = {}
                station_total_delay = 0
                for delay_type in ["weather", "maintenance", "congestion", "operational"]:
                    delay_value = solver.Value(self.delay_vars[train_id][delay_type][station])
                    delays[delay_type] = delay_value
                    station_total_delay += delay_value
                
                train_delays[station] = delays
                total_train_delay += station_total_delay
            
            solution["train_schedules"][train_id] = {
                "schedule": train_schedule,
                "delays": train_delays,
                "total_delay": total_train_delay,
                "type": train["type"].value,
                "priority": train["priority"]
            }
            
            total_system_delay += total_train_delay
            
            final_delays = list(train_delays[train["route"][-1]].values())
            if sum(final_delays) <= 5:
                on_time_trains += 1
        
        solution["performance_metrics"] = {
            "total_system_delay_minutes": total_system_delay,
            "average_delay_per_train": total_system_delay / len(self.trains),
            "punctuality_percentage": (on_time_trains / len(self.trains)) * 100,
            "on_time_trains": on_time_trains,
            "total_trains": len(self.trains)
        }
        
        solution["train_interactions"] = self._analyze_train_interactions(solution, solver)
        
        solution["operational_insights"] = self._analyze_performance(solution)
        solution["recommendations"] = self._generate_recommendations(solution)
        
        return solution
    
    def _format_time(self, minutes: int) -> str:

        hours = minutes // 60
        mins = minutes % 60
        return f"{hours:02d}:{mins:02d}"
    
    def _analyze_train_interactions(self, solution, solver) -> Dict:

        interactions = {
            "overtaking_events": [],
            "waiting_events": [],
            "single_track_conflicts": []
        }
        
        trains_by_priority = sorted(self.trains, key=lambda t: t["priority"], reverse=True)
        
        for station in self.station_config.keys():
            trains_at_station = []
            
            for train in self.trains:
                if station in train["route"]:
                    train_id = train["id"]
                    arrival = solver.Value(self.time_vars[train_id]["arrival"][station])
                    departure = solver.Value(self.time_vars[train_id]["departure"][station])
                    dwell = departure - arrival
                    
                    trains_at_station.append({
                        "id": train_id,
                        "name": train_id.split("_")[0],
                        "type": train["type"].value,
                        "priority": train["priority"],
                        "arrival": arrival,
                        "departure": departure,
                        "dwell": dwell
                    })
            
            # Sort by arrival time
            trains_at_station.sort(key=lambda t: t["arrival"])
            
            for i in range(len(trains_at_station)):
                for j in range(i + 1, len(trains_at_station)):
                    train_i = trains_at_station[i]
                    train_j = trains_at_station[j]
                    
                    if (train_i["arrival"] < train_j["arrival"] and 
                        train_i["departure"] > train_j["departure"] and
                        train_j["priority"] > train_i["priority"]):
                        
                        interactions["overtaking_events"].append({
                            "station": station,
                            "stopped_train": train_i["id"],
                            "stopped_train_type": train_i["type"],
                            "stopped_train_priority": train_i["priority"],
                            "overtaking_train": train_j["id"],
                            "overtaking_train_type": train_j["type"],
                            "overtaking_train_priority": train_j["priority"],
                            "wait_time_minutes": train_i["dwell"],
                            "time": self._format_time(train_i["arrival"])
                        })
                    
                    min_dwell = self._get_minimum_dwell_time(self.trains[i], station)
                    if train_i["dwell"] > min_dwell + 15:  # More than 15 min extra
                        interactions["waiting_events"].append({
                            "station": station,
                            "waiting_train": train_i["id"],
                            "waiting_train_type": train_i["type"],
                            "possibly_waiting_for": train_j["id"],
                            "extra_wait_minutes": train_i["dwell"] - min_dwell,
                            "time": self._format_time(train_i["arrival"])
                        })
        
        single_tracks = [track for track in self.tracks if track["tracks"] == 1]
        for track in single_tracks:
            section = f"{track['from']}_to_{track['to']}"
            trains_on_section = []
            
            for train in self.trains:
                if track["from"] in train["route"] and track["to"] in train["route"]:
                    from_idx = train["route"].index(track["from"])
                    to_idx = train["route"].index(track["to"])
                    
                    if abs(to_idx - from_idx) == 1:
                        train_id = train["id"]
                        dep_time = solver.Value(self.time_vars[train_id]["departure"][track["from"]])
                        arr_time = solver.Value(self.time_vars[train_id]["arrival"][track["to"]])
                        
                        trains_on_section.append({
                            "id": train_id,
                            "priority": train["priority"],
                            "departure": dep_time,
                            "arrival": arr_time
                        })
            
            trains_on_section.sort(key=lambda t: t["departure"])
            
            for i in range(len(trains_on_section) - 1):
                train_current = trains_on_section[i]
                train_next = trains_on_section[i + 1]
                
                if train_next["departure"] >= train_current["arrival"]:
                    if train_next["priority"] < train_current["priority"]:
                        interactions["single_track_conflicts"].append({
                            "section": section,
                            "waited_train": train_next["id"],
                            "priority_train": train_current["id"],
                            "wait_started": self._format_time(train_current["departure"]),
                            "wait_ended": self._format_time(train_next["departure"])
                        })
        
        return interactions
    
    def _analyze_performance(self, solution) -> Dict:

        insights = {}
        
        weather_delays = sum(
            sum(train_data["delays"][station].get("weather", 0) 
                for station in train_data["delays"])
            for train_data in solution["train_schedules"].values()
        )
        insights["weather_impact"] = "High" if weather_delays > 100 else "Moderate" if weather_delays > 50 else "Low"
        
        maintenance_delays = sum(
            sum(train_data["delays"][station].get("maintenance", 0)
                for station in train_data["delays"])
            for train_data in solution["train_schedules"].values()
        )
        insights["maintenance_impact"] = "High" if maintenance_delays > 80 else "Moderate" if maintenance_delays > 40 else "Low"
        
        single_track_sections = [t for t in self.tracks if t["tracks"] == 1]
        insights["single_track_bottlenecks"] = len(single_track_sections)
        
        superfast_delays = [
            train_data["total_delay"] 
            for train_data in solution["train_schedules"].values()
            if train_data["type"] == "superfast"
        ]
        insights["premium_train_performance"] = "Good" if all(d <= 10 for d in superfast_delays) else "Needs Improvement"
        
        return insights
    
    def _generate_recommendations(self, solution) -> List[str]:

        recommendations = []
        metrics = solution["performance_metrics"]
        insights = solution["operational_insights"]
        
        # Punctuality recommendations
        if metrics["punctuality_percentage"] < 80:
            recommendations.append("[PRIORITY] Punctuality below 80% target")
            recommendations.append("   - Review and optimize station dwell times")
            recommendations.append("   - Consider dynamic scheduling adjustments")
        
        # Weather impact recommendations
        if insights["weather_impact"] == "High":
            recommendations.append("[WEATHER] HIGH WEATHER IMPACT detected")
            recommendations.append("   - Implement weather-specific speed restrictions")
            recommendations.append("   - Enhance drainage systems on critical sections")
            recommendations.append("   - Consider weather forecasting integration")
        
        # Maintenance optimization
        if insights["maintenance_impact"] == "High":
            recommendations.append("[MAINTENANCE] MAINTENANCE IMPACT significant")
            recommendations.append("   - Reschedule maintenance during low-traffic periods")
            recommendations.append("   - Coordinate multiple maintenance activities")
            recommendations.append("   - Implement faster maintenance techniques")
        
        # Infrastructure recommendations
        if insights["single_track_bottlenecks"] > 0:
            recommendations.append(f"[BOTTLENECK] {insights['single_track_bottlenecks']} single track sections")
            recommendations.append("   - Priority: Double tracking of Lonavala-Junction_Z section")
            recommendations.append("   - Add additional crossing loops")
            recommendations.append("   - Implement automatic block signaling")
        
        # Premium service recommendations
        if insights["premium_train_performance"] == "Needs Improvement":
            recommendations.append("[PREMIUM] PREMIUM SERVICES need attention")
            recommendations.append("   - Guarantee priority paths for Rajdhani/Shatabdi trains")
            recommendations.append("   - Implement dynamic rescheduling for delays")
            recommendations.append("   - Review crew scheduling for premium trains")
        
        # General efficiency recommendations
        if metrics["average_delay_per_train"] > 15:
            recommendations.append("[DELAYS] HIGH AVERAGE DELAYS detected")
            recommendations.append("   - Implement real-time train tracking")
            recommendations.append("   - Optimize signal spacing and timing")
            recommendations.append("   - Review timetable buffer times")
        
        return recommendations
    
    def print_comprehensive_results(self, solution):

        print("\n" + "=" * 80)
        print("COMPREHENSIVE INDIAN RAILWAY OPTIMIZATION RESULTS")
        print("=" * 80)
        
        if solution.get("error"):
            print(f"ERROR: {solution['error']}")
            return
        
        # System overview
        print(f"\nSolution Status: {solution['status']}")
        print(f"Objective Value: {solution['objective_value']}")
        print(f"Solve Time: {solution['solve_time']:.2f} seconds")
        
        # Performance metrics
        metrics = solution["performance_metrics"]
        print(f"\nSYSTEM PERFORMANCE METRICS")
        print(f"   Total System Delay: {metrics['total_system_delay_minutes']} minutes")
        print(f"   Average Delay per Train: {metrics['average_delay_per_train']:.1f} minutes")
        print(f"   Punctuality Rate: {metrics['punctuality_percentage']:.1f}% ({metrics['on_time_trains']}/{metrics['total_trains']} trains)")
        
        # Weather and operational analysis
        insights = solution["operational_insights"]
        print(f"\nOPERATIONAL ANALYSIS")
        print(f"   Weather Impact: {insights['weather_impact']}")
        print(f"   Maintenance Impact: {insights['maintenance_impact']}")
        print(f"   Single Track Bottlenecks: {insights['single_track_bottlenecks']} sections")
        print(f"   Premium Train Performance: {insights['premium_train_performance']}")
        
        # Detailed train schedules
        print(f"\nOPTIMIZED TRAIN SCHEDULES")
        print("-" * 80)
        
        for train in self.trains:
            train_id = train["id"]
            train_data = solution["train_schedules"][train_id]
            
            print(f"\n{'=' * 80}")
            print(f"TRAIN: {train_id}")
            print(f"   Type: {train_data['type'].title()} | Priority: {train_data['priority']} | Total Delay: {train_data['total_delay']} min")
            print(f"{'=' * 80}")
            
            # Get all interactions for this train
            interactions = solution.get("train_interactions", {})
            overtaking_at_stations = {}
            waiting_at_stations = {}
            
            for event in interactions.get("overtaking_events", []):
                if event["stopped_train"] == train_id:
                    if event["station"] not in overtaking_at_stations:
                        overtaking_at_stations[event["station"]] = []
                    overtaking_at_stations[event["station"]].append(event)
                elif event["overtaking_train"] == train_id:
                    if event["station"] not in overtaking_at_stations:
                        overtaking_at_stations[event["station"]] = []
                    overtaking_at_stations[event["station"]].append(event)
            
            for event in interactions.get("waiting_events", []):
                if event["waiting_train"] == train_id:
                    if event["station"] not in waiting_at_stations:
                        waiting_at_stations[event["station"]] = []
                    waiting_at_stations[event["station"]].append(event)
            
            for idx, station in enumerate(train["route"]):
                schedule = train_data["schedule"][station]
                delays = train_data["delays"][station]
                
                total_station_delay = sum(delays.values())
                delay_indicator = "🔴" if total_station_delay > 15 else "🟡" if total_station_delay > 5 else "🟢"
                
                min_dwell = self._get_minimum_dwell_time(train, station) if station in self.station_config else 0
                actual_dwell = schedule['dwell_minutes']
                extra_wait = max(0, actual_dwell - min_dwell)
                
                print(f"\n   Station {idx + 1}/{len(train['route'])}: {station}")
                print(f"      Arrival:   {schedule['arrival']:>5s} | Departure: {schedule['departure']:>5s}")
                print(f"      Dwell:     {actual_dwell:>3d} min (Min: {min_dwell} min, Extra wait: {extra_wait} min)")
                
                if total_station_delay > 0:
                    delay_status = "[HIGH]" if total_station_delay > 15 else "[MED]" if total_station_delay > 5 else "[LOW]"
                    print(f"      Total Delay: {total_station_delay} min {delay_status}")
                    for delay_type, delay_value in delays.items():
                        if delay_value > 0:
                            print(f"         - {delay_type.title()}: {delay_value} min")
                
                if station in overtaking_at_stations:
                    for event in overtaking_at_stations[station]:
                        if event["stopped_train"] == train_id:
                            print(f"      [STOPPED FOR] {event['overtaking_train']} (Priority {event['overtaking_train_priority']}) - Waited {event['wait_time_minutes']} min")
                        elif event["overtaking_train"] == train_id:
                            print(f"      [OVERTOOK] {event['stopped_train']} (Priority {event['stopped_train_priority']})")
                
                if station in waiting_at_stations:
                    for event in waiting_at_stations[station]:
                        print(f"      Extended wait: {event['extra_wait_minutes']} min (possibly for {event['possibly_waiting_for']})")
                
                if idx < len(train["route"]) - 1:
                    next_station = train["route"][idx + 1]
                    next_arrival = train_data["schedule"][next_station]["arrival"]
                    
                    dep_time = int(schedule['departure'].split(':')[0]) * 60 + int(schedule['departure'].split(':')[1])
                    arr_time = int(next_arrival.split(':')[0]) * 60 + int(next_arrival.split(':')[1])
                    travel_time = arr_time - dep_time
                    
                    track = self.find_track(station, next_station)
                    base_time = track["min_travel_time"] if track else 0
                    extra_time = travel_time - base_time
                    
                    print(f"      -> {next_station}: {travel_time} min (Base: {base_time} min, Extra: {extra_time} min)")
        
        # Train Interactions
        interactions = solution.get("train_interactions", {})
        if any(interactions.values()):
            print(f"\nTRAIN INTERACTIONS & PRIORITY EVENTS")
            print("-" * 80)
            
            # Overtaking events
            overtaking_events = interactions.get("overtaking_events", [])
            if overtaking_events:
                print(f"\nOVERTAKING EVENTS ({len(overtaking_events)}):")
                for event in overtaking_events:
                    print(f"  Location: {event['station']} @ {event['time']}")
                    print(f"     Stopped: {event['stopped_train']} ({event['stopped_train_type']}, Priority: {event['stopped_train_priority']})")
                    print(f"     STOPPED FOR:")
                    print(f"     Overtook: {event['overtaking_train']} ({event['overtaking_train_type']}, Priority: {event['overtaking_train_priority']})")
                    print(f"     Wait time: {event['wait_time_minutes']} minutes")
                    print()
            
            # Waiting events
            waiting_events = interactions.get("waiting_events", [])
            if waiting_events:
                print(f"\nEXTENDED WAITING EVENTS ({len(waiting_events)}):")
                for event in waiting_events[:5]:  # Show top 5
                    print(f"  Location: {event['station']} @ {event['time']}")
                    print(f"     Train: {event['waiting_train']} ({event['waiting_train_type']})")
                    print(f"     Extra wait: {event['extra_wait_minutes']} minutes")
                    print(f"     Possibly waiting for: {event['possibly_waiting_for']}")
                    print()
            
            # Single track conflicts
            single_track_conflicts = interactions.get("single_track_conflicts", [])
            if single_track_conflicts:
                print(f"\nSINGLE TRACK SEQUENCING ({len(single_track_conflicts)}):")
                for event in single_track_conflicts:
                    print(f"  Section: {event['section']}")
                    print(f"     Waited: {event['waited_train']} waited for")
                    print(f"     Priority: {event['priority_train']} (higher priority)")
                    print(f"     Time: {event['wait_started']} -> {event['wait_ended']}")
                    print()
        
        # Recommendations
        print(f"\nOPERATIONAL RECOMMENDATIONS")
        print("-" * 80)
        for recommendation in solution["recommendations"]:
            print(recommendation)
        
        print("\\n" + "=" * 80)
    
    def find_track(self, from_station: str, to_station: str):
        """Find track connection between two stations"""
        for track in self.tracks:
            if ((track["from"] == from_station and track["to"] == to_station) or
                (track["from"] == to_station and track["to"] == from_station)):
                return track
        return None

def main():
    print("\n" + "=" * 80)
    print("Enhanced Indian Railway Train Delay Optimization System")
    print("Comprehensive modeling of weather, maintenance, and operational factors")
    print("=" * 80)
    
    # Get custom delay factor from user
    print("\nCUSTOM DELAY CONFIGURATION")
    print("Enter delay factor (0.0 to 2.0):")
    print("  - 0.0 = No delays (ideal conditions)")
    print("  - 0.5 = Moderate delays")
    print("  - 1.0 = Normal delays (default)")
    print("  - 1.5 = High delays")
    
    try:
        delay_input = input("\nDelay Factor [default: 1.0]: ").strip()
        custom_delay_factor = float(delay_input) if delay_input else 1.0
        custom_delay_factor = max(0.0, min(custom_delay_factor, 2.0))  # Clamp
    except ValueError:
        print("WARNING: Invalid input, using default factor: 1.0")
        custom_delay_factor = 1.0
    
    print(f"\nUsing delay factor: {custom_delay_factor}")
    
    # Select scenario
    print("\nSELECT SCENARIO:")
    print("  1. Monsoon Season (July)")
    print("  2. Winter Fog Season (January)")
    print("  3. Summer Heat Season (April)")
    print("  4. Normal Season (October)")
    
    try:
        scenario_choice = input("\nSelect scenario [1-4, default: 1]: ").strip()
        scenario_choice = int(scenario_choice) if scenario_choice else 1
    except ValueError:
        scenario_choice = 1
    
    scenarios = {
        1: datetime(2024, 7, 15),   # Monsoon
        2: datetime(2024, 1, 15),   # Winter
        3: datetime(2024, 4, 15),   # Summer
        4: datetime(2024, 10, 15)   # Normal
    }
    
    scenario_date = scenarios.get(scenario_choice, scenarios[1])
    
    print(f"\nSelected Scenario: {scenario_date.strftime('%B %d, %Y')}")
    print(f"Delay Multiplier: {custom_delay_factor}x")
    print("=" * 80)
    
    optimizer = EnhancedIndianRailwayOptimizer(
        scenario_date=scenario_date,
        custom_delay_factor=custom_delay_factor
    )
    
    solution = optimizer.solve_optimization()
    optimizer.print_comprehensive_results(solution)
    
    # Export results
    filename = f"optimization_results_{scenario_date.strftime('%Y_%m_%d')}_delay_{custom_delay_factor}.json"
    with open(filename, 'w') as f:
        json.dump(solution, f, indent=2, default=str)
    
    print(f"\nResults exported to '{filename}'")

def quick_test(delay_factor: float = 1.0):

    print(f"\nQUICK TEST MODE - Delay Factor: {delay_factor}x")
    
    optimizer = EnhancedIndianRailwayOptimizer(
        scenario_date=datetime(2024, 7, 15),
        custom_delay_factor=delay_factor
    )
    
    solution = optimizer.solve_optimization()
    
    metrics = solution.get("performance_metrics", {})
    print(f"\nQUICK RESULTS:")
    print(f"   Punctuality: {metrics.get('punctuality_percentage', 0):.1f}%")
    print(f"   Avg Delay: {metrics.get('average_delay_per_train', 0):.1f} min")
    print(f"   Total Delay: {metrics.get('total_system_delay_minutes', 0)} min")
    
    return solution

if __name__ == "__main__":
    main()