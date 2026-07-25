import {
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Brain,
  Target,
  ShieldAlert,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

import type { EligibilityResponse } from "../types/matching";

interface EligibilityCardProps {
  result: EligibilityResponse;
}

export function EligibilityCard({
  result,
}: EligibilityCardProps) {
  const confidence = Math.round(result.confidence * 100);

  const getStatus = () => {
    switch (result.eligibility) {
      case "Eligible":
        return {
          badge: "default" as const,
          icon: <CheckCircle2 className="h-5 w-5 text-green-600" />,
        };

      case "Possibly Eligible":
        return {
          badge: "secondary" as const,
          icon: <AlertTriangle className="h-5 w-5 text-yellow-600" />,
        };

      default:
        return {
          badge: "destructive" as const,
          icon: <XCircle className="h-5 w-5 text-red-600" />,
        };
    }
  };

  const status = getStatus();

  return (
    <Card className="shadow-sm">
      <CardHeader>
        <CardTitle>Eligibility Assessment</CardTitle>
      </CardHeader>

      <CardContent className="space-y-8">
        <div className="flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
          <div className="flex items-center gap-3">
            {status.icon}

            <div>
              <p className="text-sm text-muted-foreground">
                Decision
              </p>

              <Badge
                variant={status.badge}
                className="mt-2"
              >
                {result.eligibility}
              </Badge>
            </div>
          </div>

          <div className="rounded-lg bg-slate-100 px-6 py-4 text-center">
            <p className="text-sm text-muted-foreground">
              Confidence
            </p>

            <p className="mt-2 text-3xl font-bold">
              {confidence}%
            </p>
          </div>
        </div>

        <div className="rounded-lg border p-5">
          <div className="mb-3 flex items-center gap-2">
            <Brain className="h-5 w-5 text-blue-600" />
            <h3 className="font-semibold">AI Reasoning</h3>
          </div>

          <p className="leading-7 text-muted-foreground">
            {result.reasoning}
          </p>
        </div>

        <div className="grid gap-6 lg:grid-cols-2">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-base">
                <Target className="h-5 w-5 text-green-600" />
                Matched Criteria
              </CardTitle>
            </CardHeader>

            <CardContent>
              {result.matched_criteria.length === 0 ? (
                <p className="text-sm text-muted-foreground">
                  No matched criteria.
                </p>
              ) : (
                <ul className="space-y-2">
                  {result.matched_criteria.map((criterion) => (
                    <li
                      key={criterion}
                      className="rounded-md border border-green-200 bg-green-50 p-3 text-sm"
                    >
                      {criterion}
                    </li>
                  ))}
                </ul>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-base">
                <ShieldAlert className="h-5 w-5 text-red-600" />
                Failed Criteria
              </CardTitle>
            </CardHeader>

            <CardContent>
              {result.failed_criteria.length === 0 ? (
                <p className="text-sm text-muted-foreground">
                  No failed criteria.
                </p>
              ) : (
                <ul className="space-y-2">
                  {result.failed_criteria.map((criterion) => (
                    <li
                      key={criterion}
                      className="rounded-md border border-red-200 bg-red-50 p-3 text-sm"
                    >
                      {criterion}
                    </li>
                  ))}
                </ul>
              )}
            </CardContent>
          </Card>
        </div>
      </CardContent>
    </Card>
  );
}