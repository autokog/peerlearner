import { apiFetch } from "@/lib/api";
import { useEffect, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import MoveStudentDialog from "./MoveStudentDialog";

function WhatsAppLinkEditor({ group, onSaved }: { group: any; onSaved: () => void }) {
  const [link, setLink] = useState(group.whatsapp_link ?? "");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  async function handleSave() {
    setSaving(true);
    setError("");
    const res = await fetch(`/api/admin/groups/${group.id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ whatsapp_link: link }),
    });
    const data = await res.json();
    if (!res.ok) {
      setError(data.error ?? "Save failed.");
    } else {
      onSaved();
    }
    setSaving(false);
  }

  return (
    <div className="mt-3 pt-3 border-t">
      <p className="text-xs text-muted-foreground mb-1.5">WhatsApp Group Link</p>
      <div className="flex gap-2">
        <Input
          value={link}
          onChange={(e: React.ChangeEvent<HTMLInputElement>) => setLink(e.target.value)}
          placeholder="https://chat.whatsapp.com/..."
          className="text-xs h-8"
        />
        <Button size="sm" onClick={handleSave} disabled={saving} className="h-8 shrink-0">
          {saving ? "Saving…" : "Save"}
        </Button>
      </div>
      {error && <p className="text-xs text-destructive mt-1">{error}</p>}
    </div>
  );
}

export function AdminGroups() {
  const [groups, setGroups] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [moving, setMoving] = useState<{ student: any } | null>(null);

  async function loadGroups() {
    const res = await apiFetch("/api/admin/groups");
    if (res.ok) {
      const data = await res.json();
      setGroups(data);
    }
    setLoading(false);
  }

  useEffect(() => { loadGroups(); }, []);

  function handleMoved(_student: any, _group: any) {
    setMoving(null);
    loadGroups();
  }

  if (loading) {
    return (
      <div className="space-y-4">
        {Array.from({ length: 3 }).map((_, i) => (
          <Card key={i}>
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <Skeleton className="h-4 w-24" />
                <Skeleton className="h-5 w-16 rounded-full" />
              </div>
            </CardHeader>
            <CardContent>
              <ul className="divide-y">
                {Array.from({ length: 4 }).map((_, j) => (
                  <li key={j} className="flex items-center justify-between py-1.5">
                    <div className="flex items-center gap-2.5">
                      <Skeleton className="w-7 h-7 rounded-full shrink-0" />
                      <div className="space-y-1.5">
                        <Skeleton className="h-3.5 w-28" />
                        <Skeleton className="h-3 w-36" />
                      </div>
                    </div>
                    <Skeleton className="h-7 w-14 rounded-md" />
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {groups.length === 0 && (
        <p className="text-sm text-muted-foreground">No groups yet.</p>
      )}
      {groups.map((g) => (
        <Card key={g.id}>
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm font-semibold">{g.name}</CardTitle>
              <Badge variant="secondary">{g.members.length} members</Badge>
            </div>
          </CardHeader>
          <CardContent>
            {g.members.length === 0 ? (
              <p className="text-xs text-muted-foreground">No members.</p>
            ) : (
              <ul className="divide-y">
                {g.members.map((s: any) => (
                  <li key={s.id} className="flex items-center justify-between py-1.5">
                    <div className="flex items-center gap-2.5 min-w-0">
                      <img
                        src={s.gravatar_url}
                        alt={s.name}
                        className="w-7 h-7 rounded-full border border-border shrink-0"
                      />
                      <div className="min-w-0">
                        <p className="text-sm font-medium">{s.name}</p>
                        <p className="text-xs text-muted-foreground">
                          {s.student_id} · {s.gender} · {s.course ?? "—"}
                        </p>
                      </div>
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setMoving({ student: s })}
                    >
                      Move
                    </Button>
                  </li>
                ))}
              </ul>
            )}
            <WhatsAppLinkEditor group={g} onSaved={loadGroups} />
          </CardContent>
        </Card>
      ))}

      {moving && (
        <MoveStudentDialog
          student={moving.student}
          groups={groups}
          onClose={() => setMoving(null)}
          onMoved={handleMoved}
        />
      )}
    </div>
  );
}

export function AuditLogView() {
  const [entries, setEntries] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  useEffect(() => {
    setLoading(true);
    apiFetch(`/api/admin/audit-log?page=${page}&per_page=50`)
      .then((r) => r.json())
      .then((data) => {
        setEntries(data.entries ?? []);
        setTotalPages(data.pages ?? 1);
      })
      .finally(() => setLoading(false));
  }, [page]);

  if (loading) {
    return (
      <div className="rounded-md border overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-muted/50">
            <tr>
              {["Time", "User", "Action", "IP", "Method", "Path", "User Agent", "Referrer", "Detail"].map((h) => (
                <th key={h} className="px-3 py-2 text-left font-medium text-muted-foreground">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y">
            {Array.from({ length: 10 }).map((_, i) => (
              <tr key={i}>
                {Array.from({ length: 9 }).map((_, j) => (
                  <td key={j} className="px-3 py-2.5">
                    <Skeleton className="h-3.5" style={{ width: `${50 + ((i + j) * 17) % 50}%` }} />
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {entries.length === 0 && (
        <p className="text-sm text-muted-foreground">No audit log entries yet.</p>
      )}
      {entries.length > 0 && (
        <div className="overflow-x-auto rounded-md border">
          <table className="w-full text-sm">
            <thead className="bg-muted/50">
              <tr>
                <th className="px-3 py-2 text-left font-medium text-muted-foreground">Time</th>
                <th className="px-3 py-2 text-left font-medium text-muted-foreground">User</th>
                <th className="px-3 py-2 text-left font-medium text-muted-foreground">Action</th>
                <th className="px-3 py-2 text-left font-medium text-muted-foreground">IP</th>
                <th className="px-3 py-2 text-left font-medium text-muted-foreground">Method</th>
                <th className="px-3 py-2 text-left font-medium text-muted-foreground">Path</th>
                <th className="px-3 py-2 text-left font-medium text-muted-foreground">User Agent</th>
                <th className="px-3 py-2 text-left font-medium text-muted-foreground">Referrer</th>
                <th className="px-3 py-2 text-left font-medium text-muted-foreground">Detail</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {entries.map((e) => (
                <tr key={e.id} className="hover:bg-muted/30">
                  <td className="px-3 py-2 whitespace-nowrap text-xs text-muted-foreground">
                    {new Date(e.created_at).toLocaleString()}
                  </td>
                  <td className="px-3 py-2 text-xs">{e.user_email ?? "—"}</td>
                  <td className="px-3 py-2">
                    <Badge variant="outline" className="text-xs font-mono">{e.action}</Badge>
                  </td>
                  <td className="px-3 py-2 text-xs text-muted-foreground whitespace-nowrap">{e.ip_address ?? "—"}</td>
                  <td className="px-3 py-2 text-xs font-mono">{e.method ?? "—"}</td>
                  <td className="px-3 py-2 text-xs font-mono text-muted-foreground whitespace-nowrap">{e.path ?? "—"}</td>
                  <td className="px-3 py-2 text-xs text-muted-foreground max-w-[200px]">
                    <span title={e.user_agent ?? ""} className="block truncate">{e.user_agent ?? "—"}</span>
                  </td>
                  <td className="px-3 py-2 text-xs text-muted-foreground max-w-[150px]">
                    <span title={e.referrer ?? ""} className="block truncate">{e.referrer ?? "—"}</span>
                  </td>
                  <td className="px-3 py-2 text-xs text-muted-foreground">
                    {e.detail ? JSON.stringify(e.detail) : "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {totalPages > 1 && (
        <div className="flex items-center gap-2 justify-end">
          <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
            Previous
          </Button>
          <span className="text-xs text-muted-foreground">Page {page} of {totalPages}</span>
          <Button variant="outline" size="sm" disabled={page >= totalPages} onClick={() => setPage((p) => p + 1)}>
            Next
          </Button>
        </div>
      )}
    </div>
  );
}
