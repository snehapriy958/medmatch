import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

import type { Patient } from "../types/patient";

interface PatientTableProps {
  patients: Patient[];
  canDelete: boolean;
  onAddNote: (patient: Patient) => void;
  onDelete: (patient: Patient) => void;
}

export function PatientTable({
  patients,
  canDelete,
  onAddNote,
  onDelete,
}: PatientTableProps) {
  if (patients.length === 0) {
    return (
      <div className="rounded-lg border p-8 text-center text-muted-foreground">
        No patients found.
      </div>
    );
  }

  return (
    <div className="rounded-lg border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Name</TableHead>
            <TableHead>Age</TableHead>
            <TableHead>Gender</TableHead>
            <TableHead>Diagnosis</TableHead>
            <TableHead className="w-[220px]">
              Actions
            </TableHead>
          </TableRow>
        </TableHeader>

        <TableBody>
          {patients.map((patient) => (
            <TableRow key={patient.id}>
              <TableCell>{patient.name}</TableCell>

              <TableCell>{patient.age}</TableCell>

              <TableCell>{patient.gender}</TableCell>

              <TableCell>{patient.diagnosis}</TableCell>

              <TableCell className="space-x-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => onAddNote(patient)}
                >
                  Add Note
                </Button>

                {canDelete && (
                  <Button
                    variant="destructive"
                    size="sm"
                    onClick={() => onDelete(patient)}
                  >
                    Delete
                  </Button>
                )}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}