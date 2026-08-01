package com.medmatch.auth.filter;

import java.io.IOException;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.slf4j.MDC;
import org.springframework.core.Ordered;
import org.springframework.core.annotation.Order;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;

@Component
@Order(Ordered.LOWEST_PRECEDENCE)
public class RequestLoggingFilter extends OncePerRequestFilter {

    private static final Logger log =
            LoggerFactory.getLogger(RequestLoggingFilter.class);

    @Override
    protected void doFilterInternal(
            HttpServletRequest request,
            HttpServletResponse response,
            FilterChain filterChain
    ) throws ServletException, IOException {


        long start = System.nanoTime();

        try {

            filterChain.doFilter(request, response);

        } finally {

            double duration =
                    (System.nanoTime() - start) / 1_000_000.0;

            String clientIp = request.getHeader("X-Forwarded-For");

            if (clientIp == null || clientIp.isBlank()) {
                clientIp = request.getRemoteAddr();
            }

            log.info(
                    "[{}] {} {} | {} | {} | {} ms",
                    MDC.get("requestId"),
                    request.getMethod(),
                    request.getRequestURI(),
                    response.getStatus(),
                    clientIp,
                    String.format("%.2f", duration)
            );
        }
    }
}