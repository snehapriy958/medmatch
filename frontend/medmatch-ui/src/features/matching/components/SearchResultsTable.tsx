import {
  BadgeCheck,
  FlaskConical,
  FileText,
} from "lucide-react";

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

import type { MatchingResult } from "../types/matching";

interface SearchResultsTableProps {
  results: MatchingResult[];
}

export function SearchResultsTable({
  results,
}: SearchResultsTableProps) {
  if (results.length === 0) {
    return (
      <Card className="shadow-sm">
        <CardContent className="flex h-40 items-center justify-center">
          <div className="text-center">
            <h3 className="font-semibold">
              No Matching Trial Criteria
            </h3>

            <p className="mt-2 text-sm text-muted-foreground">
              Evaluate a patient note to retrieve the most
              relevant clinical trial criteria.
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="shadow-sm">
      <CardHeader>
        <CardTitle>
          Retrieved Trial Criteria
        </CardTitle>
      </CardHeader>

      <CardContent>
        <div className="overflow-x-auto rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>
                  Trial
                </TableHead>

                <TableHead>
                  Condition
                </TableHead>

                <TableHead>
                  Phase
                </TableHead>

                <TableHead>
                  Type
                </TableHead>

                <TableHead>
                  Criterion
                </TableHead>

                <TableHead className="text-right">
                  Similarity
                </TableHead>
              </TableRow>
            </TableHeader>

            <TableBody>
              {results.map((result) => {
                const similarity = Math.max(
                  0,
                  (1 - result.distance) * 100
                );

                return (
                  <TableRow key={result.id}>
                    <TableCell className="min-w-[250px]">
                      <div className="space-y-1">
                        <div className="flex items-center gap-2 font-semibold">
                          <FlaskConical className="h-4 w-4 text-blue-600" />
                          {result.title}
                        </div>

                        {result.status && (
                          <div>
                            <BadgeCheck className="mr-1 inline h-3 w-3 text-green-600" />
                            <span className="text-xs text-muted-foreground">
                              {result.status}
                            </span>
                          </div>
                        )}
                      </div>
                    </TableCell>

                    <TableCell>
                      {result.condition ?? "N/A"}
                    </TableCell>

                    <TableCell>
                      {result.phase ?? "N/A"}
                    </TableCell>

                    <TableCell className="capitalize">
                      {result.criteria_type}
                    </TableCell>

                    <TableCell className="min-w-[380px]">
                      <div className="flex gap-2">
                        <FileText className="mt-1 h-4 w-4 flex-shrink-0 text-slate-500" />

                        <span className="text-sm leading-6">
                          {result.description}
                        </span>
                      </div>
                    </TableCell>

                    <TableCell className="text-right font-semibold">
                      {similarity.toFixed(1)}%
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </div>

        <p className="mt-4 text-sm text-muted-foreground">
          Displaying the {results.length} most relevant clinical trial criteria
          retrieved through semantic vector search.
        </p>
      </CardContent>
    </Card>
  );
}