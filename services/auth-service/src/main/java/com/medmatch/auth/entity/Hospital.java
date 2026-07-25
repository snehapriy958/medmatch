package com.medmatch.auth.entity;

import java.util.UUID;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;


@Entity
@Table(name = "hospitals")
public class Hospital {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;


    @Column(nullable = false, unique = true, length = 50)
    private String code;


    @Column(nullable = false, length = 255)
    private String name;


    @Column(length = 500)
    private String address;


    public Hospital() {
    }


    public Hospital(
            String code,
            String name,
            String address
    ) {
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


    public void setCode(String code) {
        this.code = code;
    }


    public String getName() {
        return name;
    }


    public void setName(String name) {
        this.name = name;
    }


    public String getAddress() {
        return address;
    }


    public void setAddress(String address) {
        this.address = address;
    }
}