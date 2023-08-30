# MonchoCut
All you need to Cut by Moncho a wood!

# Requirements
rectpack
matplotlib

# Venv
```bash
python3 -m venv venv
venv/bin/python -m pip install -U pip rectpack matplotlib pyyaml --no-cache-dir
```

If you're in Windows Bash, perhaps you hav to replace all the:

```bash
venv/bin/python
```

by

```bash
venv\Scripts\python.exe
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
venv/bin/python monchocut.py --file cutlist.txt
```

If you want to replicate the same list 5 times:

```bash
venv/bin/python monchocut.py --file cutlist.txt --qty 5
```

# Using Yaml config

Create a YAML config with the `path` and `qty` (if not, 1 will be used).

content of `config.yaml`:

```yaml
furniture_1:
  - path: 'path/to/furniture_1/cutlist.txt'
furniture_2:
  - path: 'path/to/furniture_2/cutlist.txt'
  - qty: 2
```

Then run:

```bash
venv/bin/python monchocut.py --yaml config.yaml
```
