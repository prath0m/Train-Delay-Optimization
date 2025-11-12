# 🚂 Enhanced Indian Railway Train Delay Optimization System

## 📁 Project Structure

```
Train delay optimization/
├── .venv/                              # Python virtual environment
├── complete_enhanced_system.py        # Main enhanced optimization system
├── railway_config.py                  # Configuration parameters
├── ENHANCEMENT_SUMMARY.md             # Detailed documentation
├── optimization_results_*.json        # Generated results
└── README.md                          # This file
```

## 🚀 How to Run the System

### **Step 1: Navigate to Project Directory**
```bash
cd "/Users/prathameshkale/Documents/Train delay optimization"
```

### **Step 2: Install Dependencies (First Time Only)**
```bash
./venv/bin/pip install -r requirements.txt
```

### **Step 3: Run the Optimization System**
```bash
./venv/bin/python complete_enhanced_system.py
```

The system will prompt you for:
1. **Delay Factor** (0.0 to 2.0): Controls how much weather/maintenance impacts trains
   - `0.0` = No delays (ideal conditions)
   - `0.5` = 50% reduced delays
   - `1.0` = Normal delays (default)
2. **Scenario Selection** (1-4): Choose the weather season
   - `1` = Monsoon Season (July)
   - `2` = Winter Fog Season (January)
   - `3` = Summer Heat Season (April)
   - `4` = Normal Season (October)

### **Step 3: View Results**
The system will:
- Display comprehensive optimization results on screen
- Generate JSON results file: `optimization_results_YYYY_MM_DD_delay_X.X.json`
- Show train-by-train schedules with delay breakdowns
- Provide operational recommendations

## 🎯 Quick Test Examples

### **Example 1: Test with No Delays (Ideal Conditions)**
```bash
cd "/Users/prathameshkale/Documents/Train delay optimization"
echo -e "0.0\n1" | ./venv/bin/python complete_enhanced_system.py
```

### **Example 2: Test with 30% Delays (Monsoon)**
```bash
cd "/Users/prathameshkale/Documents/Train delay optimization"
echo -e "0.3\n1" | ./venv/bin/python complete_enhanced_system.py
```

### **Example 3: Test with Normal Delays (Winter Fog)**
```bash
cd "/Users/prathameshkale/Documents/Train delay optimization"
echo -e "1.0\n2" | ./venv/bin/python complete_enhanced_system.py
```

### **Example 4: Test with Double Delays (Severe Monsoon)**
```bash
cd "/Users/prathameshkale/Documents/Train delay optimization"
echo -e "2.0\n1" | ./venv/bin/python complete_enhanced_system.py
```

## 📊 Expected Output

The system will display:

```
🚂 Enhanced Indian Railway Train Delay Optimization System
   Comprehensive modeling of weather, maintenance, and operational factors
================================================================================

⚙️  CUSTOM DELAY CONFIGURATION
Enter delay factor (0.0 to 2.0):
  • 0.0 = No delays (ideal conditions)
  • 0.5 = 50% reduced delays
  • 1.0 = Normal delays (default)
  • 1.5 = 50% increased delays
  • 2.0 = Double delays (severe conditions)

Delay Factor [default: 1.0]: 0.3

✅ Using delay factor: 0.3

📅 SELECT SCENARIO:
  1. Monsoon Season (July)
  2. Winter Fog Season (January)
  3. Summer Heat Season (April)
  4. Normal Season (October)

Select scenario [1-4, default: 1]: 1

🗓️  Selected Scenario: July 15, 2024
🎚️  Delay Multiplier: 0.3x
================================================================================
🚂 Enhanced Indian Railway Delay Optimization
📅 Scenario Date: July 15, 2024
🌦️  Weather Season: Monsoon
🔧 Maintenance Blocks: 2
============================================================
Building comprehensive optimization model...
   ✅ Variables initialized
   ✅ Basic operational constraints
   ✅ Weather impact constraints
   ✅ Maintenance constraints
   ✅ Single track constraints
   ✅ Priority and overtaking rules
   ✅ Platform capacity constraints
   ✅ Freight movement restrictions
   ✅ Multi-objective function set

Solving optimization problem...

================================================================================
🚂 COMPREHENSIVE INDIAN RAILWAY OPTIMIZATION RESULTS
================================================================================
✅ Solution Status: OPTIMAL
🎯 Objective Value: -7690.0
⏱️  Solve Time: 0.01 seconds

📊 SYSTEM PERFORMANCE METRICS
   Total System Delay: 0 minutes
   Average Delay per Train: 0.0 minutes
   Punctuality Rate: 100.0% (8/8 trains)

🌦️  OPERATIONAL ANALYSIS
   Weather Impact: Low
   Maintenance Impact: Low
   Single Track Bottlenecks: 3 sections
   Premium Train Performance: Good

🚂 OPTIMIZED TRAIN SCHEDULES
--------------------------------------------------------------------------------
12301_Howrah_Rajdhani
Type: Superfast, Priority: 5.0, Total Delay: 0 min
  Station_C                 | Arr: 00:00 | Dep: 06:00 | Dwell:  0min | Delay:   0min 🟢
  Station_A                 | Arr: 06:45 | Dep: 07:45 | Dwell: 60min | Delay:   0min 🟢
  [... more stations ...]

💡 OPERATIONAL RECOMMENDATIONS
--------------------------------------------------------------------------------
🚧 BOTTLENECK: 3 single track sections
   • Priority: Double tracking of Lonavala-Junction_Z section
   • Add additional crossing loops
   • Implement automatic block signaling

📁 Results exported to 'optimization_results_2024_07_15_delay_0.3.json'
```

## ⚙️ Customization Options

### **Adjust Delay Factor**
The system now supports a custom delay factor (0.0 to 2.0) that scales all weather and maintenance delays:
- **0.0**: Ideal conditions, no weather/maintenance impacts
- **0.5**: Reduced impact (50% of normal)
- **1.0**: Normal conditions (default)
- **1.5**: Increased impact (50% more than normal)
- **2.0**: Severe conditions (double impact)

### **Change Weather Scenario**
Select from 4 seasonal scenarios when running:
1. **Monsoon (July)**: Heavy rain impacts on steep sections
2. **Winter (January)**: Fog restrictions on flat sections
3. **Summer (April)**: Heat-related track expansion effects
4. **Normal (October)**: Clear weather conditions

### **Modify Train Fleet**
Edit the `self.trains` list in `complete_enhanced_system.py` around line ~75 to add/remove trains.

### **Update Station Configuration**
Modify the `self.station_config` dictionary around line ~130 to change platform counts, facilities, etc.

### **Adjust Weather Impact Parameters**
Edit the `_get_weather_scenario()` method around line ~162 to change:
- Speed reduction percentages
- Additional time delays
- Affected track sections

## 🔧 System Requirements

- **Python**: 3.7+ (currently using 3.13.7)
- **Required Packages**: 
  - `ortools` (Google OR-Tools for optimization)
  - `numpy` (numerical computations)
- **Virtual Environment**: Already configured in `.venv/`

## 📈 Key Features Included

✅ **Weather Impact Modeling**
- Monsoon delays (heavy rain)
- Winter fog restrictions  
- Summer heat effects

✅ **Maintenance Integration**
- Scheduled track work
- Speed restrictions
- Construction blocks

✅ **Indian Railway Rules**
- Train priority system
- Single track protocols
- Freight restrictions

✅ **Advanced Constraints**
- Platform capacity limits
- Crew duty hours
- Crossing loop management

✅ **Multi-Objective Optimization**
- Minimize delays
- Maximize punctuality
- Optimize resource usage

## 🆘 Troubleshooting

### **Issue: "No module named 'ortools'"**
```bash
# Install required packages from requirements.txt
./venv/bin/pip install -r requirements.txt
```

### **Issue: "zsh: command not found: python"**
```bash
# Use the virtual environment's Python directly
./venv/bin/python complete_enhanced_system.py
```

### **Issue: "No feasible solution found"**
This can happen when delay factors are too high (> 0.5) and create conflicting constraints. Try:
- Reducing the delay factor (use 0.0 to 0.5 range)
- Selecting a different season scenario
- The system works best with delay factors ≤ 0.3

### **Issue: Virtual environment not found**
```bash
# Recreate virtual environment
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
```

### **Issue: Permission denied**
```bash
# Make script executable
chmod +x complete_enhanced_system.py
```

### **Issue: Output shows "all delay 0 min"**
- If using delay factor 0.0, this is expected (ideal conditions)
- For higher factors, check that you selected a scenario with weather impacts (option 1-3, not 4)

## 📞 Support

If you encounter any issues:

1. Check that the virtual environment is activated
2. Ensure required packages are installed: `pip list`
3. Verify Python version: `python --version`
4. Check file permissions: `ls -la`

## 🎯 Next Steps

1. **Run the basic system** with default settings
2. **Experiment with different seasons** by changing the date
3. **Add your own trains** to the fleet configuration
4. **Modify station characteristics** based on your network
5. **Integrate real-time data** for live optimization

---

**Ready to optimize your railway network! 🚂✨**