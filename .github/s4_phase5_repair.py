from pathlib import Path

path = Path('.github/s4_phase5.py')
text = path.read_text()
text = text.replace(
    '        queen_mg.set_value(&mut degraded, 100);\n        queen_eg.set_value(&mut degraded, 100);',
    '        let degraded_queen_mg = baseline_values[queen_mg.index()] - 200;\n        let degraded_queen_eg = baseline_values[queen_eg.index()] - 200;\n        queen_mg.set_value(&mut degraded, degraded_queen_mg);\n        queen_eg.set_value(&mut degraded, degraded_queen_eg);',
    1,
)
old = '''        let initial_queen_distance =
            (i32::from(100_i16) - i32::from(baseline_values[queen_mg.index()])).abs()
                + (i32::from(100_i16) - i32::from(baseline_values[queen_eg.index()])).abs();'''
new = '''        let initial_queen_distance =
            (i32::from(degraded_queen_mg) - i32::from(baseline_values[queen_mg.index()])).abs()
                + (i32::from(degraded_queen_eg)
                    - i32::from(baseline_values[queen_eg.index()]))
                .abs();'''
if text.count(old) != 1:
    raise SystemExit('queen-distance fixture anchor missing')
text = text.replace(old, new, 1)
path.write_text(text)
