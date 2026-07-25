import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

interface DashboardStatCardProps {
  title: string;
  value: number;
}

export function DashboardStatCard({
  title,
  value,
}: DashboardStatCardProps) {
  return (
    <Card className="shadow-sm">
      <CardHeader>
        <CardTitle className="text-sm text-muted-foreground">
          {title}
        </CardTitle>
      </CardHeader>

      <CardContent>
        <p className="text-4xl font-bold">
          {value}
        </p>
      </CardContent>
    </Card>
  );
}