import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../api/client';

export default function AdminPage() {
  const [datasets, setDatasets] = useState<Array<{ id: number; name: string; description: string; enabled: boolean }>>([]);
  const [settings, setSettings] = useState<Array<{ key: string; value: string }>>([]);
  const [audit, setAudit] = useState<Array<Record<string, unknown>>>([]);
  const [selectedDataset, setSelectedDataset] = useState<number | null>(null);
  const [tables, setTables] = useState<Array<Record<string, unknown>>>([]);
  const [newDataset, setNewDataset] = useState({ name: '', description: '' });
  const [newTable, setNewTable] = useState({ name: '', description: '' });
  const [newColumn, setNewColumn] = useState({ tableId: 0, name: '', data_type: 'VARCHAR(255)', description: '' });
  const [error, setError] = useState('');

  const load = async () => {
    try {
      setDatasets(await api.adminDatasets());
      setSettings(await api.listSettings());
      setAudit(await api.listAudit());
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load admin data');
    }
  };

  useEffect(() => { load(); }, []);

  const loadTables = async (datasetId: number) => {
    setSelectedDataset(datasetId);
    setTables(await api.listTables(datasetId));
  };

  return (
    <div className="page admin-page">
      <header className="header">
        <Link to="/">← Dashboard</Link>
        <h1>Admin — Metadata Catalog</h1>
      </header>
      {error && <p className="error">{error}</p>}

      <section className="admin-section">
        <h2>App Settings</h2>
        <table className="schema-table">
          <thead><tr><th>Key</th><th>Value</th><th></th></tr></thead>
          <tbody>
            {settings.map((s) => (
              <tr key={s.key}>
                <td>{s.key}</td>
                <td>
                  <input
                    defaultValue={s.value}
                    onBlur={async (e) => {
                      await api.updateSetting(s.key, e.target.value);
                      load();
                    }}
                  />
                </td>
                <td><small>blur to save</small></td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <section className="admin-section">
        <h2>Datasets</h2>
        <div className="inline-form">
          <input placeholder="Name" value={newDataset.name} onChange={(e) => setNewDataset({ ...newDataset, name: e.target.value })} />
          <input placeholder="Description" value={newDataset.description} onChange={(e) => setNewDataset({ ...newDataset, description: e.target.value })} />
          <button onClick={async () => {
            await api.createDataset({ ...newDataset, enabled: true });
            setNewDataset({ name: '', description: '' });
            load();
          }}>Add Dataset</button>
        </div>
        <ul>
          {datasets.map((d) => (
            <li key={d.id}>
              <button onClick={() => loadTables(d.id)}>{d.name}</button>
              {d.enabled ? ' (enabled)' : ' (disabled)'}
              <button className="btn danger small" onClick={async () => { await api.deleteDataset(d.id); load(); }}>Delete</button>
            </li>
          ))}
        </ul>
      </section>

      {selectedDataset && (
        <section className="admin-section">
          <h2>Tables for Dataset #{selectedDataset}</h2>
          <div className="inline-form">
            <input placeholder="Table name" value={newTable.name} onChange={(e) => setNewTable({ ...newTable, name: e.target.value })} />
            <input placeholder="Description" value={newTable.description} onChange={(e) => setNewTable({ ...newTable, description: e.target.value })} />
            <button onClick={async () => {
              await api.createTable(selectedDataset, newTable);
              setNewTable({ name: '', description: '' });
              loadTables(selectedDataset);
            }}>Add Table</button>
          </div>
          {tables.map((t) => (
            <details key={t.id as number}>
              <summary>{t.name as string}</summary>
              <p>{t.description as string}</p>
              <table className="schema-table">
                <thead><tr><th>Column</th><th>Type</th><th>Description</th><th></th></tr></thead>
                <tbody>
                  {((t.columns as Array<Record<string, unknown>>) || []).map((c) => (
                    <tr key={c.id as number}>
                      <td>{c.name as string}</td>
                      <td>{c.data_type as string}</td>
                      <td>{c.description as string}</td>
                      <td><button className="btn danger small" onClick={async () => {
                        await api.deleteColumn(c.id as number);
                        loadTables(selectedDataset);
                      }}>Delete</button></td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <div className="inline-form">
                <input placeholder="Column name" onChange={(e) => setNewColumn({ ...newColumn, tableId: t.id as number, name: e.target.value })} />
                <input placeholder="Type" value={newColumn.data_type} onChange={(e) => setNewColumn({ ...newColumn, data_type: e.target.value })} />
                <input placeholder="Description" onChange={(e) => setNewColumn({ ...newColumn, tableId: t.id as number, description: e.target.value })} />
                <button onClick={async () => {
                  await api.createColumn(newColumn.tableId, {
                    name: newColumn.name,
                    data_type: newColumn.data_type,
                    description: newColumn.description,
                  });
                  loadTables(selectedDataset);
                }}>Add Column</button>
              </div>
            </details>
          ))}
        </section>
      )}

      <section className="admin-section">
        <h2>Audit Log (recent)</h2>
        <table className="schema-table">
          <thead><tr><th>Time</th><th>User</th><th>Action</th><th>Resource</th></tr></thead>
          <tbody>
            {audit.slice(0, 50).map((log) => (
              <tr key={log.id as number}>
                <td>{String(log.created_at)}</td>
                <td>{String(log.user_id)}</td>
                <td>{String(log.action)}</td>
                <td>{String(log.resource_type)} {String(log.resource_id)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}
