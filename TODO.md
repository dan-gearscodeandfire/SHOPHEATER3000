# TODO - SHOPHEATER3000

## High Priority

### 🔴 Web UI Control Switches - BUGGY/LAGGY
**Status:** KNOWN ISSUE - Needs investigation and proper fix

**Problem:**
- Solenoid toggle switches are very buggy and laggy
- When clicked, switches toggle multiple times before settling
- User experience is poor - controls don't feel responsive
- Current fix (immediate state update after command) did not fully resolve the issue

**Attempted Fixes:**
1. ✗ Debouncing client-side updates (reverted - workaround, not proper fix)
2. ✗ Immediate state update after server processes command (implemented, but not sufficient)

**Next Steps:**
- [ ] Investigate timing between hardware response and state updates
- [ ] Check if relay state reads are accurate/fast enough
- [ ] Consider adding state change confirmation from hardware
- [ ] May need to review entire control flow architecture
- [ ] Test with hardware disconnected to isolate UI vs hardware timing

**Temporary Workaround:**
- None currently - users should be aware controls may require multiple clicks

---

## Medium Priority

### Display Solenoid Status on Grid
**Status:** TODO - Enhancement

Currently solenoid status is only shown in control toggles below the grid. Consider adding visual indicators on the grid itself to show valve states.

---

## Low Priority

### Reduce Debug Logging Verbosity
**Status:** Nice to have

Current implementation has extensive debug logging which is useful for development but may be too verbose for production use.

**Tasks:**
- [ ] Add logging level configuration
- [ ] Move verbose logs to DEBUG level
- [ ] Keep essential logs at INFO level

### Add HTTPS Support
**Status:** Future enhancement

For secure remote access, HTTPS should be implemented.

**Tasks:**
- [ ] Generate SSL certificates
- [ ] Configure uvicorn for HTTPS
- [ ] Update documentation

### Suppress Temperature Sensor Permission Warnings
**Status:** Low priority - cosmetic

Temperature sensor initialization shows permission warnings that are harmless but clutter output.

```
/bin/sh: 1: cannot create /sys/bus/w1/devices/28-*/w1_slave: Permission denied
```

These warnings don't affect functionality but could be suppressed or redirected.

---

## Completed ✅

- [x] Sensor calibration with ice water test
- [x] Assign specific sensor IDs to locations
- [x] Web UI real-time display implementation
- [x] WebSocket connection stability (fixed connection loop)
- [x] Temperature conversion to Fahrenheit
- [x] Delta calculations (heater, radiator, air)
- [x] Flow rate display
- [x] Fan speed control (text + slider)
- [x] Basic solenoid control implementation

---

**Last Updated:** January 10, 2026  
**Priority Order:** Fix control switches → Other enhancements

