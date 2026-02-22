import { useEffect, useState } from "react";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

interface MyGroupProps {
  user: any;
}

export default function MyGroup({ user }: MyGroupProps) {
  const student = user.student;
  const [groupMembers, setGroupMembers] = useState<any[]>([]);
  const [groupName, setGroupName] = useState("");

  useEffect(() => {
    if (!student?.group_id) return;
    fetch("/api/groups")
      .then((r) => r.json())
      .then((groups) => {
        const group = groups.find((g: any) => g.id === student.group_id);
        if (group) {
          setGroupMembers(group.members);
          setGroupName(group.name);
        }
      });
  }, [student?.group_id]);

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
              <CardTitle>{groupName || `Group ${student.group_id}`}</CardTitle>
              <CardDescription>
                {groupMembers.length} member{groupMembers.length !== 1 ? "s" : ""}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ul className="divide-y">
                {groupMembers.map((m: any) => (
                  <li
                    key={m.id}
                    className="flex items-center justify-between py-2.5 text-sm"
                  >
                    <div>
                      <p className="font-medium">
                        {m.name}
                        {m.id === student.id && (
                          <span className="ml-2 text-xs text-muted-foreground">
                            (you)
                          </span>
                        )}
                      </p>
                      <p className="text-muted-foreground text-xs">{m.course}</p>
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
  );
}
