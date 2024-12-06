-- Create table for testing
CREATE TABLE customers (
  id INT PRIMARY KEY,
  firstName VARCHAR(50),
  lastName VARCHAR(50),
  email VARCHAR(100)
);

-- Insert data for testing
INSERT INTO customers (id, firstName, lastName, email)
VALUES
(1, 'John', 'Doe', 'john.doe@example.com'),
(2, 'Jane', 'Smith', 'jane.smith@example.com'),
(3, 'Mike', 'Johnson', 'mike.johnson@example.com'),
(4, 'Emily', 'Brown', 'emily.brown@example.com');