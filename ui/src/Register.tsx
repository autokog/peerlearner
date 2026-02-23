import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

interface Course {
  id: string;
  name: string;
}

interface Unit {
  id: string;
  code: string;
  name: string;
}

interface RegisterProps {
  onSuccess: (data: { student: any; group: any }) => void;
}

export default function Register({ onSuccess }: RegisterProps) {
  const [form, setForm] = useState({
    name: "",
    student_id: "",
    gender: "",
    phone: "",
    course_id: "",
  });
  const [selectedUnits, setSelectedUnits] = useState<string[]>([]);
  const [courses, setCourses] = useState<Course[]>([]);
  const [units, setUnits] = useState<Unit[]>([]);
  const [unitsLoading, setUnitsLoading] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetch("/api/courses")
      .then((r) => r.json())
      .then(setCourses)
      .catch(() => setError("Could not load courses. Is the server running?"));
  }, []);

  useEffect(() => {
    if (!form.course_id) {
      setUnits([]);
      setSelectedUnits([]);
      return;
    }
    setUnitsLoading(true);
    fetch(`/api/units?course_id=${form.course_id}`)
      .then((r) => r.json())
      .then((u) => { setUnits(u); setSelectedUnits([]); })
      .catch(() => setError("Could not load units."))
      .finally(() => setUnitsLoading(false));
  }, [form.course_id]);

  function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
    setForm({ ...form, [e.target.name]: e.target.value });
  }

  function toggleUnit(id: string) {
    setSelectedUnits((prev) =>
      prev.includes(id) ? prev.filter((u) => u !== id) : [...prev, id]
    );
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");

    const email = form.student_id.replace(/\//g, "") + "@students.ouk.ac.ke";

    setLoading(true);
    try {
      const res = await fetch("/api/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ...form,
          email,
          unit_ids: selectedUnits,
        }),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data.error || "Registration failed.");
      } else {
        onSuccess(data);
      }
    } catch {
      setError("Network error. Is the server running?");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Card className="max-w-lg">
      <CardHeader>
        <CardTitle>Student Registration</CardTitle>
        <CardDescription>
          Fill in your details and you'll be automatically assigned to a group.
        </CardDescription>
      </CardHeader>
      <CardContent>
        {error && (
          <Alert variant="destructive" className="mb-6">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="name">Full Name</Label>
            <Input
              id="name"
              name="name"
              placeholder="Jane Smith"
              value={form.name}
              onChange={handleChange}
              required
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="student_id">Student ID</Label>
            <Input
              id="student_id"
              name="student_id"
              placeholder="ST03/34403/2025"
              value={form.student_id}
              onChange={handleChange}
              required
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="course_id">Course</Label>
            <Select
              value={form.course_id}
              onValueChange={(val) => setForm({ ...form, course_id: val })}
              required
            >
              <SelectTrigger id="course_id" className="w-full">
                <SelectValue placeholder="Select your course" />
              </SelectTrigger>
              <SelectContent>
                {courses.map((c) => (
                  <SelectItem key={c.id} value={String(c.id)}>
                    {c.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label>Units <span className="text-muted-foreground font-normal">(select all that apply)</span></Label>
            {!form.course_id ? (
              <p className="text-sm text-muted-foreground py-2">Select a course to see available units.</p>
            ) : unitsLoading ? (
              <p className="text-sm text-muted-foreground py-2">Loading units…</p>
            ) : (
              <div className="rounded-md border divide-y max-h-52 overflow-y-auto">
                {units.map((u) => {
                  const checked = selectedUnits.includes(u.id);
                  return (
                    <label
                      key={u.id}
                      className="flex items-center gap-3 px-3 py-2.5 cursor-pointer hover:bg-muted/50 transition-colors"
                    >
                      <input
                        type="checkbox"
                        checked={checked}
                        onChange={() => toggleUnit(u.id)}
                        className="accent-primary h-4 w-4 shrink-0"
                      />
                      <span className="text-sm">
                        <span className="font-medium">{u.code}</span>
                        <span className="text-muted-foreground"> — {u.name}</span>
                      </span>
                    </label>
                  );
                })}
              </div>
            )}
            {selectedUnits.length > 0 && (
              <p className="text-xs text-muted-foreground">{selectedUnits.length} unit{selectedUnits.length !== 1 ? "s" : ""} selected</p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="gender">Gender</Label>
            <Select
              value={form.gender}
              onValueChange={(val) => setForm({ ...form, gender: val })}
              required
            >
              <SelectTrigger id="gender" className="w-full">
                <SelectValue placeholder="Select gender" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="female">Female</SelectItem>
                <SelectItem value="male">Male</SelectItem>
                <SelectItem value="other">Other</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="phone">Phone</Label>
            <Input
              id="phone"
              name="phone"
              type="tel"
              placeholder="+254 700 000000"
              value={form.phone}
              onChange={handleChange}
              required
            />
          </div>

          <Button type="submit" className="w-full" disabled={loading}>
            {loading ? "Registering…" : "Register"}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
