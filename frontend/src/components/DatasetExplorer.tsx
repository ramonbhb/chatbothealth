interface TableColumn {
  id: number;
  name: string;
  data_type: string;
  nullable: boolean;
  is_primary_key: boolean;
  is_foreign_key: boolean;
  description: string;
  valid_values: string;
  is_phi: boolean;
}

interface TableData {
  id: number;
  name: string;
  description: string;
  columns: TableColumn[];
  sample_rows?: Array<Record<string, unknown>>;
}

interface DatasetExplorerProps {
  tables: TableData[];
}

function formatCell(value: unknown): string {
  if (value === null || value === undefined) return 'n/d';
  return String(value);
}

export function DatasetExplorer({ tables }: DatasetExplorerProps) {
  if (!tables.length) return <p className="muted">Nenhuma tabela neste conjunto de dados.</p>;

  return (
    <div className="dataset-explorer">
      {tables.map((table) => {
        const samples = table.sample_rows ?? [];
        const columnNames = table.columns.map((c) => c.name);

        return (
          <details key={table.id} open>
            <summary>
              <strong>{table.name}</strong>: {table.description}
            </summary>

            <h4 className="explorer-subheading">Estrutura</h4>
            <table className="schema-table">
              <thead>
                <tr>
                  <th>Coluna</th>
                  <th>Tipo</th>
                  <th>Chaves</th>
                  <th>Descrição</th>
                </tr>
              </thead>
              <tbody>
                {table.columns.map((col) => (
                  <tr key={col.id}>
                    <td>
                      {col.name}
                      {col.is_phi && <span className="phi-badge">PHI</span>}
                    </td>
                    <td>{col.data_type}</td>
                    <td>
                      {col.is_primary_key && 'PK '}
                      {col.is_foreign_key && 'FK '}
                      {!col.nullable && 'NOT NULL'}
                    </td>
                    <td>
                      {col.description}
                      {col.valid_values && <small> Valores: {col.valid_values}</small>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            <h4 className="explorer-subheading">
              Dados de amostra ({samples.length} de 10 linhas)
            </h4>
            {samples.length > 0 ? (
              <div className="sample-table-wrap">
                <table className="schema-table sample-table">
                  <thead>
                    <tr>
                      {columnNames.map((name) => (
                        <th key={name}>{name}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {samples.map((row, rowIndex) => (
                      <tr key={rowIndex}>
                        {columnNames.map((name) => (
                          <td key={name}>{formatCell(row[name])}</td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="muted">Nenhuma linha de amostra disponível para esta tabela.</p>
            )}
          </details>
        );
      })}
    </div>
  );
}
