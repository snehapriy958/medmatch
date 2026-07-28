import {
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Brain,
  Target,
  ShieldAlert,
  FileText,
  ClipboardList,
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
          icon: (
            <CheckCircle2 className="h-5 w-5 text-green-600" />
          ),
        };

      case "Possibly Eligible":
        return {
          badge: "secondary" as const,
          icon: (
            <AlertTriangle className="h-5 w-5 text-yellow-600" />
          ),
        };

      default:
        return {
          badge: "destructive" as const,
          icon: (
            <XCircle className="h-5 w-5 text-red-600" />
          ),
        };
    }
  };

  const status = getStatus();

  return (
    <Card className="shadow-sm">
      <CardHeader>
        <CardTitle>
          Eligibility Assessment
        </CardTitle>
      </CardHeader>

      <CardContent className="space-y-8">

        {/* Decision */}
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

        {/* Summary */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-base">
              <FileText className="h-5 w-5 text-blue-600" />
              Clinical Summary
            </CardTitle>
          </CardHeader>

          <CardContent>
            <p className="leading-7 text-muted-foreground">
              {result.summary}
            </p>
          </CardContent>
        </Card>

        {/* Reasoning */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-base">
              <Brain className="h-5 w-5 text-blue-600" />
              AI Clinical Reasoning
            </CardTitle>
          </CardHeader>

          <CardContent>
            <p className="leading-7 text-muted-foreground">
              {result.reasoning}
            </p>
          </CardContent>
        </Card>

        {/* Inclusion */}
        <div className="grid gap-6 lg:grid-cols-2">

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-base">
                <Target className="h-5 w-5 text-green-600" />
                Matched Inclusion Criteria
              </CardTitle>
            </CardHeader>

            <CardContent>
              {result.matched_inclusion.length === 0 ? (
                <p className="text-sm text-muted-foreground">
                  No matched inclusion criteria.
                </p>
              ) : (
                <ul className="space-y-2">
                  {result.matched_inclusion.map(
                    (criterion) => (
                      <li
                        key={criterion}
                        className="rounded-md border border-green-200 bg-green-50 p-3 text-sm"
                      >
                        {criterion}
                      </li>
                    )
                  )}
                </ul>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-base">
                <ShieldAlert className="h-5 w-5 text-red-600" />
                Failed Inclusion Criteria
              </CardTitle>
            </CardHeader>

            <CardContent>
              {result.failed_inclusion.length === 0 ? (
                <p className="text-sm text-muted-foreground">
                  No failed inclusion criteria.
                </p>
              ) : (
                <ul className="space-y-2">
                  {result.failed_inclusion.map(
                    (criterion) => (
                      <li
                        key={criterion}
                        className="rounded-md border border-red-200 bg-red-50 p-3 text-sm"
                      >
                        {criterion}
                      </li>
                    )
                  )}
                </ul>
              )}
            </CardContent>
          </Card>

        </div>

        {/* Exclusion */}
        <div className="grid gap-6 lg:grid-cols-2">

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base">
                Satisfied Exclusion Criteria
              </CardTitle>
            </CardHeader>

            <CardContent>
              {result.satisfied_exclusion.length === 0 ? (
                <p className="text-sm text-muted-foreground">
                  None
                </p>
              ) : (
                <ul className="space-y-2">
                  {result.satisfied_exclusion.map(
                    (criterion) => (
                      <li
                        key={criterion}
                        className="rounded-md border border-green-200 bg-green-50 p-3 text-sm"
                      >
                        {criterion}
                      </li>
                    )
                  )}
                </ul>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base">
                Triggered Exclusion Criteria
              </CardTitle>
            </CardHeader>

            <CardContent>
              {result.triggered_exclusion.length === 0 ? (
                <p className="text-sm text-muted-foreground">
                  None
                </p>
              ) : (
                <ul className="space-y-2">
                  {result.triggered_exclusion.map(
                    (criterion) => (
                      <li
                        key={criterion}
                        className="rounded-md border border-red-200 bg-red-50 p-3 text-sm"
                      >
                        {criterion}
                      </li>
                    )
                  )}
                </ul>
              )}
            </CardContent>
          </Card>

        </div>

        {/* Missing Information */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <ClipboardList className="h-5 w-5 text-amber-600" />
              Missing Information
            </CardTitle>
          </CardHeader>

          <CardContent>
            {result.missing_information.length === 0 ? (
              <p className="text-sm text-muted-foreground">
                No additional information required.
              </p>
            ) : (
              <ul className="space-y-2">
                {result.missing_information.map(
                  (item) => (
                    <li
                      key={item}
                      className="rounded-md border border-yellow-200 bg-yellow-50 p-3 text-sm"
                    >
                      {item}
                    </li>
                  )
                )}
              </ul>
            )}
          </CardContent>
        </Card>

        {/* Recommendation */}
        <Card>
          <CardHeader>
            <CardTitle>
              Recommendation
            </CardTitle>
          </CardHeader>

          <CardContent>
            <p className="leading-7 text-muted-foreground">
              {result.recommendation}
            </p>
          </CardContent>
        </Card>

      </CardContent>
    </Card>
  );
}