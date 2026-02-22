import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

interface SuccessProps {
  student: any;
  group: any;
  maxMembers: number;
}

export default function Success({ student, group, maxMembers }: SuccessProps) {
  return (
    <Card className="max-w-lg">
      <CardHeader>
        <div className="flex items-center gap-2 mb-1">
          <span className="text-2xl">🎉</span>
          <CardTitle>Registration Successful!</CardTitle>
        </div>
        <CardDescription>
          Welcome, <span className="font-medium text-foreground">{student.name}</span>! You've
          been assigned to:
        </CardDescription>
      </CardHeader>

      <CardContent className="space-y-4">
        <div className="rounded-lg bg-muted px-4 py-3 text-center">
          <p className="text-xs text-muted-foreground uppercase tracking-wider mb-1">Your group</p>
          <p className="text-2xl font-bold">{group.name}</p>
        </div>

        <div>
          <p className="text-sm font-medium mb-2">
            Group Members{" "}
            <span className="text-muted-foreground font-normal">({group.members.length}/{maxMembers})</span>
          </p>
          <ul className="space-y-2">
            {group.members.map((m: any) => (
              <li
                key={m.id}
                className="flex items-center justify-between rounded-md border px-3 py-2 text-sm"
              >
                <span className={m.student_id === student.student_id ? "font-semibold" : ""}>
                  {m.name}
                  {m.student_id === student.student_id && (
                    <span className="ml-2 text-xs text-muted-foreground">(you)</span>
                  )}
                </span>
                <Badge variant="secondary" className="capitalize">
                  {m.gender}
                </Badge>
              </li>
            ))}
          </ul>
        </div>
      </CardContent>

    </Card>
  );
}
