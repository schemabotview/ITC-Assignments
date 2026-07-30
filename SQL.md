## 0. Setup — sample schema & data

```sql
DROP DATABASE IF EXISTS practice;
CREATE DATABASE practice;
USE practice;

CREATE TABLE departments (
    dept_id     INT PRIMARY KEY,
    dept_name   VARCHAR(50) NOT NULL UNIQUE,
    location    VARCHAR(50) DEFAULT 'Hyderabad'
);

CREATE TABLE employees (
    emp_id      INT PRIMARY KEY AUTO_INCREMENT,
    first_name  VARCHAR(50) NOT NULL,
    last_name   VARCHAR(50),
    email       VARCHAR(100) UNIQUE,
    hire_date   DATE NOT NULL,
    salary      DECIMAL(10,2) CHECK (salary > 0),
    manager_id  INT,
    dept_id     INT,
    CONSTRAINT fk_emp_dept    FOREIGN KEY (dept_id)    REFERENCES departments(dept_id),
    CONSTRAINT fk_emp_manager FOREIGN KEY (manager_id) REFERENCES employees(emp_id)
);

CREATE TABLE projects (
    project_id  INT PRIMARY KEY,
    project_name VARCHAR(100) NOT NULL,
    dept_id     INT,
    budget      DECIMAL(12,2),
    FOREIGN KEY (dept_id) REFERENCES departments(dept_id)
);

INSERT INTO departments (dept_id, dept_name, location) VALUES
    (10, 'Engineering', 'Hyderabad'),
    (20, 'Sales',       'Bengaluru'),
    (30, 'HR',          'Pune'),
    (40, 'Finance',     DEFAULT);

INSERT INTO employees
    (first_name, last_name, email, hire_date, salary, manager_id, dept_id) VALUES
    ('Asha',   'Rao',    'asha@corp.com',   '2019-03-01', 120000, NULL, 10),
    ('Bhanu',  'Kumar',  'bhanu@corp.com',  '2020-06-15',  85000, 1,    10),
    ('Chitra', 'Iyer',   'chitra@corp.com', '2021-01-20',  90000, 1,    10),
    ('Deepak', 'Nair',   'deepak@corp.com', '2018-11-05', 110000, NULL, 20),
    ('Esha',   'Verma',  'esha@corp.com',   '2022-07-10',  60000, 4,    20),
    ('Farhan', 'Sheikh', 'farhan@corp.com', '2023-02-28',  55000, 4,    20),
    ('Gita',   'Bose',   'gita@corp.com',   '2020-09-01',  70000, NULL, 30),
    ('Hari',   'Menon',  'hari@corp.com',   '2021-05-12',  48000, 7,    30);

INSERT INTO projects (project_id, project_name, dept_id, budget) VALUES
    (100, 'Data Platform', 10, 500000),
    (101, 'Mobile App',    10, 300000),
    (102, 'CRM Rollout',   20, 250000),
    (103, 'Payroll Sync',  40, 150000);   -- dept 40 has no employees
```

---

## 1. Constraints (PK / FK / NOT NULL / UNIQUE / CHECK / DEFAULT)

```sql
-- PRIMARY KEY: uniquely identifies each row, implies NOT NULL + UNIQUE.
--   -> emp_id in employees, dept_id in departments.

-- FOREIGN KEY: enforces referential integrity between tables.
--   employees.dept_id must exist in departments.dept_id.
-- This INSERT FAILS (dept 99 does not exist):
INSERT INTO employees (first_name, hire_date, dept_id)
VALUES ('Test', '2024-01-01', 99);

-- NOT NULL: value is mandatory. This FAILS (first_name is NOT NULL):
INSERT INTO employees (last_name, hire_date) VALUES ('NoFirst', '2024-01-01');

-- UNIQUE: no duplicate values. This FAILS (email already exists):
INSERT INTO employees (first_name, email, hire_date)
VALUES ('Dup', 'asha@corp.com', '2024-01-01');

-- CHECK: value must satisfy a condition. This FAILS (salary must be > 0):
INSERT INTO employees (first_name, hire_date, salary, dept_id)
VALUES ('Neg', '2024-01-01', -500, 10);

-- DEFAULT: used when no value is supplied (Finance got 'Hyderabad').
SELECT dept_name, location FROM departments WHERE dept_id = 40;

-- Composite PRIMARY KEY (junction table for many-to-many):
CREATE TABLE emp_project (
    emp_id     INT,
    project_id INT,
    role       VARCHAR(40) DEFAULT 'Member',
    PRIMARY KEY (emp_id, project_id),
    FOREIGN KEY (emp_id)     REFERENCES employees(emp_id),
    FOREIGN KEY (project_id) REFERENCES projects(project_id)
);

-- Inspect constraints on a table:
SHOW CREATE TABLE employees;                -- MySQL
-- \d employees                             -- PostgreSQL (psql)
```

---

## 2. Filtering & sorting (WHERE, ORDER BY, LIMIT, conditions)

```sql
-- Basic filter
SELECT first_name, salary FROM employees WHERE dept_id = 10;

-- Comparison + logical operators
SELECT * FROM employees WHERE salary >= 70000 AND dept_id IN (10, 20);

-- Range, set membership, pattern, null checks
SELECT * FROM employees WHERE salary BETWEEN 50000 AND 90000;
SELECT * FROM employees WHERE dept_id IN (10, 30);
SELECT * FROM employees WHERE email LIKE '%@corp.com';
SELECT * FROM employees WHERE first_name LIKE 'A%';     -- starts with A
SELECT * FROM employees WHERE manager_id IS NULL;       -- top-level managers

-- Sorting: multi-column, ascending/descending
SELECT first_name, salary FROM employees ORDER BY dept_id ASC, salary DESC;

-- Top-N with LIMIT (MySQL/Postgres). SQL Server: SELECT TOP 3 ...
SELECT first_name, salary FROM employees ORDER BY salary DESC LIMIT 3;

-- Pagination: skip 2, take 3
SELECT first_name FROM employees ORDER BY emp_id LIMIT 3 OFFSET 2;

-- Conditional expression (CASE)
SELECT first_name, salary,
       CASE WHEN salary >= 100000 THEN 'High'
            WHEN salary >= 70000  THEN 'Mid'
            ELSE 'Entry' END AS band
FROM employees;

-- DISTINCT
SELECT DISTINCT dept_id FROM employees;
```

---

## 3. DELETE vs DROP vs TRUNCATE

```sql
-- DELETE: removes selected rows (DML), can be filtered, is logged, can be rolled back.
DELETE FROM emp_project WHERE role = 'Member';
DELETE FROM emp_project;              -- removes ALL rows (no WHERE), still row-by-row.

-- TRUNCATE: removes ALL rows fast (DDL), resets AUTO_INCREMENT, cannot use WHERE,
-- usually cannot be rolled back. Blocked if referenced by a foreign key.
TRUNCATE TABLE emp_project;

-- DROP: removes the entire table (structure + data + constraints).
DROP TABLE IF EXISTS emp_project;

/* Summary:
   DELETE   -> rows (optional WHERE), DML, rollback-able, keeps table & identity
   TRUNCATE -> all rows, DDL, fast, resets identity, no WHERE
   DROP     -> the whole table definition disappears
*/
```

---

## 4. Aggregate functions & GROUP BY / HAVING

```sql
-- Scalar aggregates over the whole table
SELECT COUNT(*)      AS headcount,
       MIN(salary)   AS min_sal,
       MAX(salary)   AS max_sal,
       AVG(salary)   AS avg_sal,
       SUM(salary)   AS total_payroll
FROM employees;

-- Grouped aggregates: one row per department
SELECT dept_id,
       COUNT(*)            AS emp_count,
       ROUND(AVG(salary))  AS avg_salary,
       MAX(salary)         AS top_salary
FROM employees
GROUP BY dept_id;

-- HAVING filters AFTER grouping (WHERE filters BEFORE)
SELECT dept_id, AVG(salary) AS avg_salary
FROM employees
WHERE hire_date >= '2019-01-01'      -- row filter first
GROUP BY dept_id
HAVING AVG(salary) > 70000           -- group filter after
ORDER BY avg_salary DESC;

-- COUNT of non-null vs all
SELECT COUNT(*) AS all_rows, COUNT(manager_id) AS with_manager FROM employees;

-- Multi-column grouping
SELECT dept_id, YEAR(hire_date) AS hire_year, COUNT(*) AS hires
FROM employees
GROUP BY dept_id, YEAR(hire_date)
ORDER BY dept_id, hire_year;
```

---

## 5. Set operators (UNION, UNION ALL, INTERSECT, EXCEPT)

```sql
-- UNION: combines two result sets, REMOVES duplicates. Columns must match in count/type.
SELECT first_name, dept_id FROM employees WHERE dept_id = 10
UNION
SELECT first_name, dept_id FROM employees WHERE salary > 100000;

-- UNION ALL: keeps duplicates (faster, no de-dup pass).
SELECT dept_id FROM employees
UNION ALL
SELECT dept_id FROM projects;

-- INTERSECT: rows in BOTH (Postgres/SQL Server/Oracle; MySQL 8 lacks it).
-- dept_ids that have both an employee and a project:
SELECT dept_id FROM employees
INTERSECT
SELECT dept_id FROM projects;

-- EXCEPT / MINUS: rows in first but not second.
-- dept_ids with projects but no employees (-> 40):
SELECT dept_id FROM projects
EXCEPT
SELECT dept_id FROM employees;

-- MySQL 8 equivalent of INTERSECT/EXCEPT (no native keyword):
--   INTERSECT -> INNER JOIN or IN (subquery)
--   EXCEPT    -> LEFT JOIN ... WHERE right IS NULL, or NOT IN (subquery)
SELECT DISTINCT p.dept_id FROM projects p
LEFT JOIN employees e ON e.dept_id = p.dept_id
WHERE e.dept_id IS NULL;             -- projects' depts with no employees
```

---
