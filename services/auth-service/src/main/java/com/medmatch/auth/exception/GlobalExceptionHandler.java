package com.medmatch.auth.exception;

import java.time.LocalDateTime;

import lombok.AllArgsConstructor;
import lombok.Getter;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;

import org.springframework.security.access.AccessDeniedException;

import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;


@RestControllerAdvice
public class GlobalExceptionHandler {


    @ExceptionHandler(ResourceNotFoundException.class)
    public ResponseEntity<ErrorResponse> handleResourceNotFound(
            ResourceNotFoundException ex
    ) {

        return buildResponse(
                ex.getMessage(),
                HttpStatus.NOT_FOUND
        );
    }



    @ExceptionHandler(EmailAlreadyExistsException.class)
    public ResponseEntity<ErrorResponse> handleEmailAlreadyExists(
            EmailAlreadyExistsException ex
    ) {

        return buildResponse(
                ex.getMessage(),
                HttpStatus.CONFLICT
        );
    }



    @ExceptionHandler(DuplicateResourceException.class)
    public ResponseEntity<ErrorResponse> handleDuplicateResource(
            DuplicateResourceException ex
    ) {

        return buildResponse(
                ex.getMessage(),
                HttpStatus.CONFLICT
        );
    }



    @ExceptionHandler(InvalidCredentialsException.class)
    public ResponseEntity<ErrorResponse> handleInvalidCredentials(
            InvalidCredentialsException ex
    ) {

        return buildResponse(
                ex.getMessage(),
                HttpStatus.UNAUTHORIZED
        );
    }



    @ExceptionHandler(AccessDeniedException.class)
    public ResponseEntity<ErrorResponse> handleAccessDenied(
            AccessDeniedException ex
    ) {

        return buildResponse(
                ex.getMessage(),
                HttpStatus.FORBIDDEN
        );
    }



    @ExceptionHandler(Exception.class)
    public ResponseEntity<ErrorResponse> handleGenericException(
            Exception ex
    ) {

        ex.printStackTrace();

        return buildResponse(
                "An unexpected error occurred",
                HttpStatus.INTERNAL_SERVER_ERROR
        );
    }



    private ResponseEntity<ErrorResponse> buildResponse(
            String message,
            HttpStatus status
    ) {

        ErrorResponse errorResponse =
                new ErrorResponse(
                        message,
                        status.value(),
                        LocalDateTime.now()
                );

        return ResponseEntity
                .status(status)
                .body(errorResponse);
    }



    @Getter
    @AllArgsConstructor
    public static class ErrorResponse {

        private final String message;

        private final int status;

        private final LocalDateTime timestamp;
    }

}