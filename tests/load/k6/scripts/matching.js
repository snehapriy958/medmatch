import http from "k6/http";
import { check, sleep } from "k6";
import { Trend } from "k6/metrics";

import { CONFIG } from "../config.js";
import { login } from "../auth-helper.js";

const matchingTime = new Trend("matching_duration");

export const options = {
    stages: [
        { duration: "30s", target: 5 },
        { duration: "1m", target: 20 },
        { duration: "1m", target: 40 },
        { duration: "30s", target: 0 },
    ],

    thresholds: {
        http_req_failed: ["rate<0.01"],
        http_req_duration: ["p(95)<5000"],
    },
};

const note = `
54-year-old male with Stage II colon cancer.
Completed surgery.
ECOG performance status 0.
No liver disease.
Creatinine normal.
No active infection.
`;

export function setup() {

    const token = login("doctor");

    return {
        token,
    };
}

export default function (data) {

    const payload = JSON.stringify({
        patient_note: note,
        limit: 10,
    });

    const response = http.post(
        `${CONFIG.aiUrl}/api/matching/search`,
        payload,
        {
            headers: {
                Authorization: `Bearer ${data.token}`,
                "Content-Type": "application/json",
            },
            tags: {
                endpoint: "matching-search",
                service: "ai-service",
            },
        }
    );

    matchingTime.add(response.timings.duration);

    check(response, {
        "status 200": (r) => {
            if (r.status !== 200) {
                console.log(
                    `Status=${r.status} Body=${r.body}`
                );
            }
            return r.status === 200;
        },

        "response has matches": (r) =>
            r.status === 200 &&
            r.json("matches") !== undefined,
    });

    sleep(1);
}