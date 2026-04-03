from ortools.sat.python import cp_model
from datetime import datetime
from typing import Dict, List, Optional

from enums import WeatherCondition, TrainType
from config import MAINTENANCE_PRESETS
from network import STATIONS, TRACKS, TRAINS, STATION_CONFIG


class EnhancedIndianRailwayOptimizer:

    def __init__(self, scenario_date: datetime = None, custom_delay_factor: float = 1.0,
                 maintenance_preset: int = None, custom_maintenance: List[Dict] = None):
        self.model = cp_model.CpModel()
        self.scenario_date = scenario_date or datetime.now()
        self.custom_delay_factor = max(0.0, min(custom_delay_factor, 2.0))

        self.maintenance_preset = maintenance_preset
        self.custom_maintenance = custom_maintenance

        self.stations = list(STATIONS)
        self.tracks = [dict(t) for t in TRACKS]
        self.trains = [dict(t) for t in TRAINS]
        self.station_config = {k: dict(v) for k, v in STATION_CONFIG.items()}

        self.weather_scenarios = self._get_weather_scenario()
        self.maintenance_blocks = self._get_maintenance_blocks()
        self.operational_constraints = self._get_operational_constraints()

        self.bottleneck_sections = self._identify_bottlenecks()

        self.time_vars = {}
        self.delay_vars = {}
        self.assignment_vars = {}
        self.intervals = {}

    # ------------------------------------------------------------------
    # Configuration helpers
    # ------------------------------------------------------------------

    def _get_weather_scenario(self) -> Dict:
        month = self.scenario_date.month

        if month in [6, 7, 8, 9]:
            return {
                "season": "monsoon",
                "conditions": {
                    "Station_A_to_Lonavala_Hold_Point": {
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
        elif month in [12, 1, 2]:
            return {
                "season": "winter",
                "conditions": {
                    "Station_J_to_Station_A": {
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
        elif month in [4, 5]:
            return {
                "season": "summer",
                "conditions": {
                    "Station_A_to_Lonavala_Hold_Point": {
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
        if self.custom_maintenance is not None:
            return self.custom_maintenance

        if self.maintenance_preset is not None:
            preset = MAINTENANCE_PRESETS.get(self.maintenance_preset, MAINTENANCE_PRESETS[0])
            blocks = preset.get("blocks", [])
            for block in blocks:
                block["speed_limit"] = block.get("speed_limit", 0.5) * self.custom_delay_factor
            return blocks

        return MAINTENANCE_PRESETS[5]["blocks"]

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
                "minimum_separation": 5,
                "single_track_precedence": "priority_based"
            },
            "freight_restrictions": {
                "peak_hours": ["07:00-10:00", "17:00-20:00"],
                "restricted_sections": ["Station_C_to_Station_J", "Junction_Z_to_Station_B"]
            },
            "crew_constraints": {
                "maximum_duty_hours": 8 * 60,
                "minimum_rest_time": 30,
                "crew_change_stations": ["Station_C", "Station_J", "Junction_Z"]
            }
        }

    def _identify_bottlenecks(self) -> List[Dict]:
        bottlenecks = []

        for track in self.tracks:
            if track.get("bottleneck", False):
                bottleneck_info = {
                    "section": f"{track['from']}_to_{track['to']}",
                    "from": track["from"],
                    "to": track["to"],
                    "severity": 1.0 if track["tracks"] == 1 else 0.5,
                    "gradient": track.get("gradient", "level"),
                    "crossing_loops": track.get("crossing_loops", 1),
                    "max_hourly_capacity": track.get("max_hourly_capacity", 2),
                    "priority_factor": 1.0
                }

                if "steep" in track.get("gradient", ""):
                    bottleneck_info["priority_factor"] *= 2.0
                if "bridge" in track.get("notes", "").lower():
                    bottleneck_info["priority_factor"] *= 1.5

                bottlenecks.append(bottleneck_info)

        bottlenecks.sort(key=lambda x: x["priority_factor"], reverse=True)
        return bottlenecks

    # ------------------------------------------------------------------
    # Model building
    # ------------------------------------------------------------------

    def initialize_model_variables(self):
        horizon = 36 * 60

        for train in self.trains:
            train_id = train["id"]

            self.time_vars[train_id] = {
                "arrival": {}, "departure": {}, "dwell": {}
            }
            self.delay_vars[train_id] = {
                "weather": {}, "maintenance": {}, "congestion": {}, "operational": {}
            }
            self.assignment_vars[train_id] = {}

            for station in train["route"]:
                self.time_vars[train_id]["arrival"][station] = self.model.NewIntVar(
                    0, horizon, f"arr_{train_id}_{station}")
                self.time_vars[train_id]["departure"][station] = self.model.NewIntVar(
                    0, horizon, f"dep_{train_id}_{station}")
                self.time_vars[train_id]["dwell"][station] = self.model.NewIntVar(
                    0, 60, f"dwell_{train_id}_{station}")

                for delay_type in ["weather", "maintenance", "congestion", "operational"]:
                    self.delay_vars[train_id][delay_type][station] = self.model.NewIntVar(
                        0, 180, f"{delay_type}_delay_{train_id}_{station}")

                if station in self.station_config:
                    max_platforms = (self.station_config[station]["platforms"] +
                                     self.station_config[station]["loops"])
                    self.assignment_vars[train_id][station] = self.model.NewIntVar(
                        1, max_platforms, f"platform_{train_id}_{station}")

    def add_basic_operational_constraints(self):
        for train in self.trains:
            train_id = train["id"]
            route = train["route"]

            scheduled_dep = train.get("scheduled_departure", 480)
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
                gradient_factor = 1.0

                if track.get("gradient") == "steep_climb":
                    if train["type"] in [TrainType.FREIGHT, TrainType.GOODS]:
                        gradient_factor = 1.4
                    elif train["type"] in [TrainType.SUPERFAST, TrainType.EXPRESS]:
                        gradient_factor = 1.15
                    else:
                        gradient_factor = 1.3

                section_key = f"{from_station}_to_{to_station}"
                weather_conditions = self.weather_scenarios.get("conditions", {})

                min_travel_time = int(base_time * gradient_factor)

                if section_key in weather_conditions:
                    weather_additional = int(
                        weather_conditions[section_key]["additional_time"] * self.custom_delay_factor
                    )
                    if train["type"] in [TrainType.SUPERFAST, TrainType.EXPRESS]:
                        weather_additional = int(weather_additional * 0.5)
                    min_travel_time = int(base_time * gradient_factor) + weather_additional

                if train["type"] in [TrainType.FREIGHT, TrainType.GOODS]:
                    flexibility_multiplier = 1.15
                else:
                    flexibility_multiplier = 1.05

                if track.get("bottleneck", False):
                    flexibility_multiplier *= 1.1

                max_travel_time = int(min_travel_time * flexibility_multiplier) + 3

                actual_travel_time = self.model.NewIntVar(
                    min_travel_time, max_travel_time,
                    f"travel_{train_id}_{from_station}_{to_station}")

                self.model.Add(actual_travel_time >= min_travel_time)

                self.model.Add(
                    self.time_vars[train_id]["arrival"][to_station] ==
                    self.time_vars[train_id]["departure"][from_station] + actual_travel_time
                )

                if i > 0:
                    min_dwell = self._get_minimum_dwell_time(train, from_station)
                    self.model.Add(self.time_vars[train_id]["dwell"][from_station] >= min_dwell)

                    self.model.Add(
                        self.time_vars[train_id]["departure"][from_station] ==
                        self.time_vars[train_id]["arrival"][from_station] +
                        self.time_vars[train_id]["dwell"][from_station]
                    )

    def _get_minimum_dwell_time(self, train, station: str) -> int:
        if station not in self.station_config:
            return 1

        station_info = self.station_config[station]
        train_type_key = train["type"].value

        base_dwell = station_info["dwell_times"].get(train_type_key, 3)

        if station_info.get("crew_change", False) and train_type_key in ["superfast", "express", "mail_express"]:
            base_dwell += 5

        if station_info.get("maintenance_depot", False) and train_type_key in ["freight", "goods"]:
            base_dwell += 2

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
                    weather_delay = int(
                        conditions[section_key]["additional_time"] * self.custom_delay_factor
                    )

                    if train["type"] == TrainType.SUPERFAST:
                        weather_delay = 0
                    elif train["type"] == TrainType.EXPRESS:
                        weather_delay = int(weather_delay * 0.2)
                    elif train["type"] == TrainType.MAIL_EXPRESS:
                        weather_delay = int(weather_delay * 0.5)

                    self.model.Add(
                        self.delay_vars[train_id]["weather"][to_station] == weather_delay
                    )
                else:
                    self.model.Add(
                        self.delay_vars[train_id]["weather"][to_station] == 0
                    )

            if route:
                self.model.Add(self.delay_vars[train_id]["weather"][route[0]] == 0)

    def add_maintenance_constraints(self):
        for train in self.trains:
            train_id = train["id"]
            for station in train["route"]:
                self.model.Add(self.delay_vars[train_id]["maintenance"][station] == 0)

    def add_single_track_constraints(self):
        single_tracks = [track for track in self.tracks if track["tracks"] == 1]

        for track in single_tracks:
            from_station = track["from"]
            to_station = track["to"]
            is_bottleneck = track.get("bottleneck", False)

            intervals = []

            for train in self.trains:
                train_id = train["id"]
                route = train["route"]

                if from_station in route and to_station in route:
                    from_idx = route.index(from_station)
                    to_idx = route.index(to_station)

                    if abs(to_idx - from_idx) == 1:
                        buffer_time = 3 if is_bottleneck else 2

                        if from_idx < to_idx:
                            start_time = self.time_vars[train_id]["departure"][from_station]
                            end_time = self.time_vars[train_id]["arrival"][to_station]

                            buffered_end = self.model.NewIntVar(
                                0, 36 * 60, f"buffered_end_{train_id}_{from_station}_{to_station}"
                            )
                            self.model.Add(buffered_end == end_time + buffer_time)

                            duration = self.model.NewIntVar(
                                track["min_travel_time"], track["min_travel_time"] * 4,
                                f"duration_{train_id}_{from_station}_{to_station}"
                            )
                            self.model.Add(duration == end_time - start_time + buffer_time)

                            interval = self.model.NewIntervalVar(
                                start_time, duration, buffered_end,
                                f"single_track_{train_id}_{from_station}_{to_station}"
                            )
                        else:
                            start_time = self.time_vars[train_id]["departure"][to_station]
                            end_time = self.time_vars[train_id]["arrival"][from_station]

                            buffered_end = self.model.NewIntVar(
                                0, 36 * 60, f"buffered_end_{train_id}_{to_station}_{from_station}"
                            )
                            self.model.Add(buffered_end == end_time + buffer_time)

                            duration = self.model.NewIntVar(
                                track["min_travel_time"], track["min_travel_time"] * 4,
                                f"duration_{train_id}_{to_station}_{from_station}"
                            )
                            self.model.Add(duration == end_time - start_time + buffer_time)

                            interval = self.model.NewIntervalVar(
                                start_time, duration, buffered_end,
                                f"single_track_{train_id}_{to_station}_{from_station}"
                            )

                        intervals.append(interval)

            if intervals:
                self.model.AddNoOverlap(intervals)

    def add_priority_constraints(self):
        priority_rules = self.operational_constraints["priority_rules"]

        for station in self.stations:
            if station not in self.station_config:
                continue

            station_trains = [t for t in self.trains if station in t["route"]]

            if len(station_trains) < 2:
                continue

            station_trains_sorted = sorted(station_trains, key=lambda t: t["priority"], reverse=True)

            for i, train1 in enumerate(station_trains_sorted):
                for train2 in station_trains_sorted[i + 1:]:
                    priority_diff = train1["priority"] - train2["priority"]

                    if priority_diff >= 0.5:
                        train1_first = self.model.NewBoolVar(
                            f"priority_order_{train1['id']}_before_{train2['id']}_{station}"
                        )

                        min_sep = self.operational_constraints["crossing_rules"]["minimum_separation"]
                        large_gap = 90

                        self.model.Add(
                            self.time_vars[train1["id"]]["departure"][station] + min_sep <=
                            self.time_vars[train2["id"]]["departure"][station]
                        ).OnlyEnforceIf(train1_first)

                        self.model.Add(
                            self.time_vars[train2["id"]]["departure"][station] + large_gap <=
                            self.time_vars[train1["id"]]["arrival"][station]
                        ).OnlyEnforceIf(train1_first.Not())

            for i, train1 in enumerate(station_trains):
                for train2 in station_trains[i + 1:]:
                    type1 = train1["type"].value
                    type2 = train2["type"].value

                    if type2 in priority_rules.get(type1, {}).get("can_overtake", []):
                        overtake = self.model.NewBoolVar(
                            f"overtake_{train1['id']}_{train2['id']}_{station}"
                        )

                        min_sep = self.operational_constraints["crossing_rules"]["minimum_separation"]

                        self.model.Add(
                            self.time_vars[train1["id"]]["departure"][station] + min_sep <=
                            self.time_vars[train2["id"]]["departure"][station]
                        ).OnlyEnforceIf(overtake)

    def add_no_waiting_for_lower_priority_constraints(self):
        for station in self.stations:
            if station not in self.station_config:
                continue

            station_trains = [t for t in self.trains if station in t["route"]]
            station_trains_sorted = sorted(station_trains, key=lambda t: t["priority"], reverse=True)

            for i, train_high in enumerate(station_trains_sorted):
                for train_low in station_trains_sorted[i + 1:]:
                    if train_high["priority"] <= train_low["priority"]:
                        continue

                    if station not in train_high["route"] or station not in train_low["route"]:
                        continue

                    choice_var = self.model.NewBoolVar(
                        f"high_departs_first_{train_high['id']}_{train_low['id']}_{station}"
                    )

                    self.model.Add(
                        self.time_vars[train_high["id"]]["departure"][station] <=
                        self.time_vars[train_low["id"]]["departure"][station]
                    ).OnlyEnforceIf(choice_var)

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
                continue

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
                demands.append(1)

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
        bottleneck_penalty = 0
        punctuality_bonus = 0
        operational_efficiency = 0
        dwell_penalty = 0
        premium_protection = 0

        bottleneck_stations = {bn["to"] for bn in self.bottleneck_sections}

        for train in self.trains:
            train_id = train["id"]
            priority = train["priority"]

            for station in train["route"]:
                total_delay = sum([
                    self.delay_vars[train_id][delay_type][station]
                    for delay_type in ["weather", "maintenance", "congestion", "operational"]
                ])

                if train["type"] == TrainType.SUPERFAST:
                    weight = 1000
                elif train["type"] == TrainType.EXPRESS:
                    weight = 200
                elif train["type"] == TrainType.MAIL_EXPRESS:
                    weight = 80
                elif train["type"] == TrainType.PASSENGER:
                    weight = 15
                else:
                    weight = 3

                if station in bottleneck_stations:
                    bottleneck_weight = 3.0
                    bottleneck_penalty += total_delay * int(priority * priority * weight * bottleneck_weight * 150)

                delay_penalty += total_delay * int(priority * priority * weight * 100)

                if train["type"] == TrainType.SUPERFAST:
                    premium_protection += total_delay * 50000
                elif train["type"] == TrainType.EXPRESS:
                    premium_protection += total_delay * 10000

                min_dwell = self._get_minimum_dwell_time(train, station)
                actual_dwell = self.time_vars[train_id]["dwell"][station]
                extra_dwell = self.model.NewIntVar(0, 480, f"extra_dwell_{train_id}_{station}")
                self.model.Add(extra_dwell >= actual_dwell - min_dwell)
                dwell_penalty += extra_dwell * int(priority * priority * 50)

        for train in self.trains:
            train_id = train["id"]
            final_station = train["route"][-1]

            scheduled_arrival = train.get("scheduled_departure", 480) + 120
            actual_arrival = self.time_vars[train_id]["arrival"][final_station]

            on_time = self.model.NewBoolVar(f"on_time_{train_id}")
            self.model.Add(actual_arrival <= scheduled_arrival + 5).OnlyEnforceIf(on_time)
            self.model.Add(actual_arrival > scheduled_arrival + 5).OnlyEnforceIf(on_time.Not())

            if train["type"] == TrainType.SUPERFAST:
                punctuality_bonus += on_time * 100000
            elif train["type"] == TrainType.EXPRESS:
                punctuality_bonus += on_time * 30000
            elif train["type"] == TrainType.MAIL_EXPRESS:
                punctuality_bonus += on_time * 10000
            else:
                punctuality_bonus += on_time * int(train["priority"] * 1000)

        for station in self.station_config:
            station_trains = [t for t in self.trains if station in t["route"]]

            for i in range(len(station_trains) - 1):
                if (station_trains[i]["id"] in self.time_vars and
                        station_trains[i + 1]["id"] in self.time_vars):
                    train1_id = station_trains[i]["id"]
                    train2_id = station_trains[i + 1]["id"]

                    gap = self.model.NewIntVar(0, 480, f"platform_gap_{train1_id}_{train2_id}_{station}")
                    self.model.Add(
                        gap >= self.time_vars[train2_id]["arrival"][station] -
                        self.time_vars[train1_id]["departure"][station]
                    )

                    operational_efficiency += gap * 5

        total_objective = (
            delay_penalty +
            bottleneck_penalty +
            premium_protection +
            dwell_penalty +
            operational_efficiency -
            punctuality_bonus
        )

        self.model.Minimize(total_objective)

    # ------------------------------------------------------------------
    # Solve
    # ------------------------------------------------------------------

    def solve_optimization(self) -> Dict:
        print("\n" + "=" * 60)
        print("Enhanced Indian Railway Delay Optimization")
        print(f"Scenario Date: {self.scenario_date.strftime('%B %d, %Y')}")
        print(f"Weather Season: {self.weather_scenarios['season'].title()}")
        print(f"Maintenance Blocks: {len(self.maintenance_blocks)}")
        print("=" * 60)

        if self.bottleneck_sections:
            print("\nCRITICAL BOTTLENECK SECTIONS (Priority Order):")
            for i, bottleneck in enumerate(self.bottleneck_sections, 1):
                print(f"  {i}. {bottleneck['section']}")
                print(f"     - Gradient: {bottleneck['gradient']}")
                print(f"     - Crossing Loops: {bottleneck['crossing_loops']}")
                print(f"     - Max Hourly Capacity: {bottleneck['max_hourly_capacity']} trains")
                print(f"     - Priority Factor: {bottleneck['priority_factor']:.2f}x")

        print("\nBuilding comprehensive optimization model...")

        self.initialize_model_variables()
        print("   [OK] Variables initialized")

        self.add_basic_operational_constraints()
        print("   [OK] Basic operational constraints")

        self.add_weather_impact_constraints()
        print("   [OK] Weather impact constraints")

        self.add_maintenance_constraints()
        print("   [OK] Maintenance constraints")

        self.add_single_track_constraints()
        print("   [OK] Single track constraints (with bottleneck priority)")

        self.add_priority_constraints()
        print("   [OK] Priority and overtaking rules")

        self.add_no_waiting_for_lower_priority_constraints()
        print("   [OK] No waiting for lower priority constraints")

        self.add_platform_capacity_constraints()
        print("   [OK] Platform capacity constraints")

        self.add_freight_restrictions()
        print("   [OK] Freight movement restrictions")

        self.set_optimization_objective()
        print("   [OK] Multi-objective function set (bottleneck-focused)")

        print("\nSolving optimization problem...")

        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = 600.0
        solver.parameters.num_search_workers = 8
        solver.parameters.log_search_progress = False
        solver.parameters.linearization_level = 2

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

    # ------------------------------------------------------------------
    # Analysis helpers
    # ------------------------------------------------------------------

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
                    if train_i["dwell"] > min_dwell + 15:
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
        insights["critical_bottlenecks"] = len(self.bottleneck_sections)

        bottleneck_delays = {}
        for bottleneck in self.bottleneck_sections:
            section_key = f"{bottleneck['from']}_to_{bottleneck['to']}"
            section_delays = sum(
                sum(train_data["delays"].get(bottleneck['to'], {}).get(delay_type, 0)
                    for delay_type in ["weather", "maintenance", "congestion", "operational"])
                for train_data in solution["train_schedules"].values()
            )
            bottleneck_delays[section_key] = section_delays

        insights["bottleneck_delays"] = bottleneck_delays
        insights["max_bottleneck_delay"] = max(bottleneck_delays.values()) if bottleneck_delays else 0

        superfast_delays = [
            train_data["total_delay"]
            for train_data in solution["train_schedules"].values()
            if train_data["type"] == "superfast"
        ]
        insights["premium_train_performance"] = (
            "Good" if all(d <= 10 for d in superfast_delays) else "Needs Improvement"
        )

        return insights

    def _generate_recommendations(self, solution) -> List[str]:
        recommendations = []
        metrics = solution["performance_metrics"]
        insights = solution["operational_insights"]

        if insights.get("critical_bottlenecks", 0) > 0:
            max_delay = insights.get("max_bottleneck_delay", 0)
            if max_delay > 20:
                recommendations.append("[CRITICAL] BOTTLENECK CONGESTION - Immediate Action Required")
                recommendations.append(f"   - Maximum bottleneck delay: {max_delay} minutes")

                bottleneck_delays = insights.get("bottleneck_delays", {})
                for section, delay in sorted(bottleneck_delays.items(), key=lambda x: x[1], reverse=True)[:2]:
                    recommendations.append(f"   - {section}: {delay} min cumulative delay")

                recommendations.append("   - PRIORITY: Double-track the Lonavala_Hold_Point to Junction_Z section (currently single track)")
                recommendations.append("   - Install 3+ additional crossing loops on critical sections")
                recommendations.append("   - Implement advanced traffic management system for bottleneck sections")
                recommendations.append("   - Consider freight train rerouting during peak hours")

        if metrics["punctuality_percentage"] < 80:
            recommendations.append("[PRIORITY] Punctuality below 80% target")
            recommendations.append("   - Review and optimize station dwell times at bottleneck stations")
            recommendations.append("   - Implement priority scheduling for premium trains")
            recommendations.append("   - Consider staggered scheduling to reduce bottleneck conflicts")

        if insights["weather_impact"] == "High":
            recommendations.append("[WEATHER] HIGH WEATHER IMPACT detected")
            recommendations.append("   - Reduce max speeds on steep climbs during monsoon")
            recommendations.append("   - Enhance drainage and maintenance on Lonavala-Junction_Z section")
            recommendations.append("   - Implement weather forecasting for dynamic scheduling")

        if insights["maintenance_impact"] == "High":
            recommendations.append("[MAINTENANCE] MAINTENANCE IMPACT significant")
            recommendations.append("   - Schedule maintenance outside peak traffic windows")
            recommendations.append("   - Avoid simultaneous maintenance on parallel sections")
            recommendations.append("   - Use night hours for non-critical maintenance")

        if insights["single_track_bottlenecks"] > 0:
            recommendations.append(f"[INFRASTRUCTURE] {insights['single_track_bottlenecks']} single track sections causing delays")
            recommendations.append("   - HIGHEST PRIORITY: Double Station_J to Lonavala_Hold_Point (steep climb section)")
            recommendations.append("   - HIGHEST PRIORITY: Double Lonavala_Hold_Point to Junction_Z (critical bridged section)")
            recommendations.append("   - MEDIUM PRIORITY: Expand H_Loop crossing capacity at Station_H")
            recommendations.append("   - Implement automatic block signaling on all single-track sections")

        if insights["premium_train_performance"] == "Needs Improvement":
            recommendations.append("[PREMIUM] PREMIUM SERVICES (Rajdhani/Shatabdi) need attention")
            recommendations.append("   - Guarantee dedicated priority paths through bottleneck sections")
            recommendations.append("   - Reduce express train stops at minor stations")
            recommendations.append("   - Implement express line fast-tracking")

        if metrics["average_delay_per_train"] > 15:
            recommendations.append("[DELAYS] HIGH AVERAGE DELAYS detected")
            recommendations.append("   - Deploy real-time train tracking and dynamic rescheduling")
            recommendations.append("   - Optimize signal spacing (reduce spacing at bottlenecks)")
            recommendations.append("   - Review and increase scheduled buffer times on bottleneck sections")

        return recommendations

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    def find_track(self, from_station: str, to_station: str):
        for track in self.tracks:
            if ((track["from"] == from_station and track["to"] == to_station) or
                    (track["from"] == to_station and track["to"] == from_station)):
                return track
        return None
