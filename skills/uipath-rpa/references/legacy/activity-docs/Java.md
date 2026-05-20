# UiPath Java Activities - Community Reference

## Overview
Execute Java code and interact with Java objects from UiPath workflows. Package: `UiPath.Java.Activities` (from Community.Activities repo).

---

## Activities

| Activity | Purpose | Key Arguments |
|----------|---------|---------------|
| `JavaScope` | Container - initialize JVM | Path (JRE/JDK install), Body |
| `LoadJar` | Load JAR file into classpath | JarPath (required), Output: loaded into scope |
| `InvokeJavaMethod` | Call static/instance method | Instance (JavaObject, null for static), MethodName (required), TargetType (class name for static), InputParameters (object[]) -> Result (JavaObject) |
| `CreateJavaObject` | Instantiate Java class | TargetType (class name, required), InputParameters (object[]) -> Result (JavaObject) |
| `ConvertJavaObject` | Convert JavaObject to .NET | JavaObject, TypeArgument -> typed result |
| `GetJavaField` | Read field from Java object | Instance (JavaObject), FieldName (required), TargetType (class for static fields) -> Result (JavaObject) |

---

## JavaScope Configuration
- `Path` (string) - Path to JRE/JDK installation (e.g., `C:\Program Files\Java\jre1.8.0_291`)
- All Java activities must be inside JavaScope

---

## Critical Gotchas

### JavaScope
1. **All Java activities MUST be inside JavaScope** - container required
2. **JRE/JDK must be installed** on the machine - not bundled
3. **JAVA_HOME or explicit Path** required for JVM initialization
4. **JVM architecture must match** - 32-bit JRE for x86 workflows, 64-bit for x64

### JAR Loading
5. **LoadJar must be called before using classes from that JAR**
6. **Multiple JARs can be loaded** - each LoadJar adds to classpath
7. **JAR dependency resolution** - all dependent JARs must also be loaded

### Method Invocation
8. **Static methods**: set Instance=null, TargetType to fully qualified class name
9. **Instance methods**: set Instance to JavaObject, TargetType not needed
10. **InputParameters are positional** (object array) - order and types must match Java method signature
11. **Method overloading** resolved by parameter count and types

### Type Conversion
12. **ConvertJavaObject maps**: Java String -> .NET string, int/long -> int/long, boolean -> bool
13. **Complex Java objects remain as JavaObject** - must use ConvertJavaObject for .NET types
14. **Arrays**: Java arrays can map to .NET arrays via ConvertJavaObject
15. **JavaObject is opaque** from .NET side - use GetJavaField or InvokeJavaMethod to access

### Performance
16. **JNI bridge overhead** - each call crosses JVM/.NET boundary
17. **Minimize cross-boundary calls** - do heavy work in Java, return results
18. **JVM startup time** - first JavaScope invocation is slow (~1-3 seconds)

### Error Handling
19. **Java exceptions wrapped** in .NET exceptions - check InnerException for Java stack trace
20. **ClassNotFoundException** if JAR not loaded or class name misspelled
21. **NoSuchMethodException** if method signature doesn't match
