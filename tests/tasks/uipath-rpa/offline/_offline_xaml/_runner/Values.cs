using System.Collections;
using System.Data;
using System.Globalization;
using System.Text.Json;
using System.Text.Json.Nodes;

namespace XamlRunner;

// JSON <-> argument values. A DataTable travels as
// {"columns": [{"name": "Amount", "type": "Decimal"}, ...], "rows": [[...], ...]},
// the one shape specs, scenario inputs and outputs all share. A DataRow input is that shape
// with exactly one row.
public static class Values
{
    private static readonly Dictionary<string, Type> ColumnTypes = new(StringComparer.OrdinalIgnoreCase)
    {
        ["String"] = typeof(string),
        ["Int32"] = typeof(int),
        ["Int64"] = typeof(long),
        ["Decimal"] = typeof(decimal),
        ["Double"] = typeof(double),
        ["Boolean"] = typeof(bool),
        ["DateTime"] = typeof(DateTime),
        ["Object"] = typeof(object),
    };

    public static object? FromJson(JsonElement value, Type target)
    {
        if (value.ValueKind == JsonValueKind.Null) return null;
        if (target == typeof(DataTable)) return ToDataTable(value);
        if (target == typeof(DataRow))
        {
            var table = ToDataTable(value);
            if (table.Rows.Count != 1) throw new ArgumentException($"a DataRow takes a table of exactly one row, got {table.Rows.Count}");
            return table.Rows[0];
        }
        if (target == typeof(object)) return Untyped(value);
        return value.Deserialize(target);
    }

    private static object? Untyped(JsonElement value) => value.ValueKind switch
    {
        JsonValueKind.True => true,
        JsonValueKind.False => false,
        JsonValueKind.String => value.GetString(),
        JsonValueKind.Number => value.TryGetInt32(out var i) ? i : value.GetDecimal(),
        JsonValueKind.Array => value.EnumerateArray().Select(Untyped).ToArray(),
        _ => value.GetRawText(),
    };

    private static DataTable ToDataTable(JsonElement value)
    {
        var table = new DataTable();
        foreach (var col in value.GetProperty("columns").EnumerateArray())
        {
            var name = col.ValueKind == JsonValueKind.String ? col.GetString()! : col.GetProperty("name").GetString()!;
            var typeName = col.ValueKind == JsonValueKind.Object && col.TryGetProperty("type", out var t) ? t.GetString()! : "String";
            if (!ColumnTypes.TryGetValue(typeName, out var type)) throw new ArgumentException($"unknown column type {typeName}");
            table.Columns.Add(name, type);
        }
        foreach (var row in value.GetProperty("rows").EnumerateArray())
        {
            var cells = row.EnumerateArray().ToArray();
            if (cells.Length != table.Columns.Count) throw new ArgumentException($"row has {cells.Length} cells, table has {table.Columns.Count} columns");
            table.Rows.Add(cells.Select((c, i) => c.ValueKind == JsonValueKind.Null ? DBNull.Value : c.Deserialize(table.Columns[i].DataType)!).ToArray());
        }
        return table;
    }

    public static JsonNode? ToJson(object? value) => value switch
    {
        null or DBNull => null,
        DataTable table => FromDataTable(table),
        DataRow row => new JsonObject(row.Table.Columns.Cast<DataColumn>().Select(c => KeyValuePair.Create(c.ColumnName, ToJson(row[c])))),
        string s => JsonValue.Create(s),
        bool b => JsonValue.Create(b),
        decimal d => JsonValue.Create(d),
        double d => JsonValue.Create(d),
        float f => JsonValue.Create(f),
        int or long or short or byte => JsonValue.Create(Convert.ToInt64(value, CultureInfo.InvariantCulture)),
        DateTime dt => JsonValue.Create(dt.ToString("o", CultureInfo.InvariantCulture)),
        Exception ex => new JsonObject { ["type"] = ex.GetType().FullName, ["message"] = ex.Message },
        IDictionary dict => new JsonObject(dict.Keys.Cast<object>().Select(k => KeyValuePair.Create(Convert.ToString(k, CultureInfo.InvariantCulture)!, ToJson(dict[k])))),
        IEnumerable seq => new JsonArray(seq.Cast<object?>().Select(ToJson).ToArray()),
        _ => JsonValue.Create(Convert.ToString(value, CultureInfo.InvariantCulture)),
    };

    private static JsonObject FromDataTable(DataTable table) => new()
    {
        ["columns"] = new JsonArray(table.Columns.Cast<DataColumn>()
            .Select(c => (JsonNode)new JsonObject { ["name"] = c.ColumnName, ["type"] = c.DataType.Name }).ToArray()),
        ["rows"] = new JsonArray(table.Rows.Cast<DataRow>()
            .Where(r => r.RowState != DataRowState.Deleted)
            .Select(r => (JsonNode)new JsonArray(r.ItemArray.Select(ToJson).ToArray())).ToArray()),
    };
}
