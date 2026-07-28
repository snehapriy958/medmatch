package com.medmatch.auth.metrics;

import org.springframework.stereotype.Service;

import io.micrometer.core.instrument.Counter;
import io.micrometer.core.instrument.MeterRegistry;
import io.micrometer.core.instrument.Timer;

@Service
public class MetricsService {

    private final Counter loginSuccessCounter;
    private final Counter loginFailureCounter;
    private final Counter registrationCounter;
    private final Counter jwtValidationCounter;

    private final Timer loginTimer;

    public MetricsService(MeterRegistry registry) {

        loginSuccessCounter = Counter.builder("medmatch_auth_login_success_total")
                .description("Successful logins")
                .register(registry);

        loginFailureCounter = Counter.builder("medmatch_auth_login_failure_total")
                .description("Failed logins")
                .register(registry);

        registrationCounter = Counter.builder("medmatch_auth_registration_total")
                .description("Registered users")
                .register(registry);

        jwtValidationCounter = Counter.builder("medmatch_auth_jwt_validation_total")
                .description("Validated JWT tokens")
                .register(registry);

        loginTimer = Timer.builder("medmatch_auth_login_duration_seconds")
                .description("Authentication login duration")
                .register(registry);
    }

    public void loginSuccess() {
        loginSuccessCounter.increment();
    }

    public void loginFailure() {
        loginFailureCounter.increment();
    }

    public void registration() {
        registrationCounter.increment();
    }

    public void jwtValidated() {
        jwtValidationCounter.increment();
    }

    public Timer.Sample startLoginTimer() {
        return Timer.start();
    }

    public void stopLoginTimer(Timer.Sample sample) {
        sample.stop(loginTimer);
    }
}