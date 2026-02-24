import { apiFetch } from "@/lib/api";
import { useEffect, useState } from "react";
import { Routes, Route, Navigate, useNavigate, useLocation, Outlet } from "react-router-dom";
import Register from "./Register";
import Success from "./Success";
import MyGroup from "./MyGroup";
import GroupSidebar from "./GroupSidebar";
import Login from "./Login";
import AuthRegister from "./AuthRegister";
import GroupLookup from "./GroupLookup";
import { AdminGroups, AuditLogView } from "./AdminPanel";
import { Button } from "@/components/ui/button";

function AppLayout({ user, onLogout }: { user: any; onLogout: () => void }) {
  const navigate = useNavigate();
  const location = useLocation();
  const hasLinkedStudent = Boolean(user.student);
  const isAdmin = Boolean(user.is_admin);

  function NavBtn({ to, label }: { to: string; label: string }) {
    return (
      <Button
        variant={location.pathname === to ? "default" : "ghost"}
        size="sm"
        onClick={() => navigate(to)}
      >
        {label}
      </Button>
    );
  }

  const navLinks = (
    <>
      {hasLinkedStudent && <NavBtn to="/my-group" label="My Group" />}
      {!hasLinkedStudent && <NavBtn to="/enroll" label="Enroll" />}
      {isAdmin && <NavBtn to="/admin/groups" label="Groups" />}
      {isAdmin && <NavBtn to="/admin/audit-log" label="Audit Log" />}
    </>
  );

  return (
    <div className="min-h-screen bg-muted/40">
      <header className="border-b bg-background">
        <div className="mx-auto max-w-5xl px-6 py-3">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-xl font-bold tracking-tight">Student Grouper</h1>
              <p className="text-xs text-muted-foreground">Auto-assign students to groups</p>
            </div>
            {/* Desktop */}
            <div className="hidden sm:flex items-center gap-3">
              <nav className="flex gap-2">{navLinks}</nav>
              <div className="h-4 w-px bg-border" />
              <img
                src={user.gravatar_url}
                alt={user.email}
                title={user.email}
                className="w-8 h-8 rounded-full border border-border"
              />
              <span className="text-sm text-muted-foreground">
                {user.email}
                {isAdmin && <span className="ml-1 text-xs font-medium text-primary">(admin)</span>}
              </span>
              <Button variant="outline" size="sm" onClick={onLogout}>
                Sign Out
              </Button>
            </div>
            {/* Mobile: avatar + sign out */}
            <div className="flex sm:hidden items-center gap-2">
              <img
                src={user.gravatar_url}
                alt={user.email}
                title={user.email}
                className="w-8 h-8 rounded-full border border-border"
              />
              <Button variant="outline" size="sm" onClick={onLogout}>
                Sign Out
              </Button>
            </div>
          </div>
          {/* Mobile: nav below header */}
          <nav className="flex gap-2 mt-2 sm:hidden">{navLinks}</nav>
        </div>
      </header>

      <main className="mx-auto max-w-5xl px-6 py-10">
        <Outlet />
      </main>
    </div>
  );
}

export default function App() {
  const [user, setUser] = useState<any | null>(null);
  const [authChecked, setAuthChecked] = useState(false);
  const [result, setResult] = useState<{ student: any; group: any } | null>(null);
  const [maxMembers, setMaxMembers] = useState(10);
  const navigate = useNavigate();

  useEffect(() => {
    apiFetch("/api/config")
      .then((r) => r.json())
      .then((cfg) => setMaxMembers(cfg.max_members))
      .catch(() => {});
  }, []);

  useEffect(() => {
    apiFetch("/api/auth/me")
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => {
        if (data?.user) setUser(data.user);
      })
      .finally(() => setAuthChecked(true));
  }, []);

  function handleLogin(loggedInUser: any) {
    setUser(loggedInUser);
    navigate(loggedInUser.student ? "/my-group" : "/enroll");
  }

  async function handleLogout() {
    await apiFetch("/api/auth/logout", { method: "POST" });
    setUser(null);
    setResult(null);
    navigate("/login");
  }

  function handleSuccess(data: { student: any; group: any }) {
    setResult(data);
    setUser((prev: any) => ({ ...prev, student: data.student }));
    navigate("/success");
  }

  if (!authChecked) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-muted/40">
        <p className="text-sm text-muted-foreground">Loading…</p>
      </div>
    );
  }

  const defaultRedirect = !user ? "/login" : user.student ? "/my-group" : "/enroll";

  return (
    <Routes>
      {/* Public routes */}
      <Route
        path="/login"
        element={
          user ? (
            <Navigate to={defaultRedirect} replace />
          ) : (
            <Login
              onLogin={handleLogin}
              onGoToRegister={() => navigate("/signup")}
              onLookup={() => navigate("/lookup")}
            />
          )
        }
      />
      <Route
        path="/signup"
        element={
          user ? (
            <Navigate to={defaultRedirect} replace />
          ) : (
            <AuthRegister onLogin={handleLogin} onGoToLogin={() => navigate("/login")} />
          )
        }
      />
      <Route
        path="/lookup"
        element={<GroupLookup onGoToRegister={() => navigate("/login")} />}
      />

      {/* Authenticated routes with shared layout */}
      <Route
        element={
          user ? (
            <AppLayout user={user} onLogout={handleLogout} />
          ) : (
            <Navigate to="/login" replace />
          )
        }
      >
        <Route
          path="/enroll"
          element={
            user?.student ? (
              <Navigate to="/my-group" replace />
            ) : (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-start">
                <Register onSuccess={handleSuccess} />
                <GroupSidebar />
              </div>
            )
          }
        />
        <Route
          path="/success"
          element={
            result ? (
              <Success student={result.student} group={result.group} maxMembers={maxMembers} />
            ) : (
              <Navigate to={user?.student ? "/my-group" : "/enroll"} replace />
            )
          }
        />
        <Route path="/my-group" element={<MyGroup user={user} />} />
        <Route
          path="/admin/groups"
          element={user?.is_admin ? <AdminGroups /> : <Navigate to={defaultRedirect} replace />}
        />
        <Route
          path="/admin/audit-log"
          element={user?.is_admin ? <AuditLogView /> : <Navigate to={defaultRedirect} replace />}
        />
      </Route>

      {/* Catch-all redirect */}
      <Route path="*" element={<Navigate to={defaultRedirect} replace />} />
    </Routes>
  );
}
