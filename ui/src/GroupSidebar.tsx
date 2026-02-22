import { useEffect, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function GroupSidebar() {
  const [groups, setGroups] = useState<any[]>([]);
  const [maxMembers, setMaxMembers] = useState(10);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      fetch("/api/groups").then((r) => r.json()),
      fetch("/api/config").then((r) => r.json()),
    ])
      .then(([g, cfg]) => {
        setGroups(g);
        setMaxMembers(cfg.max_members);
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <div className="text-sm text-muted-foreground py-4">Loading…</div>;
  }

  const totalStudents = groups.reduce((sum, g) => sum + g.members.length, 0);
  const femaleCount = groups.reduce(
    (sum, g) => sum + g.members.filter((m: any) => m.gender === "female").length,
    0
  );
  const maleCount = groups.reduce(
    (sum, g) => sum + g.members.filter((m: any) => m.gender === "male").length,
    0
  );

  return (
    <div className="space-y-4">
      {/* Stats */}
      <div className="grid grid-cols-3 gap-3">
        <Card>
          <CardContent className="pt-4 pb-3 text-center">
            <p className="text-2xl font-bold">{totalStudents}</p>
            <p className="text-xs text-muted-foreground">Enrolled</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4 pb-3 text-center">
            <p className="text-2xl font-bold">{groups.length}</p>
            <p className="text-xs text-muted-foreground">Groups</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4 pb-3 text-center">
            <p className="text-2xl font-bold">
              {femaleCount}
              <span className="text-base font-normal text-muted-foreground">
                /{maleCount}
              </span>
            </p>
            <p className="text-xs text-muted-foreground">F / M</p>
          </CardContent>
        </Card>
      </div>

      {/* Group list */}
      {groups.length === 0 ? (
        <p className="text-sm text-muted-foreground">
          No groups yet — you'll be the first!
        </p>
      ) : (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-semibold">Current Groups</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2.5">
            {groups.map((g) => (
              <div key={g.id} className="space-y-1">
                <div className="flex items-center justify-between text-sm">
                  <span className="font-medium">{g.name}</span>
                  <Badge variant="secondary">{g.members.length} / {maxMembers}</Badge>
                </div>
                <div className="w-full bg-muted rounded-full h-1.5">
                  <div
                    className="bg-primary h-1.5 rounded-full transition-all"
                    style={{ width: `${Math.min((g.members.length / maxMembers) * 100, 100)}%` }}
                  />
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
