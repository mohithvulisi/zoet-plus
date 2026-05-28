import { Shield } from "lucide-react";

export default function Login({ username, password, setUsername, setPassword, onLogin, onToggleMode, error, isSignup }) {
  return (
    <div className="login-shell">
      <div className="login-card">
        <div className="brand-mark"><Shield size={34} /></div>
        <h1>Zoet+</h1>
        <p>{isSignup ? "Create a secure account to join meetings." : "Login with your username and password."}</p>
        <form onSubmit={onLogin}>
          <input value={username} onChange={(e) => setUsername(e.target.value)} placeholder="username" autoFocus autoComplete="username" />
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="password" autoComplete={isSignup ? "new-password" : "current-password"} />
          <button>{isSignup ? "Sign up" : "Login"}</button>
        </form>
        <button type="button" className="ghost" onClick={onToggleMode}>
          {isSignup ? "Already have an account? Log in" : "New here? Create an account"}
        </button>
        {error ? <div className="error">{error}</div> : null}
      </div>
    </div>
  );
}
