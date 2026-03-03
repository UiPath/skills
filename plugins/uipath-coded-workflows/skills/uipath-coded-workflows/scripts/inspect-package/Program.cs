using System.IO.Compression;
using System.Reflection;
using System.Runtime.InteropServices;
using System.Text;
using System.Xml.Linq;

if (args.Length < 2)
{
    Console.Error.WriteLine("Usage: dotnet run --project <path> -- <PackageName> <Version> [FeedUrl]");
    Console.Error.WriteLine("  FeedUrl defaults to the UiPath Official feed.");
    Console.Error.WriteLine("Example: dotnet run --project tools/inspect-package -- UiPath.Excel.Activities 3.3.1");
    return 1;
}

string packageName = args[0];
string version = args[1];
string feedUrl = args.Length >= 3
    ? args[2]
    : "https://uipath.pkgs.visualstudio.com/Public.Feeds/_packaging/UiPath-Official/nuget/v3/index.json";

string tempDir = Path.Combine(Path.GetTempPath(), $"inspect-pkg-{packageName}-{version}-{Guid.NewGuid():N}");
Directory.CreateDirectory(tempDir);

using var sharedHttp = new HttpClient { Timeout = TimeSpan.FromSeconds(120) };

try
{
    // 1. Download the main package
    string nupkgPath = Path.Combine(tempDir, $"{packageName}.{version}.nupkg");
    await DownloadNupkgAsync(packageName, version, feedUrl, nupkgPath, sharedHttp);

    // 2. Extract the nupkg (it's a ZIP)
    string extractDir = Path.Combine(tempDir, "extracted");
    ZipFile.ExtractToDirectory(nupkgPath, extractDir);

    // 3. Find DLLs in lib/ targeting the best framework
    var dllPaths = FindBestFrameworkDlls(extractDir);
    if (dllPaths.Count == 0)
    {
        Console.Error.WriteLine("No DLLs found in the package lib/ folder.");
        return 1;
    }

    // 4. Parse .nuspec for dependencies and download them
    string targetFramework = Path.GetFileName(Path.GetDirectoryName(dllPaths[0])) ?? "net6.0";
    var dependencies = ParseNuspecDependencies(extractDir, targetFramework);
    var (depDlls, subPackageDlls) = await DownloadDependencyPackagesAsync(
        dependencies, packageName, feedUrl, tempDir, sharedHttp);

    // 5. Combine main DLLs + sub-package DLLs for inspection; all dep DLLs for resolution
    var dllsToInspect = new List<string>(dllPaths);
    dllsToInspect.AddRange(subPackageDlls);

    // 6. Use MetadataLoadContext for reflection-only inspection
    var output = InspectAssemblies(dllsToInspect, depDlls, packageName);
    Console.Write(output);
    return 0;
}
catch (Exception ex)
{
    Console.Error.WriteLine($"Error: {ex.Message}");
    return 1;
}
finally
{
    try { Directory.Delete(tempDir, true); } catch { }
}

// --- Helper methods ---

static async Task DownloadNupkgAsync(string packageName, string version, string feedUrl, string outputPath, HttpClient? http = null)
{
    bool ownHttp = http == null;
    http ??= new HttpClient { Timeout = TimeSpan.FromSeconds(60) };

    try
    {
        // Resolve NuGet v3 service index to find PackageBaseAddress resource
        string baseAddress = await ResolvePackageBaseAddressAsync(http, feedUrl);

        // NuGet v3 flat container URL pattern
        string downloadUrl = $"{baseAddress.TrimEnd('/')}/{packageName.ToLowerInvariant()}/{version.ToLowerInvariant()}/{packageName.ToLowerInvariant()}.{version.ToLowerInvariant()}.nupkg";

        Console.Error.WriteLine($"Downloading {downloadUrl} ...");
        using var primaryResponse = await http.GetAsync(downloadUrl);
        if (primaryResponse.IsSuccessStatusCode)
        {
            await using var fs = File.Create(outputPath);
            await primaryResponse.Content.CopyToAsync(fs);
            Console.Error.WriteLine($"Downloaded {new FileInfo(outputPath).Length / 1024}KB");
            return;
        }

        // Fallback: try NuGet.org
        string nugetOrgUrl = $"https://api.nuget.org/v3-flatcontainer/{packageName.ToLowerInvariant()}/{version.ToLowerInvariant()}/{packageName.ToLowerInvariant()}.{version.ToLowerInvariant()}.nupkg";
        Console.Error.WriteLine($"Feed returned {primaryResponse.StatusCode}, trying nuget.org: {nugetOrgUrl}");
        using var fallbackResponse = await http.GetAsync(nugetOrgUrl);
        if (!fallbackResponse.IsSuccessStatusCode)
        {
            throw new Exception($"Package '{packageName}' version '{version}' not found. " +
                $"Primary feed returned {(int)primaryResponse.StatusCode}, nuget.org returned {(int)fallbackResponse.StatusCode}. " +
                "Verify the package name and version are correct.");
        }

        await using var fs2 = File.Create(outputPath);
        await fallbackResponse.Content.CopyToAsync(fs2);
        Console.Error.WriteLine($"Downloaded {new FileInfo(outputPath).Length / 1024}KB");
    }
    finally
    {
        if (ownHttp) http.Dispose();
    }
}

static async Task<string> ResolvePackageBaseAddressAsync(HttpClient http, string feedUrl)
{
    try
    {
        string indexJson = await http.GetStringAsync(new Uri(feedUrl));
        // Find PackageBaseAddress/3.0.0 and extract the @id from the same resource object.
        int typeIdx = indexJson.IndexOf("PackageBaseAddress/3.0.0", StringComparison.OrdinalIgnoreCase);
        if (typeIdx < 0)
            typeIdx = indexJson.IndexOf("PackageBaseAddress", StringComparison.OrdinalIgnoreCase);
        if (typeIdx > 0)
        {
            int objStart = indexJson.LastIndexOf('{', typeIdx);
            int objEnd = indexJson.IndexOf('}', typeIdx);
            if (objStart >= 0 && objEnd > objStart)
            {
                string obj = indexJson.Substring(objStart, objEnd - objStart + 1);
                int idIdx = obj.IndexOf("\"@id\"", StringComparison.OrdinalIgnoreCase);
                if (idIdx >= 0)
                {
                    int colonIdx = obj.IndexOf(':', idIdx + 4);
                    int quoteStart = obj.IndexOf('"', colonIdx + 1);
                    int quoteEnd = obj.IndexOf('"', quoteStart + 1);
                    if (quoteStart >= 0 && quoteEnd > quoteStart)
                    {
                        return obj.Substring(quoteStart + 1, quoteEnd - quoteStart - 1);
                    }
                }
            }
        }
    }
    catch (Exception ex)
    {
        Console.Error.WriteLine($"Warning: Could not resolve feed index: {ex.Message}");
    }

    // Fallback: construct a likely base address from the feed URL
    if (feedUrl.Contains("uipath.pkgs.visualstudio.com"))
        return "https://uipath.pkgs.visualstudio.com/5b98d55c-1b14-4a03-893f-7a59746f1246/_packaging/1c781268-d43d-45ab-9dfc-0151a1c740b7/nuget/v3/flat2/";
    return "https://api.nuget.org/v3-flatcontainer/";
}

static List<string> FindBestFrameworkDlls(string extractDir)
{
    string libDir = Path.Combine(extractDir, "lib");
    if (!Directory.Exists(libDir))
    {
        // Some packages put DLLs at root
        return Directory.GetFiles(extractDir, "*.dll", SearchOption.TopDirectoryOnly).ToList();
    }

    // Preference order for target frameworks
    string[] preferences = new[] {
        "net8.0", "net7.0", "net6.0",
        "net8.0-windows", "net7.0-windows", "net6.0-windows", "net6.0-windows7.0",
        "netstandard2.1", "netstandard2.0", "netstandard1.6",
        "net48", "net472", "net461", "net46", "net45",
        "netcoreapp3.1"
    };

    var frameworkDirs = Directory.GetDirectories(libDir);
    string? bestDir = null;

    foreach (var pref in preferences)
    {
        bestDir = frameworkDirs.FirstOrDefault(d =>
            Path.GetFileName(d).Equals(pref, StringComparison.OrdinalIgnoreCase));
        if (bestDir != null) break;
    }

    // If no preference matched, just take the first one
    bestDir ??= frameworkDirs.FirstOrDefault();

    if (bestDir == null) return new List<string>();

    Console.Error.WriteLine($"Using target framework: {Path.GetFileName(bestDir)}");
    return Directory.GetFiles(bestDir, "*.dll").ToList();
}

static List<(string Id, string Version)> ParseNuspecDependencies(string extractDir, string targetFramework)
{
    var deps = new List<(string Id, string Version)>();

    var nuspecFiles = Directory.GetFiles(extractDir, "*.nuspec", SearchOption.TopDirectoryOnly);
    if (nuspecFiles.Length == 0)
    {
        Console.Error.WriteLine("No .nuspec file found in package.");
        return deps;
    }

    try
    {
        var doc = XDocument.Load(nuspecFiles[0]);
        var ns = doc.Root?.Name.Namespace ?? XNamespace.None;

        var metadata = doc.Root?.Element(ns + "metadata");
        var dependencies = metadata?.Element(ns + "dependencies");
        if (dependencies == null) return deps;

        // Try to find a dependency group matching our target framework
        var groups = dependencies.Elements(ns + "group").ToList();
        XElement? bestGroup = null;

        if (groups.Count > 0)
        {
            // Exact match first
            bestGroup = groups.FirstOrDefault(g =>
                (g.Attribute("targetFramework")?.Value ?? "").Equals(targetFramework, StringComparison.OrdinalIgnoreCase));

            if (bestGroup == null)
            {
                // Try matching the base framework (e.g., "net6.0" matches "net6.0-windows7.0")
                var baseFw = targetFramework.Split('-')[0];
                bestGroup = groups.FirstOrDefault(g =>
                {
                    var fw = g.Attribute("targetFramework")?.Value ?? "";
                    return fw.StartsWith(baseFw, StringComparison.OrdinalIgnoreCase);
                });
            }

            if (bestGroup == null)
            {
                // Try the framework preference order
                string[] fwPrefs = { "net8.0", "net7.0", "net6.0", "netstandard2.1", "netstandard2.0" };
                foreach (var pref in fwPrefs)
                {
                    bestGroup = groups.FirstOrDefault(g =>
                        (g.Attribute("targetFramework")?.Value ?? "").StartsWith(pref, StringComparison.OrdinalIgnoreCase));
                    if (bestGroup != null) break;
                }
            }

            bestGroup ??= groups.FirstOrDefault();
        }

        var depElements = bestGroup != null
            ? bestGroup.Elements(ns + "dependency")
            : dependencies.Elements(ns + "dependency");

        foreach (var dep in depElements)
        {
            var id = dep.Attribute("id")?.Value;
            var ver = dep.Attribute("version")?.Value;
            if (!string.IsNullOrEmpty(id) && !string.IsNullOrEmpty(ver))
            {
                // Normalize version: strip brackets from version ranges like "[25.12.2, )"
                ver = ver.Trim('[', ']', '(', ')', ' ');
                if (ver.Contains(','))
                    ver = ver.Split(',')[0].Trim();
                if (string.IsNullOrEmpty(ver)) continue;
                deps.Add((id, ver));
            }
        }
    }
    catch (Exception ex)
    {
        Console.Error.WriteLine($"Warning: Failed to parse .nuspec dependencies: {ex.Message}");
    }

    return deps;
}

static async Task<(List<string> AllDepDlls, List<string> SubPackageDlls)> DownloadDependencyPackagesAsync(
    List<(string Id, string Version)> dependencies,
    string packageName,
    string feedUrl,
    string tempDir,
    HttpClient sharedHttp,
    int maxDepth = 2)
{
    var allDepDlls = new List<string>();
    var subPackageDlls = new List<string>();
    var downloaded = new HashSet<string>(StringComparer.OrdinalIgnoreCase);

    await DownloadDepsRecursiveAsync(dependencies, packageName, feedUrl, tempDir, sharedHttp,
        allDepDlls, subPackageDlls, downloaded, maxDepth);

    Console.Error.WriteLine($"Resolved {allDepDlls.Count} dependency DLLs ({subPackageDlls.Count} from sub-packages to inspect).");
    return (allDepDlls, subPackageDlls);
}

static async Task DownloadDepsRecursiveAsync(
    List<(string Id, string Version)> dependencies,
    string packageName,
    string feedUrl,
    string tempDir,
    HttpClient sharedHttp,
    List<string> allDepDlls,
    List<string> subPackageDlls,
    HashSet<string> downloaded,
    int remainingDepth)
{
    if (remainingDepth <= 0 || dependencies.Count == 0) return;

    // Filter out already-downloaded packages
    var toDownload = dependencies.Where(d => downloaded.Add(d.Id)).ToList();
    if (toDownload.Count == 0) return;

    Console.Error.WriteLine($"Downloading {toDownload.Count} dependency packages for assembly resolution...");

    var tasks = toDownload.Select(async dep =>
    {
        try
        {
            string depDir = Path.Combine(tempDir, $"dep-{dep.Id}-{dep.Version}");
            Directory.CreateDirectory(depDir);
            string depNupkg = Path.Combine(depDir, $"{dep.Id}.{dep.Version}.nupkg");

            await DownloadNupkgAsync(dep.Id, dep.Version, feedUrl, depNupkg, sharedHttp);

            string depExtract = Path.Combine(depDir, "extracted");
            ZipFile.ExtractToDirectory(depNupkg, depExtract);

            var depDlls = FindBestFrameworkDlls(depExtract);
            bool isSubPackage = dep.Id.StartsWith(packageName + ".", StringComparison.OrdinalIgnoreCase)
                             || dep.Id.StartsWith(packageName + "_", StringComparison.OrdinalIgnoreCase);

            Console.Error.WriteLine($"  Resolved {dep.Id} ({depDlls.Count} DLLs{(isSubPackage ? ", sub-package — will inspect" : "")})");

            // For sub-packages, parse their nuspec for further dependencies
            List<(string Id, string Version)>? subDeps = null;
            if (isSubPackage && remainingDepth > 1)
            {
                string tfm = depDlls.Count > 0
                    ? Path.GetFileName(Path.GetDirectoryName(depDlls[0])) ?? "net6.0"
                    : "net6.0";
                subDeps = ParseNuspecDependencies(depExtract, tfm);
            }

            return (Dlls: depDlls, IsSubPackage: isSubPackage, SubDeps: subDeps);
        }
        catch (Exception ex)
        {
            Console.Error.WriteLine($"  Warning: Could not resolve {dep.Id} {dep.Version}: {ex.Message}");
            return (Dlls: new List<string>(), IsSubPackage: false, SubDeps: (List<(string Id, string Version)>?)null);
        }
    }).ToList();

    var results = await Task.WhenAll(tasks);

    var nextLevelDeps = new List<(string Id, string Version)>();

    foreach (var result in results)
    {
        allDepDlls.AddRange(result.Dlls);
        if (result.IsSubPackage)
            subPackageDlls.AddRange(result.Dlls);
        if (result.SubDeps != null)
            nextLevelDeps.AddRange(result.SubDeps);
    }

    // Recurse for sub-package dependencies
    if (nextLevelDeps.Count > 0)
    {
        await DownloadDepsRecursiveAsync(nextLevelDeps, packageName, feedUrl, tempDir, sharedHttp,
            allDepDlls, subPackageDlls, downloaded, remainingDepth - 1);
    }
}

static string InspectAssemblies(List<string> dllPaths, List<string> dependencyDlls, string packageName)
{
    var sb = new StringBuilder();
    sb.AppendLine($"# NuGet Package Inspection: {packageName}");
    sb.AppendLine();

    // Set up MetadataLoadContext with runtime assembly paths for resolving base types
    var runtimeDir = RuntimeEnvironment.GetRuntimeDirectory();
    var runtimeDlls = Directory.GetFiles(runtimeDir, "*.dll")
        .Where(f => !Path.GetFileName(f).StartsWith("api-ms-"))
        .ToList();

    var allPaths = new List<string>(runtimeDlls);
    allPaths.AddRange(dllPaths);

    // Add dependency DLLs for type resolution
    foreach (var depDll in dependencyDlls)
    {
        if (!allPaths.Contains(depDll))
            allPaths.Add(depDll);
    }

    // Also add any other DLLs from the same directory (dependencies within the package)
    foreach (var dll in dllPaths)
    {
        var dir = Path.GetDirectoryName(dll)!;
        foreach (var extra in Directory.GetFiles(dir, "*.dll"))
        {
            if (!allPaths.Contains(extra))
                allPaths.Add(extra);
        }
    }

    var resolver = new PathAssemblyResolver(allPaths);
    using var mlc = new MetadataLoadContext(resolver);

    foreach (var dllPath in dllPaths)
    {
        try
        {
            var assembly = mlc.LoadFromAssemblyPath(dllPath);
            var asmName = assembly.GetName().Name;
            sb.AppendLine($"## Assembly: {asmName}");
            sb.AppendLine();

            Type[] types;
            try { types = assembly.GetTypes(); }
            catch (ReflectionTypeLoadException ex) { types = ex.Types.Where(t => t != null).ToArray()!; }

            var publicTypes = types
                .Where(t => t.IsPublic)
                .OrderBy(t => t.Namespace)
                .ThenBy(t => t.Name)
                .ToList();

            // Group: Enums
            var enums = publicTypes.Where(t => t.IsEnum).ToList();
            if (enums.Count > 0)
            {
                sb.AppendLine("### Enums");
                sb.AppendLine();
                foreach (var e in enums)
                {
                    sb.AppendLine($"#### `{FormatTypeName(e)}`");
                    sb.AppendLine($"Namespace: `{e.Namespace}`");
                    sb.AppendLine();
                    sb.AppendLine("| Name | Value |");
                    sb.AppendLine("|------|-------|");
                    foreach (var field in e.GetFields(BindingFlags.Public | BindingFlags.Static))
                    {
                        try
                        {
                            var val = field.GetRawConstantValue();
                            sb.AppendLine($"| `{field.Name}` | `{val}` |");
                        }
                        catch
                        {
                            sb.AppendLine($"| `{field.Name}` | |");
                        }
                    }
                    sb.AppendLine();
                }
            }

            // Group: Interfaces
            var interfaces = publicTypes.Where(t => t.IsInterface).ToList();
            if (interfaces.Count > 0)
            {
                sb.AppendLine("### Interfaces");
                sb.AppendLine();
                foreach (var iface in interfaces)
                {
                    sb.AppendLine($"#### `{FormatTypeName(iface)}`");
                    sb.AppendLine($"Namespace: `{iface.Namespace}`");
                    sb.AppendLine();
                    PrintMembers(sb, iface);
                }
            }

            // Group: Classes and Structs
            var classes = publicTypes.Where(t => t.IsClass && !t.IsEnum && !IsDelegate(t)).ToList();
            var structs = publicTypes.Where(t => t.IsValueType && !t.IsEnum).ToList();
            var allClassLike = classes.Concat(structs).ToList();

            if (allClassLike.Count > 0)
            {
                sb.AppendLine("### Classes & Structs");
                sb.AppendLine();
                foreach (var cls in allClassLike)
                {
                    string kind = cls.IsValueType ? "struct" : (cls.IsAbstract && cls.IsSealed ? "static class" : cls.IsAbstract ? "abstract class" : "class");
                    string inheritance = "";
                    try
                    {
                        var baseType = cls.BaseType;
                        inheritance = baseType != null && baseType.FullName != "System.Object" && baseType.FullName != "System.ValueType"
                            ? $" : {FormatTypeName(baseType)}"
                            : "";

                        var implementedInterfaces = cls.GetInterfaces();
                        if (implementedInterfaces.Length > 0)
                        {
                            var ifaceNames = implementedInterfaces
                                .Where(i => i.IsPublic)
                                .Select(FormatTypeName)
                                .Take(5);
                            var ifaceStr = string.Join(", ", ifaceNames);
                            if (!string.IsNullOrEmpty(ifaceStr))
                            {
                                inheritance = string.IsNullOrEmpty(inheritance)
                                    ? $" : {ifaceStr}"
                                    : $"{inheritance}, {ifaceStr}";
                            }
                        }
                    }
                    catch { /* skip inheritance info if unresolvable */ }

                    sb.AppendLine($"#### `{kind} {FormatTypeName(cls)}{inheritance}`");
                    sb.AppendLine($"Namespace: `{cls.Namespace}`");
                    sb.AppendLine();
                    PrintMembers(sb, cls);
                }
            }

            // Group: Delegates
            var delegates = publicTypes.Where(t => IsDelegate(t)).ToList();
            if (delegates.Count > 0)
            {
                sb.AppendLine("### Delegates");
                sb.AppendLine();
                foreach (var del in delegates)
                {
                    try
                    {
                        var invoke = del.GetMethod("Invoke");
                        if (invoke != null)
                        {
                            var parms = FormatParameters(invoke.GetParameters());
                            sb.AppendLine($"- `{FormatTypeName(invoke.ReturnType)} {FormatTypeName(del)}({parms})`");
                        }
                        else
                        {
                            sb.AppendLine($"- `{FormatTypeName(del)}`");
                        }
                    }
                    catch
                    {
                        sb.AppendLine($"- `{del.Name}` *(unresolved delegate signature)*");
                    }
                }
                sb.AppendLine();
            }
        }
        catch (Exception ex)
        {
            sb.AppendLine($"*Error loading {Path.GetFileName(dllPath)}: {ex.Message}*");
            sb.AppendLine();
        }
    }

    return sb.ToString();
}

static void PrintMembers(StringBuilder sb, Type type)
{
    var bindingFlags = BindingFlags.Public | BindingFlags.Instance | BindingFlags.Static | BindingFlags.DeclaredOnly;

    // Properties
    var properties = type.GetProperties(bindingFlags)
        .Where(p => p.GetMethod?.IsPublic == true || p.SetMethod?.IsPublic == true)
        .OrderBy(p => p.Name)
        .ToList();

    if (properties.Count > 0)
    {
        sb.AppendLine("**Properties:**");
        sb.AppendLine();
        sb.AppendLine("| Name | Type | Get | Set |");
        sb.AppendLine("|------|------|-----|-----|");
        foreach (var prop in properties)
        {
            try
            {
                string get = prop.GetMethod?.IsPublic == true ? "Y" : "";
                string set = prop.SetMethod?.IsPublic == true ? "Y" : "";
                sb.AppendLine($"| `{prop.Name}` | `{FormatTypeName(prop.PropertyType)}` | {get} | {set} |");
            }
            catch
            {
                sb.AppendLine($"| `{prop.Name}` | `<unresolved>` | | |");
            }
        }
        sb.AppendLine();
    }

    // Methods (exclude property accessors, event accessors, and compiler-generated)
    var methods = type.GetMethods(bindingFlags)
        .Where(m => !m.IsSpecialName && m.IsPublic)
        .OrderBy(m => m.Name)
        .ToList();

    if (methods.Count > 0)
    {
        sb.AppendLine("**Methods:**");
        sb.AppendLine();
        foreach (var method in methods)
        {
            try
            {
                string staticMod = method.IsStatic ? "static " : "";
                string parms = FormatParameters(method.GetParameters());
                string genericSuffix = "";
                if (method.IsGenericMethod)
                {
                    var gArgs = method.GetGenericArguments();
                    genericSuffix = $"<{string.Join(", ", gArgs.Select(a => a.Name))}>";
                }
                sb.AppendLine($"- `{staticMod}{FormatTypeName(method.ReturnType)} {method.Name}{genericSuffix}({parms})`");
            }
            catch
            {
                sb.AppendLine($"- `{method.Name}(...)` *(unresolved signature)*");
            }
        }
        sb.AppendLine();
    }

    // Events
    var events = type.GetEvents(bindingFlags);
    if (events.Length > 0)
    {
        sb.AppendLine("**Events:**");
        sb.AppendLine();
        foreach (var evt in events)
        {
            try
            {
                sb.AppendLine($"- `{FormatTypeName(evt.EventHandlerType!)} {evt.Name}`");
            }
            catch
            {
                sb.AppendLine($"- `{evt.Name}` *(unresolved handler type)*");
            }
        }
        sb.AppendLine();
    }
}

static string FormatParameters(ParameterInfo[] parameters)
{
    return string.Join(", ", parameters.Select(p =>
    {
        try
        {
            string prefix = p.IsOut ? "out " : p.ParameterType.IsByRef ? "ref " : "";
            string typeName = FormatTypeName(p.ParameterType);
            string defaultVal = p.HasDefaultValue ? $" = {FormatDefaultValue(p.DefaultValue)}" : "";
            return $"{prefix}{typeName} {p.Name}{defaultVal}";
        }
        catch
        {
            return $"<unresolved> {p.Name ?? "?"}";
        }
    }));
}

static string FormatDefaultValue(object? value)
{
    if (value == null) return "null";
    if (value is string s) return $"\"{s}\"";
    if (value is bool b) return b ? "true" : "false";
    return value.ToString() ?? "null";
}

static string FormatTypeName(Type type)
{
    try
    {
        if (type.IsByRef)
            return FormatTypeName(type.GetElementType()!);

        // Handle nullable value types
        if (type.IsGenericType && type.GetGenericTypeDefinition().FullName == "System.Nullable`1")
        {
            var inner = type.GetGenericArguments()[0];
            return $"{FormatTypeName(inner)}?";
        }

        // Handle common built-in type aliases
        var alias = type.FullName switch
        {
            "System.String" => "string",
            "System.Int32" => "int",
            "System.Int64" => "long",
            "System.Int16" => "short",
            "System.Boolean" => "bool",
            "System.Double" => "double",
            "System.Single" => "float",
            "System.Decimal" => "decimal",
            "System.Byte" => "byte",
            "System.Char" => "char",
            "System.Object" => "object",
            "System.Void" => "void",
            _ => null
        };
        if (alias != null) return alias;

        // Handle arrays
        if (type.IsArray)
            return $"{FormatTypeName(type.GetElementType()!)}[]";

        // Handle generics
        if (type.IsGenericType)
        {
            string name = type.Name;
            int backtick = name.IndexOf('`');
            if (backtick > 0) name = name[..backtick];
            var gArgs = type.GetGenericArguments().Select(FormatTypeName);
            return $"{name}<{string.Join(", ", gArgs)}>";
        }

        // Use short name
        return type.Name;
    }
    catch
    {
        try { return type.Name; }
        catch { return "<unresolved>"; }
    }
}

static bool IsDelegate(Type type)
{
    return type.IsClass && type.BaseType?.FullName is "System.Delegate" or "System.MulticastDelegate";
}