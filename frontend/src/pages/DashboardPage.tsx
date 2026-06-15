import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function DashboardPage() {
  const { user, logout } = useAuth();

  return (
    <div className="page">
      <header className="header">
        <div>
          <h1>Assistente de Pesquisa em Saúde</h1>
          <p>Bem-vindo(a), {user?.full_name}</p>
        </div>
        <div className="header-actions">
          {user?.role === 'admin' && <Link to="/admin" className="btn secondary">Administração</Link>}
          <button onClick={logout} className="btn secondary">Sair</button>
        </div>
      </header>

      <div className="dashboard-grid">
        <Link to="/projects/new" className="dashboard-card">
          <h2>Documento do Projeto</h2>
          <p>
            Documente seu estudo: dados, métodos e saídas esperadas (tabelas, gráficos, modelos).
          </p>
          <span className="card-action">Iniciar assistente →</span>
        </Link>
        <Link to="/cleaning/new" className="dashboard-card">
          <h2>Limpeza de Dados</h2>
          <p>Projete e gere um script data_clean.py com base no esquema do conjunto de dados e nas regras de limpeza.</p>
          <span className="card-action">Iniciar assistente →</span>
        </Link>
      </div>

      <div className="dashboard-links">
        <Link to="/projects">Ver sessões de projeto</Link>
        <Link to="/cleaning">Ver sessões de limpeza</Link>
      </div>
    </div>
  );
}
