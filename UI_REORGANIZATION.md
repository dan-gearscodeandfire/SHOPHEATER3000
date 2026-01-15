# UI Reorganization and Data Management System

**Date:** January 14, 2026  
**Status:** ✅ COMPLETED AND TESTED

## Overview

This document describes the major reorganization of the Shop Heater Web UI and the implementation of a comprehensive data management system. The changes make the UI cleaner, more organized, and add powerful data logging, graphing, and analysis capabilities.

---

## Phase 1: Separate Controls Page

### Problem
The main dashboard was becoming cluttered with both monitoring displays and control inputs, making it harder to quickly view system status.

### Solution
Created a dedicated `/controls` page with all system controls moved from the main dashboard:

- **New File:** `controls.html`
- **Controls Moved:**
  - Control Mode (Manual/Automatic) toggle
  - Main Loop Solenoid toggle
  - Diversion Solenoid toggle
  - Fan Speed controls (input + slider)
  - Data Logging toggle
  - Live Graphing toggle

### Benefits
- Main dashboard is now monitoring-only (cleaner, faster to read)
- Controls page provides focused interaction space
- Separation of concerns (viewing vs controlling)
- Reduced visual clutter

---

## Phase 2: Navigation System

### Implementation
Added consistent navigation links across all pages:

- **Dashboard** (`/`) - Monitoring only
- **Controls** (`/controls`) - System controls
- **Live Graph** (`/graph`) - Real-time graphing
- **Data Explorer** (`/explorer`) - Browse historical sessions

### Visual Design
- Navigation links displayed at top of every page
- Active page highlighted in green
- Hover effects for better UX
- Responsive layout

---

## Phase 3: Organized Data Storage

### Directory Structure
```
SHOPHEATER3000/
├── data_logs/              # CSV session logs
│   ├── .gitkeep
│   └── session_YYYY-MM-DD_HH-MM-SS.csv
├── graph_sessions/         # JSON graph sessions
│   ├── .gitkeep
│   └── graph_YYYY-MM-DD_HH-MM-SS.json
```

### Data Logging (CSV)
**Trigger:** Data Logging toggle ON  
**Collection:** Every 5 seconds  
**Save:** When toggle turned OFF or server shutdown  
**Filename:** `session_YYYY-MM-DD_HH-MM-SS.csv` (timestamp from START)

**CSV Contents:**
- timestamp
- All temperatures (water_hot, water_reservoir, water_mix, water_cold, air_cool, air_heated)
- All deltas (delta_water_heater, delta_water_radiator, delta_air)
- flow_rate, fan_speed
- main_loop_state, diversion_state
- control_mode, flow_mode

### Graph Sessions (JSON)
**Trigger:** Live Graphing toggle ON  
**Collection:** Every 5 seconds  
**Save:** When toggle turned OFF or server shutdown  
**Filename:** `graph_YYYY-MM-DD_HH-MM-SS.json` (timestamp from START)

**JSON Structure:**
```json
{
  "metadata": {
    "start_time": "ISO timestamp",
    "end_time": "ISO timestamp",
    "duration_seconds": 123.45,
    "data_points": 25
  },
  "data": [
    {
      "timestamp": "ISO timestamp",
      "water_hot": 48.5,
      "water_reservoir": 45.2,
      ...all sensor values...
    }
  ]
}
```

### Key Features
- **Timestamps from session START** (not shutdown) - more accurate
- **Independent operation** - Save and Graph can run separately
- **In-memory collection** - Fast, no disk I/O during logging
- **Automatic cleanup** - Data saved on toggle off or shutdown
- **Organized structure** - Separate directories for different data types

---

## Phase 4: Data Explorer

### New Page: `/explorer`

**File:** `explorer.html`

### Features

#### Graph Sessions Section
- Lists all saved graph sessions (JSON files)
- Displays:
  - Filename
  - Start time
  - Duration
  - Number of data points
- **"📊 View Graph"** button - Opens historical session in graph viewer

#### CSV Data Logs Section
- Lists all CSV session logs
- Displays:
  - Filename
  - Date extracted from filename
  - File size
  - Last modified time
- **"💾 Download"** button - Downloads CSV to user's machine

### Visual Design
- Two sections (Graph Sessions, CSV Logs)
- Count badges showing number of each type
- Hover effects on session items
- Empty state messages when no data
- Color-coded badges (purple for graph, orange for CSV)

---

## Phase 5: Enhanced Graph Viewer

### Dual Mode Operation

#### Live Mode (Default)
- URL: `/graph`
- Connects to WebSocket
- Displays real-time data
- Updates every 5 seconds
- Status indicator shows connection state

#### Historical Mode (New)
- URL: `/graph?session=graph_YYYY-MM-DD_HH-MM-SS.json`
- Loads complete session from JSON file
- Displays all session metadata
- Same UI as live mode
- No WebSocket connection needed

### Mode Detection
```javascript
const urlParams = new URLSearchParams(window.location.search);
const sessionParam = urlParams.get('session');
const isHistoricalMode = !!sessionParam;
```

### Historical Session Display
- Page title changes to "📜 Historical Graph Session"
- Info banner shows: filename, data points, duration
- Connection status hidden (not relevant)
- Full session data loaded at once
- Same interactive controls (checkboxes, zoom, etc.)

### Benefits
- **Replay past sessions** - Analyze historical data
- **Compare sessions** - Open multiple tabs
- **No data loss** - Complete session preserved
- **Same interface** - No learning curve
- **Fast loading** - JSON optimized for graphs

---

## Server-Side Changes

### New Endpoints

#### `/controls`
Serves the controls page.

#### `/explorer`
Serves the data explorer page.

#### `/api/sessions`
Returns list of all CSV session files with metadata:
```json
{
  "sessions": [
    {
      "filename": "session_2026-01-14_19-16-47.csv",
      "size": 503,
      "modified": 1736885839.0,
      "type": "csv"
    }
  ]
}
```

#### `/api/graph_sessions`
Returns list of all graph session files with metadata:
```json
{
  "sessions": [
    {
      "filename": "graph_2026-01-14_19-16-50.json",
      "start_time": "2026-01-14T19:16:50",
      "end_time": "2026-01-14T19:17:22",
      "duration": 32.0,
      "data_points": 3,
      "type": "graph"
    }
  ]
}
```

#### `/api/load_session/{filename}`
Loads and returns a complete graph session JSON file.

**Security:** Validates filename (no path traversal).

### Static File Mounting
```python
app.mount("/images", StaticFiles(directory="images"), name="images")
app.mount("/data_logs", StaticFiles(directory="data_logs"), name="data_logs")
app.mount("/graph_sessions", StaticFiles(directory="graph_sessions"), name="graph_sessions")
```

### Controller Enhancements

#### New Instance Variables
```python
self.save_start_time = None      # When logging started
self.graph_start_time = None     # When graphing started
```

#### Enhanced Methods
- `set_save_enabled()` - Records start time, saves on disable
- `set_graph_enabled()` - Records start time, saves on disable
- `save_to_csv()` - Uses start timestamp, saves to data_logs/
- `save_graph_session()` - Creates JSON with metadata, saves to graph_sessions/
- `cleanup()` - Saves both CSV and graph sessions if active

---

## Testing Results

### Test 1: Enable Data Logging
✅ **PASS**
- Toggle turned ON
- Start timestamp recorded
- Data collection began

### Test 2: Enable Live Graphing
✅ **PASS**
- Toggle turned ON
- Start timestamp recorded
- Data collection began

### Test 3: Data Collection
✅ **PASS**
- Data collected every 5 seconds
- Both CSV and graph data stored in memory

### Test 4: Save on Toggle OFF
✅ **PASS**
- Turned off Data Logging toggle
- CSV file created in `data_logs/` with correct timestamp
- Turned off Live Graphing toggle
- JSON file created in `graph_sessions/` with correct timestamp

### Test 5: Data Explorer Lists Sessions
✅ **PASS**
- Navigated to `/explorer`
- Both CSV and graph sessions listed correctly
- Metadata displayed accurately (filename, duration, data points, file size)
- Counts shown in badges

### Test 6: View Historical Graph Session
✅ **PASS**
- Clicked "📊 View Graph" button
- Redirected to `/graph?session=graph_2026-01-14_19-16-50.json`
- Historical session loaded successfully
- Graph displayed all temperature data
- Session metadata shown (3 points, 32s duration)
- Interactive controls working (checkboxes, buttons)

### Test 7: Independent Operation
✅ **PASS**
- Enabled Data Logging alone - worked independently
- Enabled Live Graphing alone - worked independently
- Enabled both together - worked independently
- Disabled in different order - both saved correctly

---

## File Changes Summary

### New Files Created
1. `controls.html` - Dedicated controls page
2. `explorer.html` - Data explorer page
3. `UI_REORGANIZATION.md` - This documentation
4. `data_logs/.gitkeep` - Track directory in git
5. `graph_sessions/.gitkeep` - Track directory in git

### Modified Files
1. `web_ui.html` - Removed controls, added navigation
2. `graph.html` - Added historical mode support
3. `shopheater3000.py` - Added endpoints, enhanced data management
4. `.gitignore` - Added data directories

### Lines Changed
- **8 files changed**
- **1,305 insertions**
- **209 deletions**

---

## User Experience Improvements

### Before
- Cluttered main page with monitoring + controls
- No way to save or analyze historical data
- Graph only showed live data
- No organized file structure

### After
- Clean separation: Dashboard (view) vs Controls (interact)
- Automatic data logging with organized storage
- Graph sessions saved for later analysis
- Data Explorer for browsing all sessions
- Historical graph viewing with same interface
- Professional file organization
- Timestamp-based naming for easy sorting

---

## Future Enhancements (Potential)

1. **Session Comparison**
   - Load multiple sessions in one graph
   - Overlay different runs
   - Identify patterns

2. **Data Analysis Tools**
   - Calculate averages, min/max
   - Efficiency metrics
   - Performance trends

3. **Export Options**
   - Export graph as PNG/SVG
   - Generate reports
   - Share sessions

4. **Session Management**
   - Delete old sessions
   - Rename sessions
   - Add notes/tags
   - Archive by date range

5. **Advanced Filtering**
   - Search sessions by date
   - Filter by duration
   - Filter by control mode used

---

## Conclusion

This reorganization represents a significant upgrade to the Shop Heater system:

✅ **Cleaner UI** - Separation of monitoring and control  
✅ **Data Persistence** - All sessions saved automatically  
✅ **Historical Analysis** - Review past performance  
✅ **Professional Organization** - Structured file storage  
✅ **Independent Operation** - Save and Graph work separately  
✅ **Easy Discovery** - Data Explorer for all sessions  
✅ **Seamless Experience** - Same UI for live and historical data  

**Status:** All features implemented, tested, and working correctly.

