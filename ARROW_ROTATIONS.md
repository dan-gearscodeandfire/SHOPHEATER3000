# Arrow Rotation Reference

## Base Orientations (0° / No Rotation)

| Arrow Type | Base Orientation | Description |
|------------|------------------|-------------|
| **Straight** (`256_arrow_[color].png`) | → (RIGHT) | Points horizontally to the right |
| **90° Turn** (`256_arrow_[color]_90.png`) | ←↑ (LEFT-UP) | Enters from left, exits upward (L-shape) |
| **Branch** (`256_arrow_[color]_branch.png`) | →⟨←↓⟩ (RIGHT to LEFT+DOWN) | Enters from right, splits to left and down (T-shape) |

## CSS Rotation Reference

- **0°** = No rotation (base image)
- **90°** = 90° clockwise (→ becomes ↓, ↑ becomes →)
- **180°** = 180° flip (→ becomes ←, ↑ becomes ↓)
- **270° or -90°** = 90° counter-clockwise (→ becomes ↑, ↓ becomes →)

---

## Cell-Specific Rotations by Flow Mode

### Cell 0:1

**Required Final Orientations:**
- **Main mode:** Turn from RIGHT to DOWN (→↓)
- **Diversion mode:** Point LEFT (←)
- **Mix mode:** Branch from RIGHT to LEFT+DOWN (→⟨←↓⟩)

**Current Rotations (from user spec):**
- **Main mode:** 90° arrow + **90° CW rotation**
  - Base ←↑ + 90° CW = ↓→ = DOWN-RIGHT turn ✓
- **Diversion mode:** Straight arrow + **180° rotation**
  - Base → + 180° = ← (points LEFT) ✓
- **Mix mode:** Branch arrow + **180° rotation**
  - Base →⟨←↓⟩ + 180° = ←⟨→↑⟩ (enters from LEFT, branches to RIGHT+UP)
  - **Question:** Does this match the actual plumbing flow?

---

### Cell 0:0

**Current Rotations (from user spec):**
- **Diversion mode:** 90° arrow + **90° CW rotation**
  - Base ←↑ + 90° CW = ↓→ = DOWN-RIGHT turn
- **Mix mode:** 90° arrow + **90° CW rotation**
  - Base ←↑ + 90° CW = ↓→ = DOWN-RIGHT turn

---

### Cell 3:1

**Current Rotations (from user spec):**
- **Main mode:** 90° arrow + **90° CW rotation**
  - Base ←↑ + 90° CW = ↓→ = DOWN-RIGHT turn
- **Diversion mode:** Straight arrow + **90° CW rotation**
  - Base → + 90° CW = ↓ (points DOWN)
- **Mix mode:** Branch arrow + **90° CW rotation**
  - Base →⟨←↓⟩ + 90° CW = ↓⟨↑→⟩ (enters from DOWN, branches to UP+RIGHT)

---

## Current Implementation Status (CORRECTED)

**Main mode (main ON, diversion OFF):**
- ✅ Cell 0:1: 90° CW
- ✅ Cell 3:1: 90° CW

**Mix mode (main ON, diversion ON):**
- ✅ Cell 0:1: 180° CW
- ✅ Cell 0:0: 180° CW
- ✅ Cell 3:1: 90° CW
- ✅ Cell 3:0: 90° CW

**Diversion mode (main OFF, diversion ON):**
- ✅ Cell 0:0: 180° CW
- ✅ Cell 3:0: 90° CW
- ✅ Cell 3:1: 90° CCW (-90deg)  

All requested rotations have been implemented in `web_ui.html`.

---

## Notes

- All three arrow types (straight, 90°, branch) come in three colors (red, orange, blue)
- Color is determined dynamically based on temperature readings
- Arrow type and rotation is determined by flow mode (main/diversion/mix)
- Visibility is also controlled by flow mode (some arrows hidden in certain modes)
