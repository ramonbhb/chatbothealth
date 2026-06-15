interface SchemaBrowserProps {
  tables: Array<{
    id: number;
    name: string;
    description: string;
    columns: Array<{
      id: number;
      name: string;
      data_type: string;
      nullable: boolean;
      is_primary_key: boolean;
      is_foreign_key: boolean;
      description: string;
      valid_values: string;
      is_phi: boolean;
    }>;
  }>;
}

export function SchemaBrowser({ tables }: SchemaBrowserProps) {
  if (!tables.length) return <p className="muted">No tables in this dataset.</p>;

  return (
    <div className="schema-browser">
      {tables.map((table) => (
        <details key={table.id} open>
          <summary>
            <strong>{table.name}</strong> — {table.description}
          </summary>
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
        </details>
      ))}
    </div>
  );
}
