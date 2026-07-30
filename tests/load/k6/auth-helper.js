import http from "k6/http";
import { check } from "k6";

import { CONFIG } from "./config.js";

export function login(role = "admin") {

    const user = CONFIG.users[role];

    if (!user) {
        throw new Error(`Unknown role: ${role}`);
    }

    const response = http.post(
        `${CONFIG.authUrl}/auth/login`,
        JSON.stringify({
            username: user.username,
            password: user.password,
        }),
        {
            headers: CONFIG.headers,
        }
    );

    check(response, {
        "login returned 200": (r) => r.status === 200,
        "token exists": (r) => r.json("accessToken") !== undefined,
    });

    const body = response.json();

    if (!body.accessToken) {
        throw new Error("No JWT token returned.");
    }

    return body.accessToken;
}