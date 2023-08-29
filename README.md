# MonchoCut
All you need to Cut by Moncho a wood!

# Requirements
rectpack
matplotlib

# Venv
```bash
python3 -m venv venv
venv/bin/python -m pip install -U pip rectpack matplotlib --no-cache-dir
```

# Usage
If you have a `cutlist.txt` from PolyBoard, or some `txt` like:

```
490.00;582.00;1;Sarasa_18;0;Techo;0;0;0.00;0;0;0.00;;;;
```

Where:
  - width: 490.00
  - height: 582.00
  - quantity: 1
  - material: Sarasa_18
  - aux_material_flag: 0
  - Cut name: Techo
  - More editable things...

```bash
venv/bin/python monchocut.py cutlist.txt 5
```

Where 5 is the number of the same list of cuts (this parameter
must be higher than 0).
