package com.medmatch.auth.dto;

import java.util.UUID;


public class HospitalResponse {

    private UUID id;

    private String code;

    private String name;

    private String address;


    public HospitalResponse() {
    }


    public HospitalResponse(
            UUID id,
            String code,
            String name,
            String address
    ) {
        this.id = id;
        this.code = code;
        this.name = name;
        this.address = address;
    }


    public UUID getId() {
        return id;
    }


    public String getCode() {
        return code;
    }


    public String getName() {
        return name;
    }


    public String getAddress() {
        return address;
    }
}