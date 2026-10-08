import { useAuth } from './hooks/useAuth';

export default function App() {
  const { isAuthenticated, isLoading, login, error } = useAuth();

  if (isLoading) return <p>Loading…</p>;
  if (!isAuthenticated) {
    return (
      <main>
        <button onClick={login}>Sign in with UiPath</button>
        {error && <p role="alert">{error}</p>}
      </main>
    );
  }

  return (
    <main>
      <h1>Quotes</h1>
      <p>Signed in. Quote requests will appear here.</p>
    </main>
  );
}
