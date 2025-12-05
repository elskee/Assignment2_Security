
select DISTINCT commit_url, cve_id, hash, repo_url FROM(
SELECT CONCAT(fx.repo_url, '/commit/', fx.hash) AS commit_url, cv.cve_id, fx.hash, fx.repo_url, f.filename, f.num_lines_added, f.num_lines_deleted, f.code_before, f.code_after, f.diff_parsed, cc.cwe_id 
FROM file_change f, commits c, fixes fx, cve cv, cwe_classification cc
WHERE f.hash = c.hash 
AND c.hash = fx.hash 
AND fx.cve_id = cv.cve_id 
AND cv.cve_id = cc.cve_id 
AND fx.score >= 55
AND f.programming_language = 'Python'
AND cc.cwe_id = 'CWE-89') AS t
ORDER BY cve_id;


