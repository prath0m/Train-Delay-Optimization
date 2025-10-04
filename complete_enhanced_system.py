#!/usr/bin/env python3
"""
Enhanced Indian Railway Train Delay Optimization System
Comprehensive system incorporating weather, maintenance, operational constraints
Based on your railway network diagram and Indian Railway operating conditions
"""

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
    """
    Enhanced railway optimization system incorporating comprehensive 
    Indian railway operational factors and constraints
    """
    
    def __init__(self, scenario_date: datetime = None):
        self.model = cp_model.CpModel()
        self.scenario_date = scenario_date or datetime.now()
        
        # Network definition based on your diagram
        self.stations = [
            "Karjat_Hold_Point", "Station_C", "Station_A", "Station_J",
            "Lonavala_Hold_Point", "Junction_Z", "Station_B", "Junction_X", 
            "Station_G", "H_Loop", "Station_D", "Junction_Y"
        ]
        
        # Enhanced track network with realistic Indian railway characteristics
        self.tracks = [
            # Main line double track sections
            {"from": "Station_C", "to": "Station_A", "length_km": 18, "tracks": 2, 
             "min_travel_time": 15, "gradient": "level", "electrified": True},
            {"from": "Station_A", "to": "Station_J", "length_km": 19, "tracks": 2,
             "min_travel_time": 16, "gradient": "level", "electrified": True},
            
            # Critical single track sections (Bhor Ghats equivalent)
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
        
        # Comprehensive train fleet with Indian railway characteristics
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
        
        # Weather and operational scenarios
        self.weather_scenarios = self._get_weather_scenario()
        self.maintenance_blocks = self._get_maintenance_blocks()
        self.operational_constraints = self._get_operational_constraints()
        
        # Model variables
        self.time_vars = {}
        self.delay_vars = {}
        self.assignment_vars = {}
        self.intervals = {}
        
    def _get_weather_scenario(self) -> Dict:
        """Get weather scenario based on date and season"""
        month = self.scenario_date.month
        
        if month in [6, 7, 8, 9]:  # Monsoon season
            return {
                "season": "monsoon",
                "conditions": {
                    "Station_J_to_Lonavala_Hold_Point": {
                        "condition": WeatherCondition.HEAVY_RAIN,
                        "speed_reduction": 0.4,  # 40% speed reduction
                        "additional_time": 20,   # 20 minutes extra
                        "visibility": "poor"
                    },
                    "Lonavala_Hold_Point_to_Junction_Z": {
                        "condition": WeatherCondition.HEAVY_RAIN,
                        "speed_reduction": 0.3,
                        "additional_time": 8,
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
                        "speed_reduction": 0.5,  # 50% speed reduction
                        "additional_time": 15,
                        "visibility": "very_poor"
                    },
                    "Junction_Z_to_Station_B": {
                        "condition": WeatherCondition.FOG,
                        "speed_reduction": 0.4,
                        "additional_time": 10,
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
                        "speed_reduction": 0.2,  # Heat affects rail expansion
                        "additional_time": 10,
                        "visibility": "good"
                    }
                }
            }
        else:
            return {"season": "normal", "conditions": {}}
    
    def _get_maintenance_blocks(self) -> List[Dict]:
        """Get scheduled maintenance blocks"""
        return [
            {
                "section": "Station_A_to_Station_J",
                "type": "track_renewal",
                "start_time": 120,  # 2:00 AM
                "end_time": 360,    # 6:00 AM
                "speed_limit": 0.3,  # 30% of normal speed
                "single_line_working": True
            },
            {
                "section": "Junction_X_to_Station_G", 
                "type": "signaling_maintenance",
                "start_time": 60,   # 1:00 AM
                "end_time": 300,    # 5:00 AM
                "speed_limit": 0.5,
                "single_line_working": False
            }
        ]
    
    def _get_operational_constraints(self) -> Dict:
        """Get Indian Railway operational constraints"""
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
        """Initialize all decision variables for the optimization model"""
        horizon = 24 * 60  # 24 hours in minutes
        
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
        """Add fundamental railway operational constraints"""
        for train in self.trains:
            train_id = train["id"]
            route = train["route"]
            
            # Set initial departure time
            scheduled_dep = train.get("scheduled_departure", 480)  # Default 8:00 AM
            first_station = route[0]
            
            # Departure from first station (with possible initial delay)
            initial_delay = self.model.NewIntVar(0, 60, f"initial_delay_{train_id}")
            self.model.Add(
                self.time_vars[train_id]["departure"][first_station] == 
                scheduled_dep + initial_delay
            )
            
            # Travel time and sequencing constraints
            for i in range(len(route) - 1):
                from_station = route[i]
                to_station = route[i + 1]
                
                track = self.find_track(from_station, to_station)
                if track is None:
                    continue
                
                base_time = track["min_travel_time"]
                
                # Calculate dynamic travel time including delays
                actual_travel_time = self.model.NewIntVar(
                    base_time, base_time * 3, f"travel_{train_id}_{from_station}_{to_station}")
                
                # Travel time includes weather and maintenance impacts
                self.model.Add(
                    actual_travel_time >= base_time + 
                    self.delay_vars[train_id]["weather"][to_station] +
                    self.delay_vars[train_id]["maintenance"][to_station]
                )
                
                # Arrival = Departure + Travel time
                self.model.Add(
                    self.time_vars[train_id]["arrival"][to_station] ==
                    self.time_vars[train_id]["departure"][from_station] + actual_travel_time
                )
                
                # Dwell time constraints
                if i > 0:  # Not the first station
                    min_dwell = self._get_minimum_dwell_time(train, from_station)
                    self.model.Add(self.time_vars[train_id]["dwell"][from_station] >= min_dwell)
                    
                    self.model.Add(
                        self.time_vars[train_id]["departure"][from_station] ==
                        self.time_vars[train_id]["arrival"][from_station] + 
                        self.time_vars[train_id]["dwell"][from_station]
                    )
    
    def _get_minimum_dwell_time(self, train, station: str) -> int:
        """Calculate minimum dwell time based on train and station type"""
        if station not in self.station_config:
            return 1  # Minimum 1 minute
        
        station_info = self.station_config[station]
        train_type_key = train["type"].value
        
        base_dwell = station_info["dwell_times"].get(train_type_key, 3)
        
        # Add extra time for crew changes
        if station_info.get("crew_change", False):
            base_dwell += 5
        
        # Add extra time for water column stops (longer trains)
        if train.get("coaches", 12) > 16 and station_info.get("water_column", False):
            base_dwell += 3
        
        return base_dwell
    
    def add_weather_impact_constraints(self):
        """Add weather-based operational constraints"""
        conditions = self.weather_scenarios.get("conditions", {})
        
        for section, impact in conditions.items():
            # Parse section to get stations
            parts = section.replace("_to_", "_").split("_")
            if len(parts) >= 2:
                from_station = "_".join(parts[:-1])
                to_station = parts[-1]
                
                for train in self.trains:
                    train_id = train["id"]
                    route = train["route"]
                    
                    if from_station in route and to_station in route:
                        from_idx = route.index(from_station)
                        to_idx = route.index(to_station)
                        
                        if abs(to_idx - from_idx) == 1:  # Direct connection
                            weather_delay = impact["additional_time"]
                            
                            # Apply weather delay
                            self.model.Add(
                                self.delay_vars[train_id]["weather"][to_station] >= weather_delay
                            )
                            
                            # Passenger trains get priority in bad weather
                            if train["type"] in [TrainType.SUPERFAST, TrainType.EXPRESS]:
                                # Reduce weather impact for priority trains
                                self.model.Add(
                                    self.delay_vars[train_id]["weather"][to_station] >= 
                                    int(weather_delay * 0.7)  # 30% reduction
                                )
    
    def add_maintenance_constraints(self):
        """Add maintenance block constraints"""
        for block in self.maintenance_blocks:
            block_start = block["start_time"]
            block_end = block["end_time"]
            section = block["section"]
            
            # Parse section
            parts = section.replace("_to_", "_").split("_")
            if len(parts) >= 2:
                from_station = "_".join(parts[:-1])
                to_station = parts[-1]
                
                for train in self.trains:
                    train_id = train["id"]
                    route = train["route"]
                    
                    if from_station in route and to_station in route:
                        # Check if train travels during maintenance window
                        maintenance_conflict = self.model.NewBoolVar(
                            f"maintenance_conflict_{train_id}_{section}")
                        
                        departure_time = self.time_vars[train_id]["departure"][from_station]
                        
                        # Conflict if departure is during maintenance
                        self.model.Add(departure_time >= block_start).OnlyEnforceIf(maintenance_conflict)
                        self.model.Add(departure_time <= block_end).OnlyEnforceIf(maintenance_conflict)
                        
                        # If conflict, add significant maintenance delay
                        maintenance_delay = 30 if block["single_line_working"] else 15
                        self.model.Add(
                            self.delay_vars[train_id]["maintenance"][to_station] >= maintenance_delay
                        ).OnlyEnforceIf(maintenance_conflict)
    
    def add_single_track_constraints(self):
        """Add single track operation constraints"""
        single_tracks = [track for track in self.tracks if track["tracks"] == 1]
        
        for track in single_tracks:
            from_station = track["from"]
            to_station = track["to"]
            
            # Collect intervals for this track
            intervals = []
            
            for train in self.trains:
                train_id = train["id"]
                route = train["route"]
                
                if from_station in route and to_station in route:
                    from_idx = route.index(from_station)
                    to_idx = route.index(to_station)
                    
                    if abs(to_idx - from_idx) == 1:  # Direct connection
                        travel_time = track["min_travel_time"]
                        
                        if from_idx < to_idx:  # Forward direction
                            interval = self.model.NewIntervalVar(
                                self.time_vars[train_id]["departure"][from_station],
                                travel_time,
                                self.time_vars[train_id]["arrival"][to_station],
                                f"single_track_{train_id}_{from_station}_{to_station}"
                            )
                        else:  # Reverse direction
                            interval = self.model.NewIntervalVar(
                                self.time_vars[train_id]["departure"][to_station],
                                travel_time, 
                                self.time_vars[train_id]["arrival"][from_station],
                                f"single_track_{train_id}_{to_station}_{from_station}"
                            )
                        
                        intervals.append(interval)
            
            # No overlap constraint
            if intervals:
                self.model.AddNoOverlap(intervals)
    
    def add_priority_constraints(self):
        """Add train priority and overtaking constraints"""
        priority_rules = self.operational_constraints["priority_rules"]
        
        for station in self.stations:
            if station not in self.station_config:
                continue
            
            # Find trains that stop at this station
            station_trains = [t for t in self.trains if station in t["route"]]
            
            if len(station_trains) < 2:
                continue
            
            # Apply priority rules for each pair of trains
            for i, train1 in enumerate(station_trains):
                for train2 in station_trains[i+1:]:
                    type1 = train1["type"].value
                    type2 = train2["type"].value
                    
                    # Check if train1 can overtake train2
                    if type2 in priority_rules.get(type1, {}).get("can_overtake", []):
                        # Train1 has priority over train2
                        overtake = self.model.NewBoolVar(f"overtake_{train1['id']}_{train2['id']}_{station}")
                        
                        # If overtaking, higher priority train departs first
                        min_sep = self.operational_constraints["crossing_rules"]["minimum_separation"]
                        
                        self.model.Add(
                            self.time_vars[train1["id"]]["departure"][station] + min_sep <=
                            self.time_vars[train2["id"]]["departure"][station]
                        ).OnlyEnforceIf(overtake)
    
    def add_platform_capacity_constraints(self):
        """Add platform and loop capacity constraints"""
        for station, config in self.station_config.items():
            total_capacity = config["platforms"] + config["loops"]
            
            # Get trains using this station
            station_trains = [t for t in self.trains if station in t["route"]]
            
            if len(station_trains) <= total_capacity:
                continue  # No capacity issues
            
            # Create platform occupation intervals
            intervals = []
            demands = []
            
            for train in station_trains:
                train_id = train["id"]
                
                # Platform occupation interval
                interval = self.model.NewIntervalVar(
                    self.time_vars[train_id]["arrival"][station],
                    self.time_vars[train_id]["dwell"][station],
                    self.time_vars[train_id]["departure"][station],
                    f"platform_occupation_{train_id}_{station}"
                )
                
                intervals.append(interval)
                demands.append(1)  # Each train needs 1 platform/loop
            
            # Cumulative capacity constraint
            self.model.AddCumulative(intervals, demands, total_capacity)
    
    def add_freight_restrictions(self):
        """Add freight movement restrictions during peak hours"""
        restrictions = self.operational_constraints["freight_restrictions"]
        
        for train in self.trains:
            if train["type"] not in [TrainType.FREIGHT, TrainType.GOODS]:
                continue
                
            train_id = train["id"]
            
            # Parse peak hours and add restrictions
            for peak_period in restrictions["peak_hours"]:
                start_time, end_time = peak_period.split("-")
                start_minutes = self._time_to_minutes(start_time)
                end_minutes = self._time_to_minutes(end_time)
                
                # Check each station in freight train route
                for station in train["route"]:
                    restriction_violation = self.model.NewBoolVar(
                        f"freight_restriction_{train_id}_{station}_{peak_period}"
                    )
                    
                    # Violation if departure is during peak hours
                    dep_time = self.time_vars[train_id]["departure"][station]
                    
                    self.model.Add(dep_time >= start_minutes).OnlyEnforceIf(restriction_violation)
                    self.model.Add(dep_time <= end_minutes).OnlyEnforceIf(restriction_violation)
                    
                    # Penalty for peak hour freight movement
                    self.model.Add(
                        self.delay_vars[train_id]["operational"][station] >= 45
                    ).OnlyEnforceIf(restriction_violation)
    
    def _time_to_minutes(self, time_str: str) -> int:
        """Convert HH:MM to minutes from midnight"""
        hours, minutes = map(int, time_str.split(":"))
        return hours * 60 + minutes
    
    def set_optimization_objective(self):
        """Set comprehensive multi-objective optimization function"""
        delay_penalty = 0
        punctuality_bonus = 0
        operational_efficiency = 0
        
        # 1. Minimize total weighted delays
        for train in self.trains:
            train_id = train["id"]
            priority = train["priority"]
            
            for station in train["route"]:
                # Sum all delay components for this station
                total_delay = sum([
                    self.delay_vars[train_id][delay_type][station]
                    for delay_type in ["weather", "maintenance", "congestion", "operational"]
                ])
                
                # Weight delays by train priority
                if train["type"] == TrainType.SUPERFAST:
                    weight = 5  # Highest penalty for Rajdhani/Shatabdi delays
                elif train["type"] == TrainType.EXPRESS:
                    weight = 3  # High penalty for Express delays
                elif train["type"] == TrainType.PASSENGER:
                    weight = 2  # Medium penalty for Passenger delays
                else:
                    weight = 1  # Lower penalty for Freight delays
                
                delay_penalty += total_delay * int(priority * weight * 100)
        
        # 2. Punctuality bonus (reward on-time performance)
        for train in self.trains:
            train_id = train["id"]
            
            # Check final station punctuality
            final_station = train["route"][-1]
            scheduled_arrival = train.get("scheduled_departure", 480) + 120  # Assume 2-hour journey
            actual_arrival = self.time_vars[train_id]["arrival"][final_station]
            
            # On-time if within 5 minutes of schedule
            on_time = self.model.NewBoolVar(f"on_time_{train_id}")
            
            self.model.Add(actual_arrival <= scheduled_arrival + 5).OnlyEnforceIf(on_time)
            self.model.Add(actual_arrival > scheduled_arrival + 5).OnlyEnforceIf(on_time.Not())
            
            # Bonus points for punctuality
            punctuality_bonus += on_time * int(train["priority"] * 1000)
        
        # 3. Operational efficiency (minimize resource conflicts)
        for station in self.station_config:
            station_trains = [t for t in self.trains if station in t["route"]]
            
            # Minimize platform idle time
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
            operational_efficiency -  # Minimize inefficiency (positive)  
            punctuality_bonus        # Maximize punctuality (subtract to maximize)
        )
        
        self.model.Minimize(total_objective)
    
    def solve_optimization(self) -> Dict:
        """Solve the comprehensive railway optimization problem"""
        print("🚂 Enhanced Indian Railway Delay Optimization")
        print(f"📅 Scenario Date: {self.scenario_date.strftime('%B %d, %Y')}")
        print(f"🌦️  Weather Season: {self.weather_scenarios['season'].title()}")
        print(f"🔧 Maintenance Blocks: {len(self.maintenance_blocks)}")
        print("=" * 60)
        
        print("Building comprehensive optimization model...")
        
        # Build model step by step
        self.initialize_model_variables()
        print("   ✅ Variables initialized")
        
        self.add_basic_operational_constraints()
        print("   ✅ Basic operational constraints")
        
        self.add_weather_impact_constraints()
        print("   ✅ Weather impact constraints")
        
        self.add_maintenance_constraints()
        print("   ✅ Maintenance constraints")
        
        self.add_single_track_constraints()
        print("   ✅ Single track constraints")
        
        self.add_priority_constraints()
        print("   ✅ Priority and overtaking rules")
        
        self.add_platform_capacity_constraints()
        print("   ✅ Platform capacity constraints")
        
        self.add_freight_restrictions()
        print("   ✅ Freight movement restrictions")
        
        self.set_optimization_objective()
        print("   ✅ Multi-objective function set")
        
        print("\\nSolving optimization problem...")
        
        # Configure and run solver
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = 300.0  # 5 minutes
        solver.parameters.num_search_workers = 8
        
        status = solver.Solve(self.model)
        
        # Extract and return solution
        return self._extract_solution(solver, status)
    
    def _extract_solution(self, solver, status) -> Dict:
        """Extract comprehensive solution with metrics"""
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
            solution["error"] = "No feasible solution found"
            return solution
        
        # Extract train schedules
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
            
            # Check punctuality (≤ 5 minutes delay at final destination)
            final_delays = list(train_delays[train["route"][-1]].values())
            if sum(final_delays) <= 5:
                on_time_trains += 1
        
        # Calculate system metrics
        solution["performance_metrics"] = {
            "total_system_delay_minutes": total_system_delay,
            "average_delay_per_train": total_system_delay / len(self.trains),
            "punctuality_percentage": (on_time_trains / len(self.trains)) * 100,
            "on_time_trains": on_time_trains,
            "total_trains": len(self.trains)
        }
        
        # Generate operational insights
        solution["operational_insights"] = self._analyze_performance(solution)
        solution["recommendations"] = self._generate_recommendations(solution)
        
        return solution
    
    def _format_time(self, minutes: int) -> str:
        """Convert minutes to HH:MM format"""
        hours = minutes // 60
        mins = minutes % 60
        return f"{hours:02d}:{mins:02d}"
    
    def _analyze_performance(self, solution) -> Dict:
        """Analyze system performance and identify issues"""
        insights = {}
        
        # Weather impact analysis
        weather_delays = sum(
            sum(train_data["delays"][station].get("weather", 0) 
                for station in train_data["delays"])
            for train_data in solution["train_schedules"].values()
        )
        insights["weather_impact"] = "High" if weather_delays > 100 else "Moderate" if weather_delays > 50 else "Low"
        
        # Maintenance impact analysis
        maintenance_delays = sum(
            sum(train_data["delays"][station].get("maintenance", 0)
                for station in train_data["delays"])
            for train_data in solution["train_schedules"].values()
        )
        insights["maintenance_impact"] = "High" if maintenance_delays > 80 else "Moderate" if maintenance_delays > 40 else "Low"
        
        # Single track bottlenecks
        single_track_sections = [t for t in self.tracks if t["tracks"] == 1]
        insights["single_track_bottlenecks"] = len(single_track_sections)
        
        # Priority train performance
        superfast_delays = [
            train_data["total_delay"] 
            for train_data in solution["train_schedules"].values()
            if train_data["type"] == "superfast"
        ]
        insights["premium_train_performance"] = "Good" if all(d <= 10 for d in superfast_delays) else "Needs Improvement"
        
        return insights
    
    def _generate_recommendations(self, solution) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        metrics = solution["performance_metrics"]
        insights = solution["operational_insights"]
        
        # Punctuality recommendations
        if metrics["punctuality_percentage"] < 80:
            recommendations.append("🎯 PRIORITY: Punctuality below 80% target")
            recommendations.append("   • Review and optimize station dwell times")
            recommendations.append("   • Consider dynamic scheduling adjustments")
        
        # Weather impact recommendations
        if insights["weather_impact"] == "High":
            recommendations.append("🌧️  HIGH WEATHER IMPACT detected")
            recommendations.append("   • Implement weather-specific speed restrictions")
            recommendations.append("   • Enhance drainage systems on critical sections")
            recommendations.append("   • Consider weather forecasting integration")
        
        # Maintenance optimization
        if insights["maintenance_impact"] == "High":
            recommendations.append("🔧 MAINTENANCE IMPACT significant")
            recommendations.append("   • Reschedule maintenance during low-traffic periods")
            recommendations.append("   • Coordinate multiple maintenance activities")
            recommendations.append("   • Implement faster maintenance techniques")
        
        # Infrastructure recommendations
        if insights["single_track_bottlenecks"] > 0:
            recommendations.append(f"🚧 BOTTLENECK: {insights['single_track_bottlenecks']} single track sections")
            recommendations.append("   • Priority: Double tracking of Lonavala-Junction_Z section")
            recommendations.append("   • Add additional crossing loops")
            recommendations.append("   • Implement automatic block signaling")
        
        # Premium service recommendations
        if insights["premium_train_performance"] == "Needs Improvement":
            recommendations.append("⭐ PREMIUM SERVICES need attention")
            recommendations.append("   • Guarantee priority paths for Rajdhani/Shatabdi trains")
            recommendations.append("   • Implement dynamic rescheduling for delays")
            recommendations.append("   • Review crew scheduling for premium trains")
        
        # General efficiency recommendations
        if metrics["average_delay_per_train"] > 15:
            recommendations.append("📈 HIGH AVERAGE DELAYS detected")
            recommendations.append("   • Implement real-time train tracking")
            recommendations.append("   • Optimize signal spacing and timing")
            recommendations.append("   • Review timetable buffer times")
        
        return recommendations
    
    def print_comprehensive_results(self, solution):
        """Print detailed optimization results"""
        print("\\n" + "=" * 80)
        print("🚂 COMPREHENSIVE INDIAN RAILWAY OPTIMIZATION RESULTS")
        print("=" * 80)
        
        if solution.get("error"):
            print(f"❌ {solution['error']}")
            return
        
        # System overview
        print(f"✅ Solution Status: {solution['status']}")
        print(f"🎯 Objective Value: {solution['objective_value']}")
        print(f"⏱️  Solve Time: {solution['solve_time']:.2f} seconds")
        
        # Performance metrics
        metrics = solution["performance_metrics"]
        print(f"\\n📊 SYSTEM PERFORMANCE METRICS")
        print(f"   Total System Delay: {metrics['total_system_delay_minutes']} minutes")
        print(f"   Average Delay per Train: {metrics['average_delay_per_train']:.1f} minutes")
        print(f"   Punctuality Rate: {metrics['punctuality_percentage']:.1f}% ({metrics['on_time_trains']}/{metrics['total_trains']} trains)")
        
        # Weather and operational analysis
        insights = solution["operational_insights"]
        print(f"\\n🌦️  OPERATIONAL ANALYSIS")
        print(f"   Weather Impact: {insights['weather_impact']}")
        print(f"   Maintenance Impact: {insights['maintenance_impact']}")
        print(f"   Single Track Bottlenecks: {insights['single_track_bottlenecks']} sections")
        print(f"   Premium Train Performance: {insights['premium_train_performance']}")
        
        # Detailed train schedules
        print(f"\\n🚂 OPTIMIZED TRAIN SCHEDULES")
        print("-" * 80)
        
        for train in self.trains:
            train_id = train["id"]
            train_data = solution["train_schedules"][train_id]
            
            print(f"\\n{train_id}")
            print(f"Type: {train_data['type'].title()}, Priority: {train_data['priority']}, Total Delay: {train_data['total_delay']} min")
            
            for station in train["route"]:
                schedule = train_data["schedule"][station]
                delays = train_data["delays"][station]
                
                total_station_delay = sum(delays.values())
                delay_indicator = "🔴" if total_station_delay > 15 else "🟡" if total_station_delay > 5 else "🟢"
                
                print(f"  {station:25s} | Arr: {schedule['arrival']} | Dep: {schedule['departure']} | "
                      f"Dwell: {schedule['dwell_minutes']:2d}min | Delay: {total_station_delay:3d}min {delay_indicator}")
                
                # Show significant delay components
                significant_delays = [f"{k}: {v}min" for k, v in delays.items() if v > 0]
                if significant_delays:
                    print(f"    └─ {', '.join(significant_delays)}")
        
        # Recommendations
        print(f"\\n💡 OPERATIONAL RECOMMENDATIONS")
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
    """Main execution function"""
    print("🚂 Enhanced Indian Railway Train Delay Optimization System")
    print("   Comprehensive modeling of weather, maintenance, and operational factors")
    print("=" * 80)
    
    # Test different seasonal scenarios
    scenarios = [
        datetime(2024, 7, 15),   # Monsoon season
        datetime(2024, 1, 15),   # Winter fog season  
        datetime(2024, 4, 15),   # Summer heat season
        datetime(2024, 10, 15)   # Normal season
    ]
    
    for scenario_date in scenarios[:1]:  # Test first scenario
        print(f"\\n🗓️  Testing Scenario: {scenario_date.strftime('%B %d, %Y')}")
        
        # Initialize and solve
        optimizer = EnhancedIndianRailwayOptimizer(scenario_date)
        solution = optimizer.solve_optimization()
        
        # Display results
        optimizer.print_comprehensive_results(solution)
        
        # Export results
        filename = f"optimization_results_{scenario_date.strftime('%Y_%m_%d')}.json"
        with open(filename, 'w') as f:
            json.dump(solution, f, indent=2, default=str)
        
        print(f"\\n📁 Results exported to '{filename}'")
        break  # Only run first scenario for demo

if __name__ == "__main__":
    main()