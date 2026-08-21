import {
  Menu,
  Bell,
  Search,
  LogOut,
  UserRound,
  FlaskConical,
} from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";

import { useAuth } from "../../context/AuthContext";
import { listPatients } from "../../api/patientApi";
import { listTrials } from "../../api/trialApi";

import type { PatientResponse } from "../../types/patient";
import type { TrialResponse } from "../../types/trial";

interface NavbarProps {
  onMenuClick: () => void;
}

export default function Navbar({ onMenuClick }: NavbarProps) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const [searchQuery, setSearchQuery] = useState("");
  const [patients, setPatients] = useState<PatientResponse[]>([]);
  const [trials, setTrials] = useState<TrialResponse[]>([]);
  const [isSearchOpen, setIsSearchOpen] = useState(false);
  const [isLoadingSearch, setIsLoadingSearch] = useState(false);

  const searchRef = useRef<HTMLDivElement>(null);

  const initials = user
    ? `${user.firstName[0]}${user.lastName[0]}`
    : "";

  /*
   * Load patients and trials the first time the user starts searching.
   *
   * The backend currently exposes:
   *   GET /api/patients
   *   GET /api/trials
   *
   * Neither endpoint accepts a search parameter, so filtering is
   * intentionally done on the frontend.
   */
  useEffect(() => {
    const query = searchQuery.trim();

    if (query.length < 2) {
      return;
    }

    let cancelled = false;

    async function loadSearchData() {
      setIsLoadingSearch(true);

      try {
        const [patientResponse, trialResponse] = await Promise.all([
          listPatients(),
          listTrials(),
        ]);

        if (!cancelled) {
          setPatients(patientResponse.patients);
          setTrials(trialResponse);
          setIsSearchOpen(true);
        }
      } catch (error) {
        console.error("Global search failed:", error);

        if (!cancelled) {
          setPatients([]);
          setTrials([]);
          setIsSearchOpen(true);
        }
      } finally {
        if (!cancelled) {
          setIsLoadingSearch(false);
        }
      }
    }

    loadSearchData();

    return () => {
      cancelled = true;
    };
  }, [searchQuery]);

  /*
   * Filter patients and trials locally.
   */
  const searchResults = useMemo(() => {
    const query = searchQuery.trim().toLowerCase();

    if (query.length < 2) {
      return {
        patients: [],
        trials: [],
      };
    }

    const matchedPatients = patients
      .filter((patient) => {
        const searchableText = [
          patient.first_name,
          patient.last_name,
          patient.mrn,
          patient.diagnosis,
          patient.cancer_type,
          patient.stage,
          patient.status,
        ]
          .filter(Boolean)
          .join(" ")
          .toLowerCase();

        return searchableText.includes(query);
      })
      .slice(0, 5);

    const matchedTrials = trials
      .filter((trial) => {
        const criteriaText = trial.criteria
          .map((criterion) => criterion.description)
          .join(" ");

        const searchableText = [
          trial.title,
          trial.brief_summary,
          trial.condition,
          trial.phase,
          trial.status,
          criteriaText,
        ]
          .filter(Boolean)
          .join(" ")
          .toLowerCase();

        return searchableText.includes(query);
      })
      .slice(0, 5);

    return {
      patients: matchedPatients,
      trials: matchedTrials,
    };
  }, [searchQuery, patients, trials]);

  /*
   * Close search dropdown when clicking outside.
   */
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (
        searchRef.current &&
        !searchRef.current.contains(event.target as Node)
      ) {
        setIsSearchOpen(false);
      }
    }

    document.addEventListener("mousedown", handleClickOutside);

    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, []);

  function handleSearchChange(
    event: React.ChangeEvent<HTMLInputElement>
  ) {
    const value = event.target.value;

    setSearchQuery(value);

    if (value.trim().length >= 2) {
      setIsSearchOpen(true);
    } else {
      setIsSearchOpen(false);
    }
  }

  function clearSearch() {
    setSearchQuery("");
    setIsSearchOpen(false);
  }

  function openPatient(patient: PatientResponse) {
    sessionStorage.setItem(
      "medmatch_selected_patient",
      patient.id
    );

    clearSearch();
    navigate("/patients");
  }

  function openTrial(trial: TrialResponse) {
    clearSearch();

    navigate("/trials");

    sessionStorage.setItem(
      "medmatch_selected_trial",
      trial.id
    );
  }

  const hasResults =
    searchResults.patients.length > 0 ||
    searchResults.trials.length > 0;

  return (
    <header className="flex h-16 items-center justify-between border-b border-border bg-surface px-4 md:px-8">
      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={onMenuClick}
          className="text-text-muted md:hidden"
          aria-label="Open navigation menu"
        >
          <Menu size={22} />
        </button>

        {/* GLOBAL SEARCH */}
        <div
          ref={searchRef}
          className="relative hidden md:block"
        >
          <Search
            size={16}
            className="pointer-events-none absolute left-3 top-1/2 z-10 -translate-y-1/2 text-text-muted"
          />

          <input
            id="global-search"
            name="global-search"
            type="search"
            value={searchQuery}
            onChange={handleSearchChange}
            onFocus={() => {
              if (searchQuery.trim().length >= 2) {
                setIsSearchOpen(true);
              }
            }}
            placeholder="Search patients, trials..."
            autoComplete="off"
            aria-label="Search patients and clinical trials"
            className="w-80 rounded-lg border border-border bg-surface py-2 pl-9 pr-3 text-sm text-text placeholder:text-text-muted focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
          />

          {isSearchOpen && (
            <div className="absolute left-0 top-full z-50 mt-2 w-[420px] overflow-hidden rounded-xl border border-border bg-surface shadow-lg">
              {isLoadingSearch ? (
                <div className="px-4 py-5 text-sm text-text-muted">
                  Searching...
                </div>
              ) : !hasResults ? (
                <div className="px-4 py-5">
                  <p className="text-sm font-medium text-text">
                    No results found
                  </p>

                  <p className="mt-1 text-xs text-text-muted">
                    Try searching by patient name, MRN, diagnosis,
                    trial name, condition, or phase.
                  </p>
                </div>
              ) : (
                <div className="max-h-[420px] overflow-y-auto">
                  {/* PATIENT RESULTS */}
                  {searchResults.patients.length > 0 && (
                    <div>
                      <div className="border-b border-border px-4 py-2 text-xs font-semibold uppercase tracking-wide text-text-muted">
                        Patients
                      </div>

                      {searchResults.patients.map((patient) => (
                        <button
                          key={patient.id}
                          type="button"
                          onClick={() => openPatient(patient)}
                          className="flex w-full items-center gap-3 border-b border-border px-4 py-3 text-left transition hover:bg-primary-bg"
                        >
                          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-primary-bg text-primary-dark">
                            <UserRound size={17} />
                          </div>

                          <div className="min-w-0">
                            <p className="truncate text-sm font-medium text-text">
                              {patient.first_name}{" "}
                              {patient.last_name}
                            </p>

                            <p className="truncate text-xs text-text-muted">
                              {patient.mrn}
                              {patient.diagnosis
                                ? ` • ${patient.diagnosis}`
                                : ""}
                            </p>
                          </div>
                        </button>
                      ))}
                    </div>
                  )}

                  {/* TRIAL RESULTS */}
                  {searchResults.trials.length > 0 && (
                    <div>
                      <div className="border-b border-border px-4 py-2 text-xs font-semibold uppercase tracking-wide text-text-muted">
                        Clinical Trials
                      </div>

                      {searchResults.trials.map((trial) => (
                        <button
                          key={trial.id}
                          type="button"
                          onClick={() => openTrial(trial)}
                          className="flex w-full items-center gap-3 border-b border-border px-4 py-3 text-left transition hover:bg-primary-bg"
                        >
                          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-primary-bg text-primary-dark">
                            <FlaskConical size={17} />
                          </div>

                          <div className="min-w-0">
                            <p className="truncate text-sm font-medium text-text">
                              {trial.title}
                            </p>

                            <p className="truncate text-xs text-text-muted">
                              {trial.condition ||
                                trial.phase ||
                                trial.status ||
                                "Clinical trial"}
                            </p>
                          </div>
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      <div className="flex items-center gap-4">
        <button
          type="button"
          className="text-text-muted hover:text-text"
          aria-label="Notifications"
        >
          <Bell size={20} />
        </button>

        <div className="flex items-center gap-2">
          <div
            className="flex h-8 w-8 items-center justify-center rounded-full bg-primary-bg text-xs font-semibold text-primary-dark"
            aria-hidden="true"
          >
            {initials}
          </div>

          <div className="hidden text-sm md:block">
            <p className="font-medium text-text">
              {user?.firstName} {user?.lastName}
            </p>

            <p className="text-xs text-text-muted">
              {user?.role.replaceAll("_", " ")}
            </p>
          </div>
        </div>

        <button
          type="button"
          onClick={logout}
          className="text-text-muted hover:text-status-down"
          title="Log out"
          aria-label="Log out"
        >
          <LogOut size={18} />
        </button>
      </div>
    </header>
  );
}