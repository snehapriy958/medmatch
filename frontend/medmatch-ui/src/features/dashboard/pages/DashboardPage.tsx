import { DashboardStatCard } from "../components/DashboardStatCard";
import { useDashboard } from "../hooks/useDashboard";

export default function DashboardPage() {
  const {
    data,
    isLoading,
    isError,
  } = useDashboard();

  if (isLoading) {
    return (
      <div className="p-8">
        Loading dashboard...
      </div>
    );
  }

  if (isError || !data) {
    return (
      <div className="p-8 text-red-600">
        Failed to load dashboard.
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <section className="rounded-xl bg-white p-8 shadow-sm">
        <h1 className="text-4xl font-bold">
          Dashboard
        </h1>

        <p className="mt-2 text-muted-foreground">
          Welcome to the MedMatch Clinical Trial Platform.
        </p>
      </section>

      <section className="grid gap-6 md:grid-cols-2">
        <DashboardStatCard
          title="Hospitals"
          value={data.hospitalCount}
        />

        <DashboardStatCard
          title="Users"
          value={data.userCount}
        />
      </section>

      <section className="rounded-xl bg-white p-8 shadow-sm">
        <h2 className="text-2xl font-semibold">
          Platform Overview
        </h2>

        <p className="mt-4 text-muted-foreground">
          Dashboard statistics are loaded
          directly from the Spring Boot
          backend.
        </p>
      </section>
    </div>
  );
}