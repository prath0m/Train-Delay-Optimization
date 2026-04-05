import json
import sys
import os
from datetime import datetime

from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

# Ensure optimizer modules on path (same directory as manage.py)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)


def index(request):
    return render(request, 'index.html')


@csrf_exempt
@require_http_methods(["POST"])
def run_optimization(request):
    try:
        data = json.loads(request.body)

        delay_factor = float(data.get('delay_factor', 1.0))
        delay_factor = max(0.0, min(delay_factor, 2.0))

        scenario_choice = int(data.get('scenario', 1))
        maintenance_preset = int(data.get('maintenance_preset', 5))
        maintenance_preset = max(0, min(maintenance_preset, 6))

        scenarios = {
            1: datetime(2024, 7, 15),
            2: datetime(2024, 1, 15),
            3: datetime(2024, 4, 15),
            4: datetime(2024, 10, 15),
        }
        scenario_date = scenarios.get(scenario_choice, scenarios[1])

        from optimizer import EnhancedIndianRailwayOptimizer
        from config import MAINTENANCE_PRESETS

        optimizer = EnhancedIndianRailwayOptimizer(
            scenario_date=scenario_date,
            custom_delay_factor=delay_factor,
            maintenance_preset=maintenance_preset,
        )

        solution = optimizer.solve_optimization()

        if solution.get('error'):
            return JsonResponse({'error': solution['error']}, status=500)

        metrics = solution.get('performance_metrics', {})
        insights = solution.get('operational_insights', {})
        recommendations = solution.get('recommendations', [])
        train_schedules = solution.get('train_schedules', {})
        interactions = solution.get('train_interactions', {})

        # Build per-train summary
        trains_data = []
        for train in sorted(optimizer.trains, key=lambda t: t['priority'], reverse=True):
            tid = train['id']
            td = train_schedules.get(tid, {})
            schedule = td.get('schedule', {})
            delays = td.get('delays', {})

            stops = []
            for station in train['route']:
                sched = schedule.get(station, {})
                delay_info = delays.get(station, {})
                total_delay = sum(delay_info.values())
                stops.append({
                    'station': station.replace('_', ' '),
                    'arrival': sched.get('arrival', '--:--'),
                    'departure': sched.get('departure', '--:--'),
                    'dwell': sched.get('dwell_minutes', 0),
                    'total_delay': total_delay,
                    'delay_breakdown': {k: v for k, v in delay_info.items() if v > 0},
                })

            total_train_delay = td.get('total_delay', 0)
            if total_train_delay == 0:
                status = 'on_time'
            elif total_train_delay <= 5:
                status = 'minor'
            elif total_train_delay <= 15:
                status = 'delayed'
            else:
                status = 'late'

            trains_data.append({
                'id': tid,
                'name': tid.replace('_', ' '),
                'type': td.get('type', ''),
                'priority': td.get('priority', 0),
                'total_delay': total_train_delay,
                'status': status,
                'stops': stops,
            })

        # Maintenance info
        maint_blocks = optimizer._get_maintenance_blocks()
        preset_info = MAINTENANCE_PRESETS.get(maintenance_preset, MAINTENANCE_PRESETS[0])
        maintenance_info = {
            'name': preset_info['name'],
            'description': preset_info['description'],
            'blocks': [
                {
                    'section': b['section'].replace('_', ' '),
                    'type': b['type'].replace('_', ' ').title(),
                    'start': f"{b['start_time']//60:02d}:{b['start_time']%60:02d}",
                    'end': f"{b['end_time']//60:02d}:{b['end_time']%60:02d}",
                    'delay_minutes': b.get('delay_minutes', 0),
                }
                for b in maint_blocks
            ],
        }

        # Bottleneck delays
        bottleneck_delays = insights.get('bottleneck_delays', {})
        bottlenecks = [
            {
                'section': k.replace('_', ' '),
                'delay': v,
                'severity': 'critical' if v > 20 else 'high' if v > 10 else 'moderate' if v > 5 else 'low',
            }
            for k, v in sorted(bottleneck_delays.items(), key=lambda x: x[1], reverse=True)
        ]

        result = {
            'status': solution.get('status', 'unknown'),
            'solve_time': round(solution.get('solve_time', 0), 2),
            'scenario': {
                'date': scenario_date.strftime('%B %d, %Y'),
                'season': optimizer._get_weather_scenario().get('season', 'normal').title(),
                'delay_factor': delay_factor,
            },
            'metrics': {
                'total_delay': metrics.get('total_system_delay_minutes', 0),
                'avg_delay': round(metrics.get('average_delay_per_train', 0), 1),
                'punctuality': round(metrics.get('punctuality_percentage', 0), 1),
                'on_time_trains': metrics.get('on_time_trains', 0),
                'total_trains': metrics.get('total_trains', 0),
            },
            'insights': {
                'weather_impact': insights.get('weather_impact', 'N/A'),
                'maintenance_impact': insights.get('maintenance_impact', 'N/A'),
                'bottlenecks': insights.get('single_track_bottlenecks', 0),
                'critical_bottlenecks': insights.get('critical_bottlenecks', 0),
                'premium_performance': insights.get('premium_train_performance', 'N/A'),
                'max_bottleneck_delay': insights.get('max_bottleneck_delay', 0),
            },
            'bottlenecks': bottlenecks,
            'trains': trains_data,
            'maintenance': maintenance_info,
            'recommendations': recommendations,
            'interactions': {
                'overtaking': interactions.get('overtaking_events', []),
                'waiting': interactions.get('waiting_events', [])[:5],
                'single_track': interactions.get('single_track_conflicts', []),
            },
        }

        return JsonResponse(result)

    except Exception as e:
        import traceback
        return JsonResponse({'error': str(e), 'traceback': traceback.format_exc()}, status=500)
