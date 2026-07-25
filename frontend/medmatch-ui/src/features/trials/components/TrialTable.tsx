import { Eye, Trash2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";


import type { Trial } from "../types/trial";

interface TrialTableProps {
  trials: Trial[];
  isLoading: boolean;
  onView: (id: string) => void;
  onDelete: (id: string) => void;
}

export default function TrialTable({
  trials,
  isLoading,
  onView,
  onDelete,
}: TrialTableProps) {
  if (isLoading) {
    return (
      <Card>
        <CardContent className="py-8 text-center">
          Loading clinical trials...
        </CardContent>
      </Card>
    );
  }

  if (trials.length === 0) {
    return (
      <Card>
        <CardContent className="py-8 text-center text-muted-foreground">
          No clinical trials found.
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Clinical Trials</CardTitle>
      </CardHeader>

      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Title</TableHead>
              <TableHead>Condition</TableHead>
              <TableHead>Phase</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Created</TableHead>
              <TableHead className="text-right">
                Actions
              </TableHead>
            </TableRow>
          </TableHeader>

          <TableBody>
            {trials.map((trial) => (
              <TableRow key={trial.id}>
                <TableCell className="font-medium">
                  {trial.title}
                </TableCell>

                <TableCell>
                  {trial.condition ?? "-"}
                </TableCell>

                <TableCell>
                  {trial.phase ?? "-"}
                </TableCell>

                <TableCell>
                  {trial.status ?? "-"}
                </TableCell>

                <TableCell>
                  {new Date(
                    trial.created_at
                  ).toLocaleDateString()}
                </TableCell>

                <TableCell className="text-right">
                  <div className="flex justify-end gap-2">
                    <Button
                      variant="outline"
                      size="icon"
                      onClick={() => onView(trial.id)}
                    >
                      <Eye />
                    </Button>

                    <Button
                        variant="destructive"
                        size="icon"
                        onClick={() => onDelete(trial.id)}
                    >
                        <Trash2 />
                    </Button>

                  </div>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}