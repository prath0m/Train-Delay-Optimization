import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from typing import Dict, Optional


TRAIN_TYPE_COLORS = {
    'superfast': '#e74c3c',
    'express': '#3498db',
    'mail_express': '#9b59b6',
    'passenger': '#2ecc71',
    'freight': '#f39c12',
    'goods': '#95a5a6'
}


def plot_train_timeline(optimizer, solution: Dict, save_path: Optional[str] = None):
    """Generate a visual timeline chart of train movements."""
    if solution.get("error"):
        print(f"ERROR: {solution['error']}")
        return

    fig, ax = plt.subplots(figsize=(14, 8))

    sorted_trains = sorted(optimizer.trains, key=lambda t: t['priority'], reverse=True)
    train_names = [t['id'].replace('_', ' ')[:25] for t in sorted_trains]
    y_positions = range(len(sorted_trains))

    for y_pos, train in zip(y_positions, sorted_trains):
        train_id = train['id']
        train_data = solution["train_schedules"][train_id]
        color = TRAIN_TYPE_COLORS.get(train_data['type'], '#7f8c8d')

        schedule = train_data['schedule']
        route = train['route']

        try:
            prev_dep_minutes = None

            for station in route:
                if station not in schedule:
                    continue

                arr_str = schedule[station]['arrival']
                dep_str = schedule[station]['departure']

                arr_min = int(arr_str.split(':')[0]) * 60 + int(arr_str.split(':')[1])
                dep_min = int(dep_str.split(':')[0]) * 60 + int(dep_str.split(':')[1])

                if prev_dep_minutes is not None and arr_min < prev_dep_minutes:
                    arr_min += 24 * 60
                if dep_min < arr_min:
                    dep_min += 24 * 60

                if prev_dep_minutes is not None:
                    travel_len = arr_min - prev_dep_minutes
                    if travel_len > 0:
                        ax.barh(y_pos, travel_len, left=prev_dep_minutes, height=0.5,
                                color=color, alpha=0.75, edgecolor='black', linewidth=0.5)

                dwell = schedule[station]['dwell_minutes']
                if dwell > 0:
                    ax.barh(y_pos, dwell, left=arr_min, height=0.75,
                            color=color, alpha=1.0, edgecolor='black', linewidth=1.0)

                station_delay = sum(train_data['delays'].get(station, {}).values())
                if station_delay > 0:
                    delay_color = '#e74c3c' if station_delay > 15 else '#f39c12' if station_delay > 5 else '#27ae60'
                    ax.plot(arr_min, y_pos + 0.45, 'v', color=delay_color,
                            markersize=5, zorder=5, clip_on=False)

                prev_dep_minutes = dep_min

            delay = train_data['total_delay']
            if delay > 0 and prev_dep_minutes is not None:
                delay_color = '#e74c3c' if delay > 15 else '#f39c12' if delay > 5 else '#27ae60'
                ax.text(prev_dep_minutes + 5, y_pos, f"+{delay}m",
                        va='center', ha='left', fontsize=8, color=delay_color, fontweight='bold')

        except (KeyError, ValueError):
            continue

    ax.set_yticks(y_positions)
    ax.set_yticklabels(train_names, fontsize=9)
    ax.set_xlabel('Time (minutes from midnight)', fontsize=10)
    ax.set_title(
        f'Train Schedule Timeline - {optimizer.scenario_date.strftime("%B %d, %Y")}\n'
        f'Punctuality: {solution["performance_metrics"]["punctuality_percentage"]:.1f}%',
        fontsize=12, fontweight='bold'
    )

    ax.set_xlim(0, 24 * 60)
    hour_ticks = [h * 60 for h in range(0, 25, 2)]
    hour_labels = [f'{h:02d}:00' for h in range(0, 25, 2)]
    ax.set_xticks(hour_ticks)
    ax.set_xticklabels(hour_labels, fontsize=8, rotation=45)

    ax.grid(axis='x', alpha=0.3, linestyle='--')
    ax.set_axisbelow(True)

    legend_patches = [
        mpatches.Patch(color=c, label=t.replace('_', ' ').title())
        for t, c in TRAIN_TYPE_COLORS.items()
    ]
    ax.legend(handles=legend_patches, loc='upper right', fontsize=8, title='Train Type')

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"\nTimeline chart saved to: {save_path}")

    plt.show()
    return fig
