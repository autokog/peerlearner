import { useState } from "react";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

interface Props {
  student: any;
  groups: any[];
  onClose: () => void;
  onMoved: (student: any, group: any) => void;
}

export default function MoveStudentDialog({ student, groups, onClose, onMoved }: Props) {
  const [groupId, setGroupId] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const availableGroups = groups.filter((g) => g.id !== student.group_id);

  async function handleMove() {
    if (!groupId) return;
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`/api/admin/students/${student.id}/move`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ group_id: parseInt(groupId) }),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data.error ?? "Failed to move student.");
        return;
      }
      onMoved(data.student, data.group);
    } catch {
      setError("Network error.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-background rounded-lg border shadow-lg p-6 w-full max-w-sm space-y-4">
        <h2 className="text-base font-semibold">Move Student</h2>
        <p className="text-sm text-muted-foreground">
          Moving <span className="font-medium text-foreground">{student.name}</span> to a new group.
        </p>

        <Select value={groupId} onValueChange={setGroupId}>
          <SelectTrigger className="w-full">
            <SelectValue placeholder="Select a group…" />
          </SelectTrigger>
          <SelectContent>
            {availableGroups.map((g) => (
              <SelectItem key={g.id} value={String(g.id)}>
                {g.name} ({g.members.length} members)
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        {error && <p className="text-sm text-destructive">{error}</p>}

        <div className="flex gap-2 justify-end">
          <Button variant="outline" size="sm" onClick={onClose} disabled={loading}>
            Cancel
          </Button>
          <Button size="sm" onClick={handleMove} disabled={!groupId || loading}>
            {loading ? "Moving…" : "Move"}
          </Button>
        </div>
      </div>
    </div>
  );
}
