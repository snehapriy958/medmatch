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
                <TableHead className="w-32">
                  Trial ID
                </TableHead>

                <TableHead className="w-40">
                  Criteria Type
                </TableHead>

                <TableHead>
                  Description
                </TableHead>

                <TableHead className="text-right">
                  Distance
                </TableHead>
              </TableRow>
            </TableHeader>

            <TableBody>
              {results.map((result) => (
                <TableRow key={result.id}>
                  <TableCell className="font-mono text-xs">
                    {result.trial_id}
                  </TableCell>

                  <TableCell className="font-medium capitalize">
                    {result.criteria_type}
                  </TableCell>

                  <TableCell className="max-w-xl">
                    <p className="line-clamp-2">
                      {result.description}
                    </p>
                  </TableCell>

                  <TableCell className="text-right font-semibold">
                    {result.distance.toFixed(4)}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>

        <p className="mt-4 text-sm text-muted-foreground">
          Showing the {results.length} most relevant trial
          criteria retrieved through semantic vector search.
        </p>
      </CardContent>
    </Card>
  );
}