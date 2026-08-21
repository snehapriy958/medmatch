package com.medmatch.auth.dto.dashboard;


import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;



@Getter
@Setter
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class SystemHealthResponse {


    /*
     * Authentication service status
     *
     * Example:
     * UP
     * DOWN
     */
    private String authServiceStatus;



    /*
     * AI matching service status
     *
     * FastAPI service
     */
    private String aiServiceStatus;



    /*
     * Database status
     *
     * PostgreSQL + pgvector
     */
    private String databaseStatus;



    /*
     * Redis status
     *
     * Used for:
     * - Cache
     * - Celery broker
     */
    private String redisStatus;



    /*
     * Vector search status
     *
     * Used by:
     * - Embedding retrieval
     * - Trial matching
     */
    private String vectorSearchStatus;



    /*
     * Overall platform status
     *
     * Example:
     * HEALTHY
     * DEGRADED
     */
    private String overallStatus;

}