import http from "k6/http";
import { check, sleep } from "k6";

import { CONFIG } from "../config.js";

export const options = {
    stages: [
        { duration: "30s", target: 1 },
        { duration: "30s", target: 10 },
        { duration: "1m", target: 25 },
        { duration: "30s", target: 50 },
        { duration: "30s", target: 0 },
    ],

    thresholds: {
        http_req_failed: ["rate<0.01"],

        http_req_duration: [
            "avg<1000",
            "p(95)<2000",
            "p(99)<3000",
        ],
    },
};

export default function () {

    const response = http.post(
        `${CONFIG.authUrl}/auth/login`,
        JSON.stringify({
            username: CONFIG.users.admin.username,
            password: CONFIG.users.admin.password,
        }),
        {
            headers: CONFIG.headers,
            tags: {
                endpoint: "login",
            },
        }
    );

    check(response, {
        "status is 200": (r) => r.status === 200,
        "JWT returned": (r) => r.json("accessToken") !== undefined,
    });

    sleep(1);
}