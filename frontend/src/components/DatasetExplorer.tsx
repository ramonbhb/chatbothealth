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
  if (value === null || value === undefined) return '—';
  return String(value);
}

export function DatasetExplorer({ tables }: DatasetExplorerProps) {
  if (!tables.length) return <p className="muted">No tables in this dataset.</p>;

  return (
    <div className="dataset-explorer">
      {tables.map((table) => {
        const samples = table.sample_rows ?? [];
        const columnNames = table.columns.map((c) => c.name);

        return (
          <details key={table.id} open>
            <summary>
              <strong>{table.name}</strong> — {table.description}
            </summary>

            <h4 className="explorer-subheading">Structure</h4>
            <table className="schema-table">
              <thead>
                <tr>
                  <th>Column</th>
                  <th>Type</th>
                  <th>Keys</th>
                  <th>Description</th>
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
                      {col.valid_values && <small> Values: {col.valid_values}</small>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            <h4 className="explorer-subheading">
              Sample data ({samples.length} of 10 rows)
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
              <p className="muted">No sample rows available for this table.</p>
            )}
          </details>
        );
      })}
    </div>
  );
}
