// Valida o modelo semântico do Power BI (TMDL) com a biblioteca oficial da Microsoft (TOM),
// sem precisar do Power BI Desktop. Roda no CI a cada push.
using Microsoft.AnalysisServices.Tabular;

var pasta = args.Length > 0 ? args[0] : Path.Combine("..", "EnergiaONS.SemanticModel", "definition");
var database = TmdlSerializer.DeserializeDatabaseFromFolder(pasta);
var model = database.Model;
var erros = new List<string>();

foreach (var tabela in model.Tables)
{
    Console.WriteLine($"  tabela {tabela.Name}: {tabela.Columns.Count(c => c.Type == ColumnType.Data)} colunas, {tabela.Measures.Count} medidas");
    if (tabela.Partitions.Count != 1) erros.Add($"{tabela.Name} deveria ter uma partição");
    foreach (var medida in tabela.Measures.Where(m => string.IsNullOrWhiteSpace(m.Expression)))
        erros.Add($"medida {medida.Name} sem expressão");
}

foreach (SingleColumnRelationship r in model.Relationships)
    Console.WriteLine($"  relacionamento {r.FromTable.Name}[{r.FromColumn.Name}] -> {r.ToTable.Name}[{r.ToColumn.Name}]");

var calendario = model.Tables.Find("dCalendario");
if (calendario?.DataCategory != "Time" || !calendario.Columns["data"].IsKey)
    erros.Add("dCalendario precisa estar marcada como tabela de datas (dataCategory Time + coluna chave)");

if (!model.Expressions.Contains("UrlDados")) erros.Add("parâmetro UrlDados não encontrado");

Console.WriteLine($"Modelo {database.Name}: {model.Tables.Count} tabelas, {model.Relationships.Count} relacionamentos, " +
                  $"{model.Tables.Sum(t => t.Measures.Count)} medidas");
if (erros.Count > 0)
{
    erros.ForEach(e => Console.Error.WriteLine($"ERRO: {e}"));
    return 1;
}
Console.WriteLine("TMDL válido.");
return 0;
