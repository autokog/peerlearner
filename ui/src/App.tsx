import { useEffect, useState } from "react";
import Register from "./Register";
import Success from "./Success";
import MyGroup from "./MyGroup";
import GroupSidebar from "./GroupSidebar";
import Login from "./Login";
import AuthRegister from "./AuthRegister";
import GroupLookup from "./GroupLookup";
import { AdminGroups, AuditLogView } from "./AdminPanel";
import { Button } from "@/components/ui/button"

type View = "register" | "success" | "my-group" | "admin-groups" | "audit-log";
type AuthView = "login" | "signup" | "lookup";

export default function App() {
  const [user, setUser] = useState<any | null>(null);
  const [authChecked, setAuthChecked] = useState(false);
  const [authView, setAuthView] = useState<AuthView>("login");
  const [view, setView] = useState<View>("register");
  const [result, setResult] = useState<{ student: any; group: any } | null>(null);
  const [maxMembers, setMaxMembers] = useState(10);

  useEffect(() => {
    fetch("/api/config")
      .then((r) => r.json())
      .then((cfg) => setMaxMembers(cfg.max_members))
      .catch(() => {});
  }, []);

  useEffect(() => {
    fetch("/api/auth/me")
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => {
        if (data?.user) {
          setUser(data.user);
          if (data.user.student) setView("my-group");
        }
      })
      .finally(() => setAuthChecked(true));
  }, []);

  function handleLogin(loggedInUser: any) {
    setUser(loggedInUser);
    if (loggedInUser.student) setView("my-group");
    else setView("register");
  }

  async function handleLogout() {
    await fetch("/api/auth/logout", { method: "POST" });
    setUser(null);
    setView("register");
    setResult(null);
  }

  function handleSuccess(data: { student: any; group: any }) {
    setResult(data);
    setUser((prev: any) => ({ ...prev, student: data.student }));
    setView("success");
  }

  if (!authChecked) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-muted/40">
        <p className="text-sm text-muted-foreground">Loading…</p>
      </div>
    );
  }

  if (!user) {
    if (authView === "lookup") {
      return (
        <GroupLookup onGoToRegister={() => setAuthView("login")} />
      );
    }
    return authView === "login" ? (
      <Login
        onLogin={handleLogin}
        onGoToRegister={() => setAuthView("signup")}
        onLookup={() => setAuthView("lookup")}
      />
    ) : (
      <AuthRegister onLogin={handleLogin} onGoToLogin={() => setAuthView("login")} />
    );
  }

  const hasLinkedStudent = Boolean(user.student);
  const isAdmin = Boolean(user.is_admin);

  const activeView = hasLinkedStudent && view === "register" ? "my-group" : view;

  function NavButton({ forView, label }: { forView: View; label: string }) {
    return (
      <Button
        variant={view === forView ? "default" : "ghost"}
        size="sm"
        onClick={() => setView(forView)}
      >
        {label}
      </Button>
    );
  }

  const navLinks = (
    <>
      {hasLinkedStudent && <NavButton forView="my-group" label="My Group" />}
      {!hasLinkedStudent && <NavButton forView="register" label="Enroll" />}
      {isAdmin && <NavButton forView="admin-groups" label="Groups" />}
      {isAdmin && <NavButton forView="audit-log" label="Audit Log" />}
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
                {user.email}{isAdmin && <span className="ml-1 text-xs font-medium text-primary">(admin)</span>}
              </span>
              <Button variant="outline" size="sm" onClick={handleLogout}>
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
              <Button variant="outline" size="sm" onClick={handleLogout}>
                Sign Out
              </Button>
            </div>
          </div>
          {/* Mobile: nav below */}
          <nav className="flex gap-2 mt-2 sm:hidden">{navLinks}</nav>
        </div>
      </header>

      <main className="mx-auto max-w-5xl px-6 py-10">
        {activeView === "my-group" && <MyGroup user={user} />}
        {activeView === "register" && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-start">
            <Register onSuccess={handleSuccess} />
            <GroupSidebar />
          </div>
        )}
        {activeView === "success" && result && (
          <Success student={result.student} group={result.group} maxMembers={maxMembers} />
        )}
        {activeView === "admin-groups" && <AdminGroups />}
        {activeView === "audit-log" && <AuditLogView />}
      </main>
    </div>
  );
}
