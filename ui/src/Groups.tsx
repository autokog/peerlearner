import { useEffect, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

export default function Groups() {
  const [groups, setGroups] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    fetch("/api/groups")
      .then((r) => r.json())
      .then(setGroups)
      .catch(() => setError("Failed to load groups."))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20 text-muted-foreground text-sm">
        Loading groups…
      </div>
    );
  }

  if (error) {
    return (
      <Alert variant="destructive" className="max-w-lg mx-auto">
        <AlertDescription>{error}</AlertDescription>
      </Alert>
    );
  }

  if (groups.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-center gap-2">
        <p className="text-muted-foreground text-sm">No groups yet.</p>
        <p className="text-muted-foreground text-sm">Register some students to get started.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-lg font-semibold">All Groups</h2>
        <p className="text-sm text-muted-foreground">
          {groups.length} group{groups.length !== 1 ? "s" : ""} &middot;{" "}
          {groups.reduce((sum, g) => sum + g.members.length, 0)} students total
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {groups.map((g) => (
          <Card key={g.id}>
            <CardHeader className="pb-2">
              <CardTitle className="text-base">{g.name}</CardTitle>
              <CardDescription>
                {g.members.length} / 10 members
              </CardDescription>
            </CardHeader>
            <CardContent>
              {g.members.length === 0 ? (
                <p className="text-sm text-muted-foreground italic">No members yet</p>
              ) : (
                <ul className="space-y-1.5">
                  {g.members.map((m: any) => (
                    <li key={m.id} className="flex items-center justify-between text-sm">
                      <span>{m.name}</span>
                      <Badge variant="secondary" className="capitalize text-xs">
                        {m.gender}
                      </Badge>
                    </li>
                  ))}
                </ul>
              )}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
