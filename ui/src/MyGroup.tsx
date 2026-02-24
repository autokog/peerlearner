import { apiFetch } from "@/lib/api";
import { useEffect, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Skeleton } from "@/components/ui/skeleton";

interface MyGroupProps {
  user: any;
}

export default function MyGroup({ user }: MyGroupProps) {
  const student = user.student;
  const [groupMembers, setGroupMembers] = useState<any[]>([]);
  const [groupName, setGroupName] = useState("");
  const [whatsappLink, setWhatsappLink] = useState<string | null>(null);
  const [loading, setLoading] = useState(Boolean(student?.group_id));
  const [allGroups, setAllGroups] = useState<any[]>([]);
  const [switchOpen, setSwitchOpen] = useState(false);
  const [selectedGroupId, setSelectedGroupId] = useState<string | null>(null);
  const [switching, setSwitching] = useState(false);
  const [switchError, setSwitchError] = useState("");

  function loadGroups() {
    if (!student?.group_id) return;
    setLoading(true);
    apiFetch("/api/groups")
      .then((r) => r.json())
      .then((groups) => {
        setAllGroups(groups);
        const group = groups.find((g: any) => g.id === student.group_id);
        if (group) {
          setGroupMembers(group.members);
          setGroupName(group.name);
          setWhatsappLink(group.whatsapp_link ?? null);
        }
      })
      .finally(() => setLoading(false));
  }

  useEffect(() => { loadGroups(); }, [student?.group_id]);

  async function handleSwitch() {
    if (!selectedGroupId) return;
    setSwitching(true);
    setSwitchError("");
    try {
      const res = await apiFetch("/api/student/switch-group", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ group_id: selectedGroupId }),
      });
      const data = await res.json();
      if (!res.ok) {
        setSwitchError(data.error ?? "Failed to switch group.");
      } else {
        student.group_id = data.student.group_id;
        setSwitchOpen(false);
        setSelectedGroupId(null);
        loadGroups();
      }
    } catch {
      setSwitchError("Network error. Please try again.");
    } finally {
      setSwitching(false);
    }
  }

  const sharedUnits = groupMembers.length > 1
    ? groupMembers.slice(1).reduce(
        (common, m) => {
          const memberUnitIds = new Set((m.units ?? []).map((u: any) => u.id));
          return common.filter((u: any) => memberUnitIds.has(u.id));
        },
        [...(groupMembers[0]?.units ?? [])]
      )
    : (groupMembers[0]?.units ?? []);

  if (!student) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-center gap-2">
        <p className="text-muted-foreground text-sm">
          Your account isn't linked to a student record yet.
        </p>
        <p className="text-muted-foreground text-sm">
          Ask a coordinator to register you using{" "}
          <span className="font-medium text-foreground">{user.email}</span>.
        </p>
      </div>
    );
  }

  return (
    <>
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-start">
      {/* Left — student info + units */}
      <div className="space-y-4">
        <Card>
          <CardHeader>
            <CardTitle>{student.name}</CardTitle>
            <CardDescription>{student.student_id}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Course</span>
              <span className="font-medium text-right max-w-[60%]">
                {student.course ?? "—"}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Email</span>
              <span>{student.email}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Phone</span>
              <span>{student.phone}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Gender</span>
              <Badge variant="secondary" className="capitalize">
                {student.gender}
              </Badge>
            </div>
          </CardContent>
        </Card>

        {student.units?.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Enrolled Units</CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-1.5">
                {student.units.map((u: any) => (
                  <li key={u.id} className="flex items-center gap-2 text-sm">
                    <Badge variant="outline">{u.code}</Badge>
                    <span>{u.name}</span>
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Right — group members */}
      <div>
        {student.group_id ? (
          <Card>
            <CardHeader>
              <div className="flex items-start justify-between gap-2">
                <div>
                  <CardTitle>
                    {loading ? <Skeleton className="h-5 w-32" /> : groupName}
                  </CardTitle>
                  <CardDescription className="mt-1">
                    {loading ? <Skeleton className="h-4 w-20" /> : `${groupMembers.length} member${groupMembers.length !== 1 ? "s" : ""}`}
                  </CardDescription>
                </div>
                {!loading && (
                  <Button variant="outline" size="sm" className="shrink-0" onClick={() => { setSelectedGroupId(null); setSwitchError(""); setSwitchOpen(true); }}>
                    Switch Group
                  </Button>
                )}
              </div>
              {!loading && whatsappLink && (
                <a
                  href={whatsappLink}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center justify-center gap-2 w-full px-4 py-2.5 rounded-md bg-green-500 hover:bg-green-600 text-white text-sm font-medium transition-colors"
                >
                  <svg viewBox="0 0 24 24" className="w-4 h-4 fill-current" xmlns="http://www.w3.org/2000/svg">
                    <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/>
                  </svg>
                  Join WhatsApp Group
                </a>
              )}
            </CardHeader>
            <CardContent>
              <ul className="divide-y">
                {loading
                  ? Array.from({ length: 4 }).map((_, i) => (
                      <li key={i} className="flex items-center justify-between py-2.5">
                        <div className="flex items-center gap-2.5">
                          <Skeleton className="w-8 h-8 rounded-full shrink-0" />
                          <div className="space-y-1.5">
                            <Skeleton className="h-3.5 w-28" />
                            <Skeleton className="h-3 w-20" />
                          </div>
                        </div>
                        <Skeleton className="h-5 w-12 rounded-full" />
                      </li>
                    ))
                  : groupMembers.map((m: any) => (
                      <li
                        key={m.id}
                        className="flex items-center justify-between py-2.5 text-sm"
                      >
                        <div className="flex items-center gap-2.5 min-w-0">
                          <img
                            src={m.gravatar_url}
                            alt={m.name}
                            className="w-8 h-8 rounded-full border border-border shrink-0"
                          />
                          <div className="min-w-0">
                            <p className="font-medium">
                              {m.name}
                              {m.id === student.id && (
                                <span className="ml-2 text-xs text-muted-foreground">
                                  (you)
                                </span>
                              )}
                            </p>
                            <p className="text-muted-foreground text-xs truncate">{m.course}</p>
                          </div>
                        </div>
                        <Badge
                          variant={m.id === student.id ? "default" : "secondary"}
                          className="capitalize"
                        >
                          {m.gender}
                        </Badge>
                      </li>
                    ))}
              </ul>
              {sharedUnits.length > 0 && (
                <div className="mt-4 pt-4 border-t">
                  <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-2">
                    Shared Units
                  </p>
                  <ul className="space-y-1.5">
                    {sharedUnits.map((u: any) => (
                      <li key={u.id} className="flex items-center gap-2 text-sm">
                        <Badge variant="outline">{u.code}</Badge>
                        <span>{u.name}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </CardContent>
          </Card>
        ) : (
          <Card>
            <CardContent className="py-4 text-sm text-muted-foreground">
              You haven't been assigned to a group yet.
            </CardContent>
          </Card>
        )}
      </div>
    </div>

    <Dialog open={switchOpen} onOpenChange={setSwitchOpen}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Switch Group</DialogTitle>
        </DialogHeader>
        <div className="space-y-2 max-h-80 overflow-y-auto pr-1">
          {allGroups
            .filter((g) => g.id !== student.group_id)
            .map((g) => {
              const full = g.members.length >= 10;
              const selected = selectedGroupId === g.id;
              return (
                <button
                  key={g.id}
                  disabled={full}
                  onClick={() => setSelectedGroupId(g.id)}
                  className={`w-full text-left px-4 py-3 rounded-md border text-sm transition-colors
                    ${full ? "opacity-40 cursor-not-allowed bg-muted" : "hover:bg-muted cursor-pointer"}
                    ${selected ? "border-primary bg-primary/5" : "border-border"}`}
                >
                  <span className="font-medium">{g.name}</span>
                  <span className="ml-2 text-muted-foreground">
                    {g.members.length} member{g.members.length !== 1 ? "s" : ""}
                    {full && " · Full"}
                  </span>
                </button>
              );
            })}
        </div>
        {switchError && (
          <p className="text-sm text-destructive">{switchError}</p>
        )}
        <DialogFooter>
          <Button variant="outline" onClick={() => setSwitchOpen(false)}>Cancel</Button>
          <Button disabled={!selectedGroupId || switching} onClick={handleSwitch}>
            {switching ? "Switching…" : "Confirm Switch"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
    </>
  );
}
