-- Create database
CREATE DATABASE gov_ai_chatbot;
USE gov_ai_chatbot;

-- =============================================
-- VEHICLE LICENSES TABLE (Simple Format)
-- =============================================
DROP TABLE IF EXISTS vehicle_summons;
DROP TABLE IF EXISTS vehicle_licenses;

CREATE TABLE vehicle_licenses (
  license_id INT AUTO_INCREMENT PRIMARY KEY,
  vehicle_id VARCHAR(20) NOT NULL,
  owner_name VARCHAR(200) NOT NULL,
  ic_number VARCHAR(20) NOT NULL,
  expiry_date DATE NOT NULL,
  renewal_fee DECIMAL(10,2) NOT NULL
);

-- =============================================
-- VEHICLE SUMMONS TABLE (Simple Format)
-- =============================================
CREATE TABLE vehicle_summons (
  summons_id INT AUTO_INCREMENT PRIMARY KEY,
  vehicle_id VARCHAR(20) NOT NULL,
  summons_type VARCHAR(100) NOT NULL,
  summons_date DATE NOT NULL,
  amount DECIMAL(10,2) NOT NULL,
  status VARCHAR(10) DEFAULT 'Unpaid'
);

-- =============================================
-- INSERT VEHICLE DATA
-- =============================================
INSERT INTO vehicle_licenses (vehicle_id, owner_name, ic_number, expiry_date, renewal_fee) VALUES
('W 1234 A','Ahmad Abdullah','900101-01-1234','2026-01-15',90.00),
('W 2345 B','Siti Hassan','900202-03-5678','2026-02-20',60.00),
('W 3456 C','Ali Lee','900303-05-9101','2026-03-25',150.00),
('JEA 123','Syafiq Rahman','901111-21-5261','2026-11-19',150.00),
('JEB 456','Liew Jun','901212-23-7281','2026-12-26',30.00),
('AEA 1234','Goh Hui','910404-08-1123','2027-04-23',30.00),
('AEB 2345','Aminah Salleh','910505-10-3145','2027-05-30',90.00),
('KV 1234','Jason Lim','920707-15-7190','2028-07-06',150.00),
('KV 2345','Rashid Ismail','920808-17-9203','2028-08-13',30.00),
('SA 1234','Aisha Musa','931010-22-3247','2029-12-18',60.00),
('QA 1234','Anita Devi','940303-09-1014','2030-05-22',150.00),
('PAA 176','Farah Nabila','921212-25-7280','2028-12-10',30.00),
('CAA 987','Chia Ming','910909-18-1223','2027-09-27',90.00),
('TAA 9876','Adam Idris','930505-12-3147','2029-06-14',90.00),
('NAA 4321','Gurpreet Singh','940808-19-9205','2030-10-27',30.00);

-- =============================================
-- INSERT SUMMONS DATA
-- =============================================
INSERT INTO vehicle_summons (vehicle_id, summons_type, summons_date, amount, status) VALUES
('W 1234 A','Speeding','2024-01-12',150.00,'Unpaid'),
('W 2345 B','Illegal Parking','2024-01-18',80.00,'Paid'),
('W 3456 C','No Seatbelt','2024-01-25',70.00,'Unpaid'),
('JEA 123','Running Red Light','2024-02-02',200.00,'Unpaid'),
('JEB 456','Expired License','2024-02-08',300.00,'Paid'),
('AEA 1234','Speeding','2024-02-14',120.00,'Unpaid'),
('AEB 2345','Illegal Parking','2024-02-20',90.00,'Paid'),
('KV 1234','Tinted Windows','2024-02-28',250.00,'Unpaid'),
('KV 2345','No Seatbelt','2024-03-05',60.00,'Unpaid'),
('SA 1234','Speeding','2024-03-12',170.00,'Paid'),
('QA 1234','No Helmet','2024-03-19',100.00,'Unpaid'),
('PAA 176','Running Red Light','2024-03-27',200.00,'Paid'),
('CAA 987','Illegal Parking','2024-04-03',85.00,'Unpaid'),
('TAA 9876','Speeding','2024-04-10',150.00,'Unpaid'),
('NAA 4321','Tinted Windows','2024-04-17',240.00,'Paid');
