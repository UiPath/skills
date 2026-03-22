# UiPath Python Activities - Community Reference

## Overview
Execute Python scripts and interact with Python objects from UiPath workflows. Package: `UiPath.Python.Activities` (from Community.Activities repo).

---

## Activities

| Activity | Purpose | Key Arguments |
|----------|---------|---------------|
| `PythonScope` | Container - initialize Python runtime | Path (Python install), Target (x86/x64), Version (Auto/Python_27/35/36/37/38/39/310), WorkingFolder, Body |
| `LoadScript` | Load Python script file | File (path to .py), Output: PythonObject (script module) |
| `RunScript` | Execute Python code string | Code (string), Output: PythonObject (result) |
| `InvokeMethod` | Call method on Python object | Instance (PythonObject), Name (method name), InputParameters (object[]), Output: PythonObject (return value) |
| `GetObject` | Convert PythonObject to .NET type | PythonObject, TypeArgument (target .NET type), Output: typed result |

---

## PythonScope Configuration

### Key Properties
- `Path` (string) - Path to Python installation (e.g., `C:\Python39`)
- `Target` (enum) - x86 or x64 (must match Python installation)
- `Version` (enum) - Auto, Python_27, Python_35, Python_36, Python_37, Python_38, Python_39, Python_310
- `WorkingFolder` (string) - Working directory for Python scripts
- `LibraryPath` (string) - Additional library paths (added to sys.path)

---

## Critical Gotchas

### PythonScope
1. **All Python activities MUST be inside PythonScope** - container required
2. **Target (x86/x64) must match Python installation** - mixing causes load failure
3. **Version Auto** tries to detect, but explicit version is safer
4. **Python must be installed** on the machine - not bundled with activities
5. **PATH environment variable** may need to include Python directory

### Host Process
6. **Python runs in separate host process** (UiPath.Python.Host.exe / UiPath.Python.Host32.exe)
7. **32-bit host (Host32)** for x86 Python, 64-bit for x64
8. **Host process crash** can orphan Python processes
9. **IPC communication** between workflow and Python host - adds latency

### Script Execution
10. **RunScript executes code string** - use for inline Python code
11. **LoadScript loads .py file** - returns module as PythonObject
12. **InvokeMethod calls function** on loaded module or object
13. **InputParameters are positional** (object array) - order matters

### Type Conversion
14. **GetObject converts PythonObject to .NET type** - limited type mapping:
    - Python int/float -> .NET int/double
    - Python str -> .NET string
    - Python list -> .NET object[] or List<T>
    - Python dict -> .NET Dictionary<string, object>
    - Complex objects may not convert cleanly
15. **PythonObject is opaque** - cannot inspect properties from .NET side without GetObject
16. **Large data transfers are slow** due to IPC serialization

### Environment
17. **Virtual environments** - set Path to venv's python.exe parent directory
18. **pip packages** must be installed in the Python environment being used
19. **sys.path** extended with WorkingFolder and LibraryPath
20. **Multiple PythonScopes** in same workflow may conflict - use one scope per Python environment
