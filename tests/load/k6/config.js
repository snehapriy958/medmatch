export const CONFIG = {
    authUrl: __ENV.AUTH_URL || "http://localhost:8081",
    aiUrl: __ENV.BASE_URL || "http://localhost:8000",

    users: {
        admin: {
            username: __ENV.ADMIN_USERNAME,
            password: __ENV.ADMIN_PASSWORD,
        },

        doctor: {
            username: __ENV.DOCTOR_USERNAME,
            password: __ENV.DOCTOR_PASSWORD,
        },

        researcher: {
            username: __ENV.RESEARCHER_USERNAME,
            password: __ENV.RESEARCHER_PASSWORD,
        },
    },

    headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
    },
};

export const DEFAULT_OPTIONS = {
    vus: 1,
    iterations: 1,

    thresholds: {
        http_req_failed: ["rate<0.01"],

        http_req_duration: [
            "avg<1000",
            "p(95)<2000",
            "p(99)<3000",
        ],
    },
};