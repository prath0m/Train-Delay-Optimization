from typing import Dict


def print_comprehensive_results(optimizer, solution: Dict):
    print("\n" + "=" * 80)
    print("COMPREHENSIVE INDIAN RAILWAY OPTIMIZATION RESULTS")
    print("=" * 80)

    if solution.get("error"):
        print(f"ERROR: {solution['error']}")
        return

    print(f"\nSolution Status: {solution['status']}")
    print(f"Objective Value: {solution['objective_value']}")
    print(f"Solve Time: {solution['solve_time']:.2f} seconds")

    metrics = solution["performance_metrics"]
    print(f"\nSYSTEM PERFORMANCE METRICS")
    print(f"   Total System Delay: {metrics['total_system_delay_minutes']} minutes")
    print(f"   Average Delay per Train: {metrics['average_delay_per_train']:.1f} minutes")
    print(f"   Punctuality Rate: {metrics['punctuality_percentage']:.1f}% ({metrics['on_time_trains']}/{metrics['total_trains']} trains)")

    insights = solution["operational_insights"]
    print(f"\nOPERATIONAL ANALYSIS")
    print(f"   Weather Impact: {insights['weather_impact']}")
    print(f"   Maintenance Impact: {insights['maintenance_impact']}")
    print(f"   Single Track Bottlenecks: {insights['single_track_bottlenecks']} sections")
    print(f"   Critical Bottlenecks: {insights.get('critical_bottlenecks', 0)} sections")
    print(f"   Premium Train Performance: {insights['premium_train_performance']}")

    if insights.get('bottleneck_delays'):
        print(f"\nBOTTLENECK DELAY ANALYSIS")
        bottleneck_delays = insights['bottleneck_delays']
        max_delay = insights.get('max_bottleneck_delay', 0)
        print(f"   Maximum Bottleneck Delay: {max_delay} minutes")

        for section, delay in sorted(bottleneck_delays.items(), key=lambda x: x[1], reverse=True):
            status = "CRITICAL" if delay > 20 else "HIGH" if delay > 10 else "MODERATE" if delay > 5 else "LOW"
            print(f"   {section}: {delay} min [{status}]")

    print(f"\nOPTIMIZED TRAIN SCHEDULES")
    print("-" * 80)

    for train in optimizer.trains:
        train_id = train["id"]
        train_data = solution["train_schedules"][train_id]

        print(f"\n{'=' * 80}")
        print(f"TRAIN: {train_id}")
        print(f"   Type: {train_data['type'].title()} | Priority: {train_data['priority']} | Total Delay: {train_data['total_delay']} min")
        print(f"{'=' * 80}")

        interactions = solution.get("train_interactions", {})
        overtaking_at_stations = {}
        waiting_at_stations = {}

        for event in interactions.get("overtaking_events", []):
            station = event["station"]
            overtaking_at_stations.setdefault(station, []).append(event)

        for event in interactions.get("waiting_events", []):
            if event["waiting_train"] == train_id:
                waiting_at_stations.setdefault(event["station"], []).append(event)

        for idx, station in enumerate(train["route"]):
            schedule = train_data["schedule"][station]
            delays = train_data["delays"][station]

            total_station_delay = sum(delays.values())
            min_dwell = optimizer._get_minimum_dwell_time(train, station) if station in optimizer.station_config else 0
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

                track = optimizer.find_track(station, next_station)
                base_time = track["min_travel_time"] if track else 0
                extra_time = travel_time - base_time

                print(f"      -> {next_station}: {travel_time} min (Base: {base_time} min, Extra: {extra_time} min)")

    interactions = solution.get("train_interactions", {})
    if any(interactions.values()):
        print(f"\nTRAIN INTERACTIONS & PRIORITY EVENTS")
        print("-" * 80)

        overtaking_events = interactions.get("overtaking_events", [])
        if overtaking_events:
            print(f"\nOVERTAKING EVENTS ({len(overtaking_events)}):")
            for event in overtaking_events:
                print(f"  Location: {event['station']} @ {event['time']}")
                print(f"     Stopped: {event['stopped_train']} ({event['stopped_train_type']}, Priority: {event['stopped_train_priority']})")
                print(f"     Overtook: {event['overtaking_train']} ({event['overtaking_train_type']}, Priority: {event['overtaking_train_priority']})")
                print(f"     Wait time: {event['wait_time_minutes']} minutes")
                print()

        waiting_events = interactions.get("waiting_events", [])
        if waiting_events:
            print(f"\nEXTENDED WAITING EVENTS ({len(waiting_events)}):")
            for event in waiting_events[:5]:
                print(f"  Location: {event['station']} @ {event['time']}")
                print(f"     Train: {event['waiting_train']} ({event['waiting_train_type']})")
                print(f"     Extra wait: {event['extra_wait_minutes']} minutes")
                print(f"     Possibly waiting for: {event['possibly_waiting_for']}")
                print()

        single_track_conflicts = interactions.get("single_track_conflicts", [])
        if single_track_conflicts:
            print(f"\nSINGLE TRACK SEQUENCING ({len(single_track_conflicts)}):")
            for event in single_track_conflicts:
                print(f"  Section: {event['section']}")
                print(f"     Waited: {event['waited_train']} waited for")
                print(f"     Priority: {event['priority_train']} (higher priority)")
                print(f"     Time: {event['wait_started']} -> {event['wait_ended']}")
                print()

    print(f"\nOPERATIONAL RECOMMENDATIONS")
    print("-" * 80)
    for recommendation in solution["recommendations"]:
        print(recommendation)

    print("\n" + "=" * 80)


def print_simple_summary(optimizer, solution: Dict):
    if solution.get("error"):
        print(f"ERROR: {solution['error']}")
        return

    metrics = solution["performance_metrics"]
    weather = optimizer._get_weather_scenario()
    season = weather.get('season', 'normal').title()

    print("\n" + "=" * 70)
    print("            TRAIN DELAY OPTIMIZATION - SUMMARY")
    print("=" * 70)
    print(f"  Scenario: {optimizer.scenario_date.strftime('%B %d, %Y')} | Weather: {season}")
    print(f"  Punctuality: {metrics['punctuality_percentage']:.1f}% | Avg Delay: {metrics['average_delay_per_train']:.1f} min")
    print("=" * 70)

    print(f"\n{'Train Name':<30} {'Type':<12} {'Priority':<8} {'Delay':<10} {'Status':<10}")
    print("-" * 70)

    sorted_trains = sorted(optimizer.trains, key=lambda t: t['priority'], reverse=True)

    for train in sorted_trains:
        train_id = train["id"]
        train_data = solution["train_schedules"][train_id]

        name = train_id.replace("_", " ")
        if len(name) > 28:
            name = name[:25] + "..."

        train_type = train_data['type'].title()
        priority = train_data['priority']
        delay = train_data['total_delay']

        if delay == 0:
            status = "On Time"
        elif delay <= 5:
            status = "Minor"
        elif delay <= 15:
            status = "Delayed"
        else:
            status = "Late"

        print(f"{name:<30} {train_type:<12} {priority:<8} {delay:>3} min    {status:<10}")

    print("-" * 70)
    print(f"{'TOTAL':<52} {metrics['total_system_delay_minutes']:>3} min")
    print("=" * 70)

    insights = solution["operational_insights"]
    print(f"\nKey Insights:")
    print(f"   - Weather Impact: {insights['weather_impact']}")
    print(f"   - Bottleneck Sections: {insights['single_track_bottlenecks']}")
    print(f"   - Premium Train Status: {insights['premium_train_performance']}")

    maint_blocks = optimizer._get_maintenance_blocks()
    if maint_blocks:
        print(f"\nActive Maintenance Blocks ({len(maint_blocks)}):")
        for block in maint_blocks:
            time_start = f"{block['start_time']//60:02d}:{block['start_time']%60:02d}"
            time_end = f"{block['end_time']//60:02d}:{block['end_time']%60:02d}"
            section_name = block['section'].replace('_', ' ')
            print(f"   - {section_name}: {block['type'].replace('_', ' ').title()} ({time_start}-{time_end})")
    else:
        print(f"\nMaintenance: None (all tracks operational)")
