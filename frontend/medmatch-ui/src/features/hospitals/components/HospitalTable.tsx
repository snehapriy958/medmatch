import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

import { Button } from "@/components/ui/button";
import type { Hospital } from "../types/hospital";

interface HospitalTableProps {
  hospitals: Hospital[];
  onEdit: (hospital: Hospital) => void;
  onDelete: (hospital: Hospital) => void;
}

export function HospitalTable({
  hospitals,
  onEdit,
  onDelete,
}: HospitalTableProps) {
  if (hospitals.length === 0) {
    return (
      <div className="rounded-lg border p-8 text-center text-muted-foreground">
        No hospitals found.
      </div>
    );
  }

  return (
    <div className="rounded-lg border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Code</TableHead>
            <TableHead>Name</TableHead>
            <TableHead>Address</TableHead>
            <TableHead className="w-[180px] text-right">
              Actions
            </TableHead>
          </TableRow>
        </TableHeader>

        <TableBody>
          {hospitals.map((hospital) => (
            <TableRow key={hospital.id}>
              <TableCell className="font-medium">
                {hospital.code}
              </TableCell>

              <TableCell>{hospital.name}</TableCell>

              <TableCell>{hospital.address}</TableCell>

              <TableCell className="space-x-2 text-right">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => onEdit(hospital)}
                >
                  Edit
                </Button>

                <Button
                  variant="destructive"
                  size="sm"
                  onClick={() => onDelete(hospital)}
                >
                  Delete
                </Button>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}