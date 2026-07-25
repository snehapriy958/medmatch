package com.medmatch.auth.config;

import org.springframework.boot.CommandLineRunner;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Component;

import com.medmatch.auth.entity.Hospital;
import com.medmatch.auth.entity.Role;
import com.medmatch.auth.entity.User;
import com.medmatch.auth.repository.HospitalRepository;
import com.medmatch.auth.repository.UserRepository;

@Component
public class DataInitializer implements CommandLineRunner {

    private static final String DEFAULT_HOSPITAL_CODE = "DEFAULT";

    private final HospitalRepository hospitalRepository;
    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;

    public DataInitializer(
            HospitalRepository hospitalRepository,
            UserRepository userRepository,
            PasswordEncoder passwordEncoder
    ) {
        this.hospitalRepository = hospitalRepository;
        this.userRepository = userRepository;
        this.passwordEncoder = passwordEncoder;
    }

    @Override
    public void run(String... args) {

        // ---------------------------------------------------------------------
        // Create Default Hospital
        // ---------------------------------------------------------------------
        Hospital defaultHospital = hospitalRepository
                .findByCode(DEFAULT_HOSPITAL_CODE)
                .orElseGet(() -> {

                    Hospital hospital = new Hospital(
                            DEFAULT_HOSPITAL_CODE,
                            "Default Hospital",
                            "MedMatch Default Organization"
                    );

                    Hospital savedHospital = hospitalRepository.save(hospital);

                    System.out.println("✓ Default hospital created.");

                    return savedHospital;
                });

        // ---------------------------------------------------------------------
        // Create Default Admin User (Only if no users exist)
        // ---------------------------------------------------------------------
        if (userRepository.count() == 0) {

            User admin = new User(
                    "admin",
                    "admin@medmatch.com",
                    passwordEncoder.encode("Admin@123"),
                    Role.ADMIN,
                    defaultHospital
            );

            userRepository.save(admin);

            System.out.println("✓ Default admin user created.");
            System.out.println("----------------------------------------");
            System.out.println("Username : admin");
            System.out.println("Password : Admin@123");
            System.out.println("Role     : ADMIN");
            System.out.println("Hospital : DEFAULT");
            System.out.println("----------------------------------------");

        } else {

            System.out.println("Users already exist. Skipping default admin creation.");
        }
    }
}