import type { ReactNode } from "react";

import { Card, CardContent } from "@/components/ui/card";

interface AuthLayoutProps {
  children: ReactNode;
}

export function AuthLayout({ children }: AuthLayoutProps) {
  return (
    <main className="min-h-screen bg-slate-100">
      <div className="mx-auto flex min-h-screen max-w-7xl items-center justify-center px-6 py-10">
        <div className="grid w-full max-w-6xl overflow-hidden rounded-2xl bg-white shadow-2xl lg:grid-cols-2">
          {/* Branding Panel */}
          <div className="hidden flex-col justify-between bg-gradient-to-br from-blue-700 via-blue-600 to-cyan-500 p-12 text-white lg:flex">
            <div>
              <h1 className="text-4xl font-bold">
                MedMatch
              </h1>

              <p className="mt-4 text-lg text-blue-100">
                AI-Powered Clinical Trial Matching Platform
              </p>
            </div>

            <div className="space-y-4 text-blue-100">
              <p>✓ Secure Authentication</p>
              <p>✓ Multi-Tenant Hospitals</p>
              <p>✓ AI Eligibility Evaluation</p>
              <p>✓ Clinical Trial Search</p>
            </div>
          </div>

          {/* Login Form */}
          <div className="flex items-center justify-center p-8 md:p-12">
            <Card className="w-full border-0 shadow-none">
              <CardContent className="p-0">
                {children}
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </main>
  );
}