import json
from datetime import datetime

from config import MAINTENANCE_PRESETS
from optimizer import EnhancedIndianRailwayOptimizer
from reporting import print_comprehensive_results, print_simple_summary
from visualization import plot_train_timeline


def main():
    print("\n" + "=" * 80)
    print("Enhanced Indian Railway Train Delay Optimization System")
    print("Comprehensive modeling of weather, maintenance, and operational factors")
    print("=" * 80)

    # --- Delay factor ---
    print("\nCUSTOM DELAY CONFIGURATION")
    print("Enter delay factor (0.0 to 2.0):")
    print("  - 0.0 = No delays (ideal conditions)")
    print("  - 0.5 = Moderate delays")
    print("  - 1.0 = Normal delays (default)")
    print("  - 1.5 = High delays")

    try:
        delay_input = input("\nDelay Factor [default: 1.0]: ").strip()
        custom_delay_factor = float(delay_input) if delay_input else 1.0
        custom_delay_factor = max(0.0, min(custom_delay_factor, 2.0))
    except ValueError:
        print("WARNING: Invalid input, using default factor: 1.0")
        custom_delay_factor = 1.0

    print(f"\nUsing delay factor: {custom_delay_factor}")

    # --- Scenario ---
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
        1: datetime(2024, 7, 15),
        2: datetime(2024, 1, 15),
        3: datetime(2024, 4, 15),
        4: datetime(2024, 10, 15)
    }

    scenario_date = scenarios.get(scenario_choice, scenarios[1])
    print(f"\nSelected Scenario: {scenario_date.strftime('%B %d, %Y')}")
    print(f"Delay Multiplier: {custom_delay_factor}x")

    # --- Maintenance ---
    print("\n" + "=" * 80)
    print("MAINTENANCE BLOCK CONFIGURATION")
    print("=" * 80)
    print("\nSelect maintenance block option:")
    print("  0. No Maintenance (all tracks operational)")
    print("  1. Light Maintenance (Night) - Minor track inspection")
    print("  2. Track Renewal (Station A - Station J)")
    print("  3. Signaling Maintenance (Junction X - Station G)")
    print("  4. Bottleneck Section Maintenance (Lonavala steep climb)")
    print("  5. Multiple Blocks (Heavy Maintenance) [default]")
    print("  6. Full Day Block (Emergency Repair on main line)")

    try:
        maint_input = input("\nSelect maintenance [0-6, default: 5]: ").strip().lower()

        if maint_input in ["no", "n", "none"]:
            maintenance_preset = 0
            print("\nAll maintenance blocks REMOVED - tracks fully operational")
        elif maint_input == "":
            maintenance_preset = 5
        else:
            maintenance_preset = int(maint_input)
            maintenance_preset = max(0, min(maintenance_preset, 6))
    except ValueError:
        print("WARNING: Invalid input, using default (Multiple Blocks)")
        maintenance_preset = 5

    preset_info = MAINTENANCE_PRESETS.get(maintenance_preset, MAINTENANCE_PRESETS[5])
    print(f"\nSelected: {preset_info['name']}")
    print(f"  {preset_info['description']}")
    if preset_info['blocks']:
        print("  Affected sections:")
        for block in preset_info['blocks']:
            time_start = f"{block['start_time']//60:02d}:{block['start_time']%60:02d}"
            time_end = f"{block['end_time']//60:02d}:{block['end_time']%60:02d}"
            print(f"    - {block['section'].replace('_', ' ')} ({time_start} - {time_end})")

    print("=" * 80)

    # --- Output format ---
    print("\nSELECT OUTPUT FORMAT:")
    print("  1. Simple Summary Table (recommended)")
    print("  2. Visual Timeline Chart")
    print("  3. Both (Summary + Chart)")
    print("  4. Full Detailed Report")

    try:
        output_choice = input("\nSelect output [1-4, default: 1]: ").strip()
        output_choice = int(output_choice) if output_choice else 1
    except ValueError:
        output_choice = 1

    # --- Run ---
    optimizer = EnhancedIndianRailwayOptimizer(
        scenario_date=scenario_date,
        custom_delay_factor=custom_delay_factor,
        maintenance_preset=maintenance_preset
    )

    solution = optimizer.solve_optimization()

    if output_choice == 1:
        print_simple_summary(optimizer, solution)
    elif output_choice == 2:
        plot_train_timeline(optimizer, solution, save_path="train_timeline.png")
    elif output_choice == 3:
        print_simple_summary(optimizer, solution)
        plot_train_timeline(optimizer, solution, save_path="train_timeline.png")
    else:
        print_comprehensive_results(optimizer, solution)

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
