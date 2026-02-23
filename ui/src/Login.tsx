import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription } from "@/components/ui/alert";

interface LoginProps {
  onLogin: (user: any) => void;
  onGoToRegister: () => void;
  onLookup: () => void;
}

export default function Login({ onLogin, onGoToRegister, onLookup }: LoginProps) {
  const [form, setForm] = useState({ email: "", password: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
    setForm({ ...form, [e.target.name]: e.target.value });
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const res = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data.error || "Login failed.");
      } else {
        onLogin(data.user);
      }
    } catch {
      setError("Network error. Is the server running?");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex">
      {/* Left panel — branding */}
      <div className="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-slate-900 via-blue-950 to-indigo-900 flex-col justify-between p-12 text-white relative overflow-hidden">
        {/* Decorative blobs */}
        <div className="absolute top-0 right-0 w-96 h-96 bg-blue-500/10 rounded-full -translate-y-1/2 translate-x-1/2" />
        <div className="absolute bottom-0 left-0 w-72 h-72 bg-indigo-500/10 rounded-full translate-y-1/2 -translate-x-1/2" />

        {/* Logo */}
        <div className="relative z-10 flex items-center gap-2">
          <div className="w-9 h-9 bg-blue-400 rounded-lg flex items-center justify-center font-bold text-slate-900 text-sm select-none">
            SG
          </div>
          <span className="font-semibold text-lg tracking-tight">Student Grouper</span>
        </div>

        {/* Hero text */}
        <div className="relative z-10 space-y-6">
          <div>
            <h2 className="text-4xl font-bold leading-tight mb-3">
              Organize students<br />effortlessly.
            </h2>
            <p className="text-blue-200 text-base leading-relaxed">
              Auto-assign students into balanced groups for seamless collaboration at Open University of Kenya.
            </p>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="bg-white/10 rounded-xl p-4 backdrop-blur-sm">
              <p className="text-xl font-bold">Auto</p>
              <p className="text-blue-200 text-sm">Group assignment</p>
            </div>
            <div className="bg-white/10 rounded-xl p-4 backdrop-blur-sm">
              <p className="text-xl font-bold">OUK</p>
              <p className="text-blue-200 text-sm">Verified emails only</p>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="relative z-10 text-blue-300/70 text-xs">
          Open University of Kenya — Student Portal
        </div>
      </div>

      {/* Right panel — form */}
      <div className="flex-1 flex items-center justify-center px-6 py-12 bg-white">
        <div className="w-full max-w-md">
          <div className="mb-8">
            <h1 className="text-2xl font-bold text-gray-900">Welcome back</h1>
            <p className="text-gray-500 mt-1 text-sm">Sign in with your OUK email to continue</p>
          </div>

          {error && (
            <Alert variant="destructive" className="mb-6">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            <div className="space-y-1.5">
              <Label htmlFor="email">OUK Email</Label>
              <Input
                id="email"
                name="email"
                type="email"
                placeholder="you@ouk.ac.ke"
                value={form.email}
                onChange={handleChange}
                required
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                name="password"
                type="password"
                placeholder="••••••••"
                value={form.password}
                onChange={handleChange}
                required
              />
            </div>
            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? "Signing in…" : "Sign In"}
            </Button>
          </form>

          <p className="text-center text-sm text-gray-500 mt-6">
            Don't have an account?{" "}
            <button
              type="button"
              onClick={onGoToRegister}
              className="text-primary font-medium hover:underline"
            >
              Create one
            </button>
          </p>

          <p className="text-center text-sm text-gray-500 mt-3">
            <button
              type="button"
              onClick={onLookup}
              className="text-primary font-medium hover:underline"
            >
              Find My Group
            </button>
            {" "}— look up your group without logging in
          </p>
        </div>
      </div>
    </div>
  );
}
