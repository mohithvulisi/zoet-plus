export const API_URL = import.meta.env.VITE_API_URL || "http://localhost:4000";

export async function api(path, options = {}) {
  const token = localStorage.getItem("zoet_token");
  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {})
  };

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(`${API_URL}${path}`, {
    headers,
    ...options
  });

  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.error || "Request failed");
  return data;
}
