# SQL Practice Queries

A self-contained set of practice queries covering constraints, DML/DDL, filtering,
aggregation, set operators, joins, window functions, CTEs, views, stored procedures,
sub-queries, and triggers.

> Dialect note: examples target **MySQL 8+** (works largely the same on PostgreSQL).
> Where a feature differs, a note is added. Run the **Setup** block first.

---

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

## 6. ALTER TABLE (DDL modifications)

```sql
-- Add a column
ALTER TABLE employees ADD COLUMN phone VARCHAR(15);

-- Modify a column's type/size (MySQL). Postgres: ALTER COLUMN ... TYPE ...
ALTER TABLE employees MODIFY COLUMN phone VARCHAR(20);

-- Rename a column (MySQL 8 / Postgres)
ALTER TABLE employees RENAME COLUMN phone TO contact_no;

-- Set / drop a DEFAULT
ALTER TABLE employees ALTER COLUMN contact_no SET DEFAULT 'N/A';
ALTER TABLE employees ALTER COLUMN contact_no DROP DEFAULT;

-- Add a constraint after creation
ALTER TABLE employees ADD CONSTRAINT chk_salary_cap CHECK (salary <= 1000000);
ALTER TABLE departments ADD CONSTRAINT uq_loc UNIQUE (dept_name, location);

-- Add an index
CREATE INDEX idx_emp_dept ON employees(dept_id);

-- Drop a column / constraint / index
ALTER TABLE employees DROP COLUMN contact_no;
ALTER TABLE employees DROP CONSTRAINT chk_salary_cap;   -- MySQL 8+/Postgres
DROP INDEX idx_emp_dept ON employees;                   -- MySQL
```

---

## 7. Joins

```sql
-- INNER JOIN: only matching rows in both tables
SELECT e.first_name, d.dept_name
FROM employees e
INNER JOIN departments d ON e.dept_id = d.dept_id;

-- LEFT (OUTER) JOIN: all employees, dept if any (keeps unmatched left rows)
SELECT e.first_name, d.dept_name
FROM employees e
LEFT JOIN departments d ON e.dept_id = d.dept_id;

-- RIGHT JOIN: all departments, even those with no employees (-> Finance)
SELECT d.dept_name, e.first_name
FROM employees e
RIGHT JOIN departments d ON e.dept_id = d.dept_id;

-- FULL OUTER JOIN (Postgres/SQL Server). MySQL: emulate with LEFT UNION RIGHT.
SELECT e.first_name, d.dept_name
FROM employees e
LEFT JOIN departments d ON e.dept_id = d.dept_id
UNION
SELECT e.first_name, d.dept_name
FROM employees e
RIGHT JOIN departments d ON e.dept_id = d.dept_id;

-- SELF JOIN: match employees to their managers
SELECT e.first_name AS employee, m.first_name AS manager
FROM employees e
LEFT JOIN employees m ON e.manager_id = m.emp_id;

-- CROSS JOIN: cartesian product (every emp × every project)
SELECT e.first_name, p.project_name
FROM employees e
CROSS JOIN projects p;

-- Multi-table join + aggregate
SELECT d.dept_name, COUNT(p.project_id) AS project_count, SUM(p.budget) AS total_budget
FROM departments d
LEFT JOIN projects p ON d.dept_id = p.dept_id
GROUP BY d.dept_name;
```

---

## 8. Window / analytic functions

```sql
-- Ranking: ROW_NUMBER vs RANK vs DENSE_RANK
--   ROW_NUMBER  -> always unique (1,2,3,4)
--   RANK        -> ties share a rank, then GAPS   (1,2,2,4)
--   DENSE_RANK  -> ties share a rank, NO gaps      (1,2,2,3)
SELECT first_name, dept_id, salary,
       ROW_NUMBER() OVER (ORDER BY salary DESC)                 AS row_num,
       RANK()       OVER (ORDER BY salary DESC)                 AS rnk,
       DENSE_RANK() OVER (ORDER BY salary DESC)                 AS dense_rnk
FROM employees;

-- PARTITION BY: rank WITHIN each department
SELECT first_name, dept_id, salary,
       RANK() OVER (PARTITION BY dept_id ORDER BY salary DESC) AS dept_rank
FROM employees;

-- Top earner per department (rank then filter via CTE — see section 9)
SELECT * FROM (
    SELECT first_name, dept_id, salary,
           DENSE_RANK() OVER (PARTITION BY dept_id ORDER BY salary DESC) AS dr
    FROM employees
) t
WHERE dr = 1;

-- LEAD / LAG: peek at next / previous row
SELECT first_name, hire_date,
       LAG(hire_date)  OVER (ORDER BY hire_date) AS prev_hire,
       LEAD(hire_date) OVER (ORDER BY hire_date) AS next_hire
FROM employees;

-- Difference vs previous salary (ordered by hire)
SELECT first_name, salary,
       salary - LAG(salary) OVER (ORDER BY hire_date) AS diff_from_prev
FROM employees;

-- Aggregate windows: running total & department average alongside each row
SELECT first_name, dept_id, salary,
       SUM(salary) OVER (ORDER BY hire_date)                      AS running_payroll,
       AVG(salary) OVER (PARTITION BY dept_id)                    AS dept_avg,
       NTILE(4)    OVER (ORDER BY salary DESC)                    AS quartile
FROM employees;
```

---

## 9. CTE — Common Table Expressions (WITH)

```sql
-- Simple CTE: name a subquery, then use it like a table
WITH dept_avg AS (
    SELECT dept_id, AVG(salary) AS avg_sal
    FROM employees
    GROUP BY dept_id
)
SELECT e.first_name, e.salary, d.avg_sal
FROM employees e
JOIN dept_avg d ON e.dept_id = d.dept_id
WHERE e.salary > d.avg_sal;          -- earns above their dept average

-- Multiple CTEs chained
WITH
high_earners AS (
    SELECT * FROM employees WHERE salary > 80000
),
by_dept AS (
    SELECT dept_id, COUNT(*) AS n FROM high_earners GROUP BY dept_id
)
SELECT d.dept_name, b.n
FROM by_dept b JOIN departments d ON d.dept_id = b.dept_id;

-- Recursive CTE: management hierarchy (org chart with levels)
WITH RECURSIVE org AS (
    SELECT emp_id, first_name, manager_id, 1 AS lvl
    FROM employees
    WHERE manager_id IS NULL              -- anchor: top managers
    UNION ALL
    SELECT e.emp_id, e.first_name, e.manager_id, o.lvl + 1
    FROM employees e
    JOIN org o ON e.manager_id = o.emp_id -- recursive step
)
SELECT lvl, first_name FROM org ORDER BY lvl, first_name;
```

---

## 10. Views

```sql
-- Create a view: a saved, reusable query (a "virtual table")
CREATE VIEW v_emp_summary AS
SELECT e.emp_id, e.first_name, e.salary, d.dept_name, d.location
FROM employees e
JOIN departments d ON e.dept_id = d.dept_id;

-- Query a view like a table
SELECT * FROM v_emp_summary WHERE dept_name = 'Engineering';

-- Replace / update a view definition
CREATE OR REPLACE VIEW v_emp_summary AS
SELECT e.emp_id, e.first_name, e.salary, d.dept_name
FROM employees e JOIN departments d ON e.dept_id = d.dept_id;

-- Aggregated view
CREATE VIEW v_dept_stats AS
SELECT d.dept_name, COUNT(e.emp_id) AS headcount, AVG(e.salary) AS avg_salary
FROM departments d
LEFT JOIN employees e ON e.dept_id = d.dept_id
GROUP BY d.dept_name;

SELECT * FROM v_dept_stats;

-- Drop views
DROP VIEW IF EXISTS v_emp_summary;
DROP VIEW IF EXISTS v_dept_stats;
```

---

## 11. Stored procedures (and a function)

```sql
-- MySQL: change delimiter so ; inside the body isn't executed early
DELIMITER //

-- Procedure with an IN parameter
CREATE PROCEDURE get_dept_employees(IN p_dept_id INT)
BEGIN
    SELECT emp_id, first_name, salary
    FROM employees
    WHERE dept_id = p_dept_id
    ORDER BY salary DESC;
END //

-- Procedure with an OUT parameter
CREATE PROCEDURE dept_headcount(IN p_dept_id INT, OUT p_count INT)
BEGIN
    SELECT COUNT(*) INTO p_count
    FROM employees
    WHERE dept_id = p_dept_id;
END //

-- Procedure with control flow + a loop-free update
CREATE PROCEDURE give_raise(IN p_dept_id INT, IN p_pct DECIMAL(5,2))
BEGIN
    IF p_pct <= 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Percentage must be positive';
    ELSE
        UPDATE employees
        SET salary = salary * (1 + p_pct/100)
        WHERE dept_id = p_dept_id;
    END IF;
END //

DELIMITER ;

-- Call them
CALL get_dept_employees(10);

CALL dept_headcount(20, @n);
SELECT @n AS sales_headcount;

CALL give_raise(30, 10);      -- 10% raise for HR

-- A stored FUNCTION (returns a single value)
DELIMITER //
CREATE FUNCTION annual_salary(p_emp_id INT)
RETURNS DECIMAL(12,2)
DETERMINISTIC
BEGIN
    DECLARE v_sal DECIMAL(12,2);
    SELECT salary * 12 INTO v_sal FROM employees WHERE emp_id = p_emp_id;
    RETURN v_sal;
END //
DELIMITER ;

SELECT first_name, annual_salary(emp_id) AS yearly FROM employees;

-- Clean up
DROP PROCEDURE IF EXISTS get_dept_employees;
DROP PROCEDURE IF EXISTS dept_headcount;
DROP PROCEDURE IF EXISTS give_raise;
DROP FUNCTION  IF EXISTS annual_salary;
```

> PostgreSQL: use `CREATE FUNCTION ... LANGUAGE plpgsql` or `CREATE PROCEDURE`
> with `$$ ... $$` dollar-quoting instead of `DELIMITER`.

---

## 12. Sub-queries (nested queries)

```sql
-- Scalar subquery: compare to a single value (overall average)
SELECT first_name, salary
FROM employees
WHERE salary > (SELECT AVG(salary) FROM employees);

-- IN subquery: membership test
SELECT first_name
FROM employees
WHERE dept_id IN (SELECT dept_id FROM projects WHERE budget > 200000);

-- Correlated subquery: inner query references the outer row
-- (employees earning more than their own department's average)
SELECT e.first_name, e.salary, e.dept_id
FROM employees e
WHERE e.salary > (
    SELECT AVG(e2.salary) FROM employees e2 WHERE e2.dept_id = e.dept_id
);

-- EXISTS / NOT EXISTS
SELECT d.dept_name
FROM departments d
WHERE EXISTS (SELECT 1 FROM employees e WHERE e.dept_id = d.dept_id);

SELECT d.dept_name
FROM departments d
WHERE NOT EXISTS (SELECT 1 FROM employees e WHERE e.dept_id = d.dept_id); -- Finance

-- Subquery in FROM (a "derived table")
SELECT dept_id, avg_sal
FROM (SELECT dept_id, AVG(salary) AS avg_sal FROM employees GROUP BY dept_id) t
WHERE avg_sal > 75000;

-- Subquery in SELECT (per-row lookup)
SELECT e.first_name,
       (SELECT d.dept_name FROM departments d WHERE d.dept_id = e.dept_id) AS dept
FROM employees e;

-- ANY / ALL
SELECT first_name, salary FROM employees
WHERE salary > ALL (SELECT salary FROM employees WHERE dept_id = 30); -- beats every HR salary
```

---

## 13. Triggers

```sql
-- Audit table to record salary changes
CREATE TABLE salary_audit (
    audit_id   INT PRIMARY KEY AUTO_INCREMENT,
    emp_id     INT,
    old_salary DECIMAL(10,2),
    new_salary DECIMAL(10,2),
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

DELIMITER //

-- BEFORE INSERT: validate / normalize data
CREATE TRIGGER trg_emp_before_insert
BEFORE INSERT ON employees
FOR EACH ROW
BEGIN
    IF NEW.salary IS NULL THEN
        SET NEW.salary = 30000;          -- default floor
    END IF;
    SET NEW.email = LOWER(NEW.email);    -- normalize
END //

-- AFTER UPDATE: log salary changes into the audit table
CREATE TRIGGER trg_salary_after_update
AFTER UPDATE ON employees
FOR EACH ROW
BEGIN
    IF OLD.salary <> NEW.salary THEN
        INSERT INTO salary_audit (emp_id, old_salary, new_salary)
        VALUES (NEW.emp_id, OLD.salary, NEW.salary);
    END IF;
END //

DELIMITER ;

-- Exercise the triggers
UPDATE employees SET salary = salary + 5000 WHERE emp_id = 2;
SELECT * FROM salary_audit;

-- Inspect / drop triggers
SHOW TRIGGERS;                            -- MySQL
DROP TRIGGER IF EXISTS trg_emp_before_insert;
DROP TRIGGER IF EXISTS trg_salary_after_update;
```

> `NEW` = the incoming row (INSERT/UPDATE); `OLD` = the previous row (UPDATE/DELETE).
> PostgreSQL triggers call a `FUNCTION ... RETURNS TRIGGER` and reference `NEW`/`OLD` the same way.

---

## Quick reference — order of a SELECT

```
FROM        -> which tables (joins happen here)
WHERE       -> filter individual rows
GROUP BY    -> collapse into groups
HAVING      -> filter groups
SELECT      -> pick / compute columns (window functions run here)
DISTINCT    -> drop duplicate rows
ORDER BY    -> sort the result
LIMIT/OFFSET-> take a slice
```
