DELETE FROM roles;


INSERT INTO roles(id, name)
VALUES
(gen_random_uuid(), 'SYSTEM_ADMIN'),
(gen_random_uuid(), 'HOSPITAL_ADMIN'),
(gen_random_uuid(), 'PHYSICIAN'),
(gen_random_uuid(), 'RESEARCH_COORDINATOR'),
(gen_random_uuid(), 'TRIAL_SPONSOR'),
(gen_random_uuid(), 'PATIENT');