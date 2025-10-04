from ortools.sat.python import cp_model
import numpy as np

# Define your railway network (from previous JSON structure)
stations = ["CSMT", "DR", "TNA", "KYN", "KJT", "LNL", "PUNE"]
tracks = [
    {"from": "CSMT", "to": "DR", "length_km": 12, "tracks": 2, "min_travel_time": 10},
    {"from": "DR", "to": "TNA", "length_km": 18, "tracks": 2, "min_travel_time": 15},
    {"from": "TNA", "to": "KYN", "length_km": 15, "tracks": 2, "min_travel_time": 12},
    {"from": "KYN", "to": "KJT", "length_km": 25, "tracks": 2, "min_travel_time": 20},
    {"from": "KJT", "to": "LNL", "length_km": 32, "tracks": 1, "min_travel_time": 45},  # Single line bottleneck!
    {"from": "LNL", "to": "PUNE", "length_km": 66, "tracks": 2, "min_travel_time": 40}
]

# Train definitions with priorities (weights for delay minimization)
trains = [
    {"id": "T001", "type": "Express", "priority": 3.0, "route": ["CSMT", "DR", "TNA", "KYN", "KJT", "LNL", "PUNE"]},
    {"id": "T002", "type": "Passenger", "priority": 2.0, "route": ["CSMT", "DR", "TNA", "KYN", "KJT", "LNL", "PUNE"]},
    {"id": "T003", "type": "Freight", "priority": 1.0, "route": ["CSMT", "DR", "TNA", "KYN", "KJT", "LNL", "PUNE"]},
    {"id": "T004", "type": "Express", "priority": 3.0, "route": ["PUNE", "LNL", "KJT", "KYN", "TNA", "DR", "CSMT"]}
]

# Scheduled departure times (in minutes from start of day)
scheduled_departures = {
    "T001": 0,    # 8:00 AM
    "T002": 15,   # 8:15 AM  
    "T003": 30,   # 8:30 AM
    "T004": 0     # 8:00 AM from Pune
}


class RailwayScheduler:
    def __init__(self, stations, tracks, trains, scheduled_departures):
        self.model = cp_model.CpModel()
        self.stations = stations
        self.tracks = tracks
        self.trains = trains
        self.scheduled_departures = scheduled_departures
        
        # Decision variables
        self.departure_vars = {}    # departure_time[train][station]
        self.arrival_vars = {}      # arrival_time[train][station]
        self.travel_vars = {}       # travel_time[train][track]
        self.delay_vars = {}        # delay[train][station]
        
        # Track occupancy intervals (for no-overlap constraints)
        self.track_intervals = {}
        
    def create_variables(self):
        """Create all decision variables"""
        horizon = 24 * 60  # 24 hours in minutes
        
        for train in self.trains:
            train_id = train["id"]
            self.departure_vars[train_id] = {}
            self.arrival_vars[train_id] = {}
            self.delay_vars[train_id] = {}
            
            for station in train["route"]:
                # Departure time from each station
                self.departure_vars[train_id][station] = self.model.NewIntVar(
                    0, horizon, f'dep_{train_id}_{station}')
                
                # Arrival time at each station  
                self.arrival_vars[train_id][station] = self.model.NewIntVar(
                    0, horizon, f'arr_{train_id}_{station}')
                
                # Delay at each station (can be positive or negative)
                self.delay_vars[train_id][station] = self.model.NewIntVar(
                    -60, 120, f'delay_{train_id}_{station}')
    
    def add_travel_time_constraints(self):
        """Add minimum travel time constraints between stations"""
        for train in self.trains:
            train_id = train["id"]
            route = train["route"]
            
            for i in range(len(route) - 1):
                from_station = route[i]
                to_station = route[i + 1]
                
                # Find the track between these stations
                track = self.find_track(from_station, to_station)
                min_travel = track["min_travel_time"]
                
                # Arrival at next station >= Departure from current + min travel time
                self.model.Add(
                    self.arrival_vars[train_id][to_station] >= 
                    self.departure_vars[train_id][from_station] + min_travel
                )
                
                # Connect departure and arrival at same station
                if i > 0:  # Not the first station
                    self.model.Add(
                        self.departure_vars[train_id][from_station] >= 
                        self.arrival_vars[train_id][from_station]
                    )
    
    def add_single_track_constraints(self):
        """Add critical single-track constraints for the Bhor Ghats section"""
        single_track = self.find_track("KJT", "LNL")
        
        # Create interval variables for track occupancy
        for train in self.trains:
            train_id = train["id"]
            route = train["route"]
            
            for i in range(len(route) - 1):
                from_st, to_st = route[i], route[i + 1]
                track = self.find_track(from_st, to_st)
                
                if track["tracks"] == 1:  # Single track section
                    # Create interval variable representing track occupancy
                    interval_var = self.model.NewIntervalVar(
                        self.departure_vars[train_id][from_st],
                        track["min_travel_time"],  # Duration
                        self.arrival_vars[train_id][to_st],
                        f'interval_{train_id}_{from_st}_{to_st}'
                    )
                    
                    key = f"{from_st}_{to_st}"
                    if key not in self.track_intervals:
                        self.track_intervals[key] = []
                    self.track_intervals[key].append(interval_var)
        
        # Add no-overlap constraints for single tracks
        for track_key, intervals in self.track_intervals.items():
            self.model.AddNoOverlap(intervals)
    
    def add_delay_calculation(self):
        """Calculate delays based on scheduled vs actual times"""
        for train in self.trains:
            train_id = train["id"]
            first_station = train["route"][0]
            scheduled_dep = self.scheduled_departures[train_id]
            
            # Delay at first station = actual departure - scheduled departure
            self.model.Add(
                self.delay_vars[train_id][first_station] == 
                self.departure_vars[train_id][first_station] - scheduled_dep
            )
            
            # For other stations, delay = actual departure - (scheduled + accumulated delay)
            # This is simplified - you might want more sophisticated delay propagation
            for i, station in enumerate(train["route"][1:], 1):
                prev_station = train["route"][i-1]
                self.model.Add(
                    self.delay_vars[train_id][station] == 
                    self.departure_vars[train_id][station] - 
                    self.departure_vars[train_id][prev_station]
                )
    
    def set_weighted_delay_objective(self):
        """Set the objective: minimize total weighted delay"""
        delay_terms = []
        
        for train in self.trains:
            train_id = train["id"]
            priority_weight = train["priority"]
            
            # Sum of absolute delays at all stations for this train
            train_delay = sum(
                self.delay_vars[train_id][station] 
                for station in train["route"]
            )
            
            # Weight by train priority (Express = 3.0, Passenger = 2.0, Freight = 1.0)
            weighted_delay = train_delay * int(priority_weight * 100)  # Scale for integers
            
            delay_terms.append(weighted_delay)
        
        # Minimize total weighted delay
        total_weighted_delay = sum(delay_terms)
        self.model.Minimize(total_weighted_delay)
    
    def find_track(self, from_station, to_station):
        """Helper to find track between two stations"""
        for track in self.tracks:
            if (track["from"] == from_station and track["to"] == to_station) or \
               (track["from"] == to_station and track["to"] == from_station):
                return track
        return None
    
    def solve(self):
        """Solve the model and return solution"""
        solver = cp_model.CpSolver()
        
        # Set solver parameters
        solver.parameters.max_time_in_seconds = 300.0  # 5 minutes
        solver.parameters.num_search_workers = 8
        
        status = solver.Solve(self.model)
        
        solution = {
            'status': status,
            'solver': solver,
            'departures': {},
            'arrivals': {},
            'delays': {}
        }
        
        if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
            # Extract solution values
            for train in self.trains:
                train_id = train["id"]
                solution['departures'][train_id] = {}
                solution['arrivals'][train_id] = {}
                solution['delays'][train_id] = {}
                
                for station in train["route"]:
                    solution['departures'][train_id][station] = solver.Value(
                        self.departure_vars[train_id][station])
                    solution['arrivals'][train_id][station] = solver.Value(
                        self.arrival_vars[train_id][station])
                    solution['delays'][train_id][station] = solver.Value(
                        self.delay_vars[train_id][station])
        
        return solution

    def print_solution(self, solution):
        """Print the solution in a readable format"""
        if solution['status'] not in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
            print("No solution found!")
            return
        
        solver = solution['solver']
        print(f"Solution status: {solver.StatusName(solution['status'])}")
        print(f"Objective value: {solver.ObjectiveValue()}")
        print(f"Wall time: {solver.WallTime():.2f} seconds")
        print()
        
        for train in self.trains:
            train_id = train["id"]
            print(f"=== {train_id} ({train['type']}, Priority: {train['priority']}) ===")
            
            for station in train["route"]:
                dep_time = solution['departures'][train_id][station]
                arr_time = solution['arrivals'][train_id][station] 
                delay = solution['delays'][train_id][station]
                
                print(f"  {station:4s} | Dep: {dep_time:4d} | Arr: {arr_time:4d} | Delay: {delay:3d} min")
            print()


# Initialize and run the scheduler
def main():
    scheduler = RailwayScheduler(stations, tracks, trains, scheduled_departures)
    
    print("Building CP-SAT model...")
    scheduler.create_variables()
    scheduler.add_travel_time_constraints()
    scheduler.add_single_track_constraints()
    scheduler.add_delay_calculation()
    scheduler.set_weighted_delay_objective()
    
    print("Solving...")
    solution = scheduler.solve()
    
    print("Solution:")
    scheduler.print_solution(solution)
    
    # Calculate total weighted delay
    total_weighted_delay = 0
    for train in trains:
        train_id = train["id"]
        priority = train["priority"]
        total_delay = sum(solution['delays'][train_id].values())
        weighted_delay = total_delay * priority
        total_weighted_delay += weighted_delay
        print(f"{train_id}: Total delay = {total_delay} × Priority {priority} = {weighted_delay}")
    
    print(f"\nTotal Weighted Delay: {total_weighted_delay}")

if __name__ == "__main__":
    main()



#Advanced Features Used:

# For handling disruptions
def add_disruption_constraints(self, disrupted_track, disruption_start, disruption_end):
    """Add constraints for track disruptions"""
    for train in self.trains:
        train_id = train["id"]
        route = train["route"]
        
        for i in range(len(route) - 1):
            from_st, to_st = route[i], route[i+1]
            track = self.find_track(from_st, to_st)
            
            if track == disrupted_track:
                # Train cannot use this track during disruption
                self.model.Add(
                    self.arrival_vars[train_id][to_st] <= disruption_start
                ).OnlyEnforceIf(
                    self.departure_vars[train_id][from_st] <= disruption_start
                )
                self.model.Add(
                    self.departure_vars[train_id][from_st] >= disruption_end  
                ).OnlyEnforceIf(
                    self.departure_vars[train_id][from_st] >= disruption_start
                )

# For platform assignment at stations
def add_platform_constraints(self):
    """Add platform occupancy constraints at major stations"""
    platform_capacities = {"CSMT": 8, "PUNE": 6, "KYN": 10}
    
    for station, capacity in platform_capacities.items():
        station_intervals = []
        
        for train in self.trains:
            if station in train["route"]:
                # Assume 10-minute platform occupancy
                platform_interval = self.model.NewIntervalVar(
                    self.arrival_vars[train["id"]][station],
                    10,  # Platform occupancy time
                    self.departure_vars[train["id"]][station],
                    f'platform_{train["id"]}_{station}'
                )
                station_intervals.append(platform_interval)
        
        # No more than 'capacity' trains at the station simultaneously
        self.model.AddCumulative(station_intervals, [1] * len(station_intervals), capacity)