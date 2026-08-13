-- Overall job funnel
SELECT
    COUNT (*) AS total_jobs,
    SUM(CASE WHEN interested = 'Yes' THEN 1 ELSE 0 END) AS interested_jobs,
    SUM(CASE WHEN applied = 'Yes' THEN 1 ELSE 0 END) AS applied_jobs,
    SUM(CASE WHEN interview = 'Yes' THEN 1 ELSE 0 END) AS interview_jobs
FROM jobs;

-- jobs reviewed
SELECT 
    SUM(
        CASE 
        WHEN interested = 'Yes'
            OR interested = 'No'
            OR posting_status = 'Closed' 
        THEN 1 
        ELSE 0
        END
        ) AS
        reviewed_jobs
FROM jobs;

-- Unique posting statuses
SELECT DISTINCT posting_status
FROM jobs;

-- jobs by alert
SELECT
    alert_name,
    COUNT(*) AS total_jobs
FROM jobs
GROUP BY alert_name
ORDER BY total_jobs DESC;

SELECT
    CASE
        WHEN interested IS NULL THEN 'NULL'
        WHEN interested = '' THEN 'BLANK'
        ELSE interested
    END AS interested_value,
    COUNT(*) AS total_jobs
FROM jobs
GROUP BY interested_value;

-- CTE for % of jobs interested of total jobs reviewed
WITH job_stats AS (
    SELECT
        SUM(
            CASE
                WHEN interested = 'Yes'
                THEN 1
                ELSE 0
            END
        ) AS interested_jobs,

        SUM(
            CASE
                WHEN interested = 'Yes'   
                    OR interested = 'No'
                    OR posting_status = 'Closed' 
            THEN 1 
            ELSE 0
            END 
        ) AS reviewed_jobs
    FROM jobs
)

SELECT
    interested_jobs,
    reviewed_jobs,
    ROUND(
        interested_jobs * 100.0 / reviewed_jobs,
        1
    ) AS interested_rate
FROM job_stats;


WITH alert_stats AS (
    SELECT
        alert_name,
        SUM(
            CASE
                WHEN interested = 'Yes'
                THEN 1
                ELSE 0
            END
        ) AS interested_jobs,
                
        SUM(
            CASE
                WHEN interested = 'Yes'   
                    OR interested = 'No'
                    OR posting_status = 'Closed' 
            THEN 1 
            ELSE 0
            END 
        ) AS reviewed_jobs
        FROM jobs
    WHERE alert_name IS NOT NULL
        AND alert_name != ''
    GROUP BY alert_name
)

SELECT
    alert_name,
    interested_jobs,
    reviewed_jobs,
    ROUND(
        interested_jobs * 100.0 / reviewed_jobs,
        1
    ) AS interested_rate
FROM alert_stats
ORDER BY interested_rate DESC;