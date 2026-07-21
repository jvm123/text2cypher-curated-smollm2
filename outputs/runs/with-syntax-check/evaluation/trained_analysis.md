# Evaluation Result Analysis

## Scope

- Source: `outputs/runs/with-syntax-check-no-truncate/evaluation/trained_results.jsonl`
- Samples: 9
- Interpretation: offline lexical and static analysis; no Cypher parsing or execution equivalence

## Outcome distribution

| Outcome | Count | Rate |
|---|---:|---:|
| cypher_shaped_non_match | 4 | 44.4% |
| exact_lexical_match | 5 | 55.6% |

## Lexical overlap among non-exact outputs

| Band | Count | Rate |
|---|---:|---:|
| high_overlap | 4 | 100.0% |

## Reference query features: lexical exact-match rate

| Feature | Samples | Exact matches | Exact-match rate |
|---|---:|---:|---:|
| aggregation | 2 | 1 | 50.0% |
| distinct | 2 | 2 | 100.0% |
| match | 9 | 5 | 55.6% |
| node_label | 9 | 5 | 55.6% |
| ordering | 1 | 0 | 0.0% |
| pagination | 2 | 1 | 50.0% |
| property_filter | 6 | 4 | 66.7% |
| relationship_pattern | 4 | 2 | 50.0% |
| return | 9 | 5 | 55.6% |
| where | 6 | 4 | 66.7% |
| with | 2 | 2 | 100.0% |

## Static feature gaps in Cypher-shaped non-matches

Cypher-shaped non-matches: 4

| Gap type | Feature | Count |
|---|---|---:|
| Omitted reference feature | aggregation | 1 |
| Omitted reference feature | relationship_pattern | 1 |
| Introduced feature | aggregation | 1 |
| Introduced feature | ordering | 1 |
| Introduced feature | pagination | 1 |
| Introduced feature | property_filter | 1 |
| Introduced feature | where | 1 |

## Execution-match confusion matrix

- Samples: 9
- Execution-evaluated samples: 0
- Definition: True positives are lexical exact matches or execution matches. True negatives are non-exact lexical matches without an execution match. False positives and false negatives are unavailable because the artifact has no independent ground-truth semantic-equivalence label. A null execution_match is treated as not execution-matched.

| Category | Count |
|---|---:|
| true positives | 5 |
| true negatives | 4 |
| false positives | 0 |
| false negatives | 0 |

### True Positives examples

#### instance_id_13430

- Execution match: None
- Token F1: 1.000

Question:

Which nodes are connected to UpdateDate where update_date is 2008-01-29, and also to another node?

Reference Cypher:

````cypher
MATCH (a:UpdateDate{update_date:'2008-01-29'})-[r]->(n), (n)-[s]->(m) RETURN labels(n) AS Interim, labels(m) AS Target
````

Generated output:

````text
MATCH (a:UpdateDate{update_date:'2008-01-29'})-[r]->(n), (n)-[s]->(m) RETURN labels(n) AS Interim, labels(m) AS Target
````
#### instance_id_19093

- Execution match: None
- Token F1: 1.000

Question:

Fetch the distinct values of the report_id from Report where either report_no is none provided or report_id is not null!

Reference Cypher:

````cypher
MATCH (n:Report) WHERE n.report_no = 'none provided' OR n.report_id IS NOT NULL RETURN DISTINCT n.report_id AS report_id
````

Generated output:

````text
MATCH (n:Report) WHERE n.report_no = 'none provided' OR n.report_id IS NOT NULL RETURN DISTINCT n.report_id AS report_id
````
#### instance_id_19443

- Execution match: None
- Token F1: 1.000

Question:

Find the title and the comments for those Article where title starts with O!

Reference Cypher:

````cypher
MATCH (n:Article) WHERE n.title STARTS WITH 'O' RETURN n.title AS title, n.comments AS comments
````

Generated output:

````text
MATCH (n:Article) WHERE n.title STARTS WITH 'O' RETURN n.title AS title, n.comments AS comments
````
#### instance_id_30446

- Execution match: None
- Token F1: 1.000

Question:

List the labels of users with an area less than 2 and a size greater than 1.

Reference Cypher:

````cypher
MATCH (u:User) WHERE u.area < 2 AND u.size > 1 RETURN u.label
````

Generated output:

````text
MATCH (u:User) WHERE u.area < 2 AND u.size > 1 RETURN u.label
````
#### instance_id_7043

- Execution match: None
- Token F1: 1.000

Question:

Search for the article_id values from 20 Article that are linked to Journal via PUBLISHED_IN with pages = 537-560, and return article_id along with the respective Journal counts!

Reference Cypher:

````cypher
MATCH (n:Article) -[r:PUBLISHED_IN]->(m:Journal) WHERE r.pages='537-560' WITH DISTINCT n, m RETURN n.article_id AS article_id, count(m) AS count LIMIT 20
````

Generated output:

````text
MATCH (n:Article) -[r:PUBLISHED_IN]->(m:Journal) WHERE r.pages='537-560' WITH DISTINCT n, m RETURN n.article_id AS article_id, count(m) AS count LIMIT 20
````

### True Negatives examples

#### instance_id_3190

- Execution match: None
- Token F1: 0.875

Question:

What are the names and ages of editors?

Reference Cypher:

````cypher
MATCH (e:Editor) RETURN e.Name, e.Age
````

Generated output:

````text
MATCH (e:Editor) RETURN e.Name AS Editor_Name, e.Age AS Editor_Age
````
#### instance_id_36940

- Execution match: None
- Token F1: 0.811

Question:

Identify streams that have moderators who are also VIPs.

Reference Cypher:

````cypher
MATCH (s:Stream)<-[:MODERATOR]-(m:User)-[:VIP]->(s) RETURN s.name AS stream, m.name AS moderator_and_vip
````

Generated output:

````text
MATCH (s:Stream)-[:MODERATOR]->(m:VIP) WHERE m.name =~'^[vip]->(:Stream)' RETURN s
````
#### instance_id_33953

- Execution match: None
- Token F1: 0.771

Question:

Find the streams that were created before 2018 and have more than 5,000 followers.

Reference Cypher:

````cypher
MATCH (s:Stream) WHERE s.createdAt < datetime('2018-01-01T00:00:00.000000Z') AND s.followers > 5000 RETURN s
````

Generated output:

````text
MATCH (s:Stream) WHERE s.createdAt < datetime('2018-01-01T00:00:00Z') AND s.followers > 5000 RETURN s.name AS stream_name, count(s) AS stream_count ORDER BY stream_count DESC LIMIT 1
````
#### instance_id_26310

- Execution match: None
- Token F1: 0.667

Question:

What are the top 5 tags used in questions with a score less than zero?

Reference Cypher:

````cypher
MATCH (q:Question)-[:TAGGED]->(t:Tag) WHERE q.score < 0 RETURN t.name, count(q) AS usage ORDER BY usage DESC LIMIT 5
````

Generated output:

````text
MATCH (q:Question) WHERE q.score < 0 RETURN q.name, q.tag ORDER BY q.score DESC LIMIT 5
````

### False Positives examples

No examples.

### False Negatives examples

No examples.

## Database-alias breakdown

| Alias | Samples | Exact lexical matches | Exact-match rate |
|---|---:|---:|---:|
| <unset> | 5 | 4 | 80.0% |
| neo4jlabs_demo_db_bluesky | 1 | 1 | 100.0% |
| neo4jlabs_demo_db_buzzoverflow | 1 | 0 | 0.0% |
| neo4jlabs_demo_db_twitch | 2 | 0 | 0.0% |

## Reference-complexity breakdown

| Recognized reference features | Samples | Exact lexical matches | Exact-match rate |
|---:|---:|---:|---:|
| 3 | 1 | 0 | 0.0% |
| 4 | 1 | 0 | 0.0% |
| 5 | 4 | 3 | 75.0% |
| 6 | 1 | 1 | 100.0% |
| 9 | 1 | 0 | 0.0% |
| 10 | 1 | 1 | 100.0% |

## Generation errors

- None

## Representative examples

### Complex Exact Matches

#### instance_id_7043 — exact_lexical_match

- Token F1: 1.000
- Reference features: aggregation, distinct, match, node_label, pagination, property_filter, relationship_pattern, return, where, with
- Predicted features: aggregation, distinct, match, node_label, pagination, property_filter, relationship_pattern, return, where, with
- Omitted reference features: none
- Introduced features: none

Question:

Search for the article_id values from 20 Article that are linked to Journal via PUBLISHED_IN with pages = 537-560, and return article_id along with the respective Journal counts!

Reference Cypher:

````cypher
MATCH (n:Article) -[r:PUBLISHED_IN]->(m:Journal) WHERE r.pages='537-560' WITH DISTINCT n, m RETURN n.article_id AS article_id, count(m) AS count LIMIT 20
````

Generated output:

````text
MATCH (n:Article) -[r:PUBLISHED_IN]->(m:Journal) WHERE r.pages='537-560' WITH DISTINCT n, m RETURN n.article_id AS article_id, count(m) AS count LIMIT 20
````

#### instance_id_19093 — exact_lexical_match

- Token F1: 1.000
- Reference features: distinct, match, node_label, property_filter, return, where
- Predicted features: distinct, match, node_label, property_filter, return, where
- Omitted reference features: none
- Introduced features: none

Question:

Fetch the distinct values of the report_id from Report where either report_no is none provided or report_id is not null!

Reference Cypher:

````cypher
MATCH (n:Report) WHERE n.report_no = 'none provided' OR n.report_id IS NOT NULL RETURN DISTINCT n.report_id AS report_id
````

Generated output:

````text
MATCH (n:Report) WHERE n.report_no = 'none provided' OR n.report_id IS NOT NULL RETURN DISTINCT n.report_id AS report_id
````

#### instance_id_13430 — exact_lexical_match

- Token F1: 1.000
- Reference features: match, node_label, property_filter, relationship_pattern, return
- Predicted features: match, node_label, property_filter, relationship_pattern, return
- Omitted reference features: none
- Introduced features: none

Question:

Which nodes are connected to UpdateDate where update_date is 2008-01-29, and also to another node?

Reference Cypher:

````cypher
MATCH (a:UpdateDate{update_date:'2008-01-29'})-[r]->(n), (n)-[s]->(m) RETURN labels(n) AS Interim, labels(m) AS Target
````

Generated output:

````text
MATCH (a:UpdateDate{update_date:'2008-01-29'})-[r]->(n), (n)-[s]->(m) RETURN labels(n) AS Interim, labels(m) AS Target
````

#### instance_id_19443 — exact_lexical_match

- Token F1: 1.000
- Reference features: match, node_label, return, where, with
- Predicted features: match, node_label, return, where, with
- Omitted reference features: none
- Introduced features: none

Question:

Find the title and the comments for those Article where title starts with O!

Reference Cypher:

````cypher
MATCH (n:Article) WHERE n.title STARTS WITH 'O' RETURN n.title AS title, n.comments AS comments
````

Generated output:

````text
MATCH (n:Article) WHERE n.title STARTS WITH 'O' RETURN n.title AS title, n.comments AS comments
````

#### instance_id_30446 — exact_lexical_match

- Token F1: 1.000
- Reference features: match, node_label, property_filter, return, where
- Predicted features: match, node_label, property_filter, return, where
- Omitted reference features: none
- Introduced features: none

Question:

List the labels of users with an area less than 2 and a size greater than 1.

Reference Cypher:

````cypher
MATCH (u:User) WHERE u.area < 2 AND u.size > 1 RETURN u.label
````

Generated output:

````text
MATCH (u:User) WHERE u.area < 2 AND u.size > 1 RETURN u.label
````

### Closest Cypher Non Matches

#### instance_id_3190 — cypher_shaped_non_match

- Token F1: 0.875
- Reference features: match, node_label, return
- Predicted features: match, node_label, return
- Omitted reference features: none
- Introduced features: none

Question:

What are the names and ages of editors?

Reference Cypher:

````cypher
MATCH (e:Editor) RETURN e.Name, e.Age
````

Generated output:

````text
MATCH (e:Editor) RETURN e.Name AS Editor_Name, e.Age AS Editor_Age
````

#### instance_id_36940 — cypher_shaped_non_match

- Token F1: 0.811
- Reference features: match, node_label, relationship_pattern, return
- Predicted features: match, node_label, property_filter, relationship_pattern, return, where
- Omitted reference features: none
- Introduced features: property_filter, where

Question:

Identify streams that have moderators who are also VIPs.

Reference Cypher:

````cypher
MATCH (s:Stream)<-[:MODERATOR]-(m:User)-[:VIP]->(s) RETURN s.name AS stream, m.name AS moderator_and_vip
````

Generated output:

````text
MATCH (s:Stream)-[:MODERATOR]->(m:VIP) WHERE m.name =~'^[vip]->(:Stream)' RETURN s
````

#### instance_id_33953 — cypher_shaped_non_match

- Token F1: 0.771
- Reference features: match, node_label, property_filter, return, where
- Predicted features: aggregation, match, node_label, ordering, pagination, property_filter, return, where
- Omitted reference features: none
- Introduced features: aggregation, ordering, pagination

Question:

Find the streams that were created before 2018 and have more than 5,000 followers.

Reference Cypher:

````cypher
MATCH (s:Stream) WHERE s.createdAt < datetime('2018-01-01T00:00:00.000000Z') AND s.followers > 5000 RETURN s
````

Generated output:

````text
MATCH (s:Stream) WHERE s.createdAt < datetime('2018-01-01T00:00:00Z') AND s.followers > 5000 RETURN s.name AS stream_name, count(s) AS stream_count ORDER BY stream_count DESC LIMIT 1
````

#### instance_id_26310 — cypher_shaped_non_match

- Token F1: 0.667
- Reference features: aggregation, match, node_label, ordering, pagination, property_filter, relationship_pattern, return, where
- Predicted features: match, node_label, ordering, pagination, property_filter, return, where
- Omitted reference features: aggregation, relationship_pattern
- Introduced features: none

Question:

What are the top 5 tags used in questions with a score less than zero?

Reference Cypher:

````cypher
MATCH (q:Question)-[:TAGGED]->(t:Tag) WHERE q.score < 0 RETURN t.name, count(q) AS usage ORDER BY usage DESC LIMIT 5
````

Generated output:

````text
MATCH (q:Question) WHERE q.score < 0 RETURN q.name, q.tag ORDER BY q.score DESC LIMIT 5
````

## Limitations

- Exact match and token overlap are lexical metrics, not semantic or execution equivalence.
- Feature extraction uses conservative regular-expression rules, not a Cypher parser.
- A non-exact result can still be semantically valid; this report does not determine that.
