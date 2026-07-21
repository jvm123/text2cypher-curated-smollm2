# Evaluation Result Analysis

## Scope

- Source: `outputs/runs/without-syntax-check/evaluation/trained_results.jsonl`
- Samples: 50
- Interpretation: offline lexical and static analysis; no Cypher parsing or execution equivalence

## Outcome distribution

| Outcome | Count | Rate |
|---|---:|---:|
| cypher_shaped_non_match | 36 | 72.0% |
| exact_lexical_match | 14 | 28.0% |

## Lexical overlap among non-exact outputs

| Band | Count | Rate |
|---|---:|---:|
| high_overlap | 34 | 94.4% |
| low_overlap | 2 | 5.6% |

## Reference query features: lexical exact-match rate

| Feature | Samples | Exact matches | Exact-match rate |
|---|---:|---:|---:|
| aggregation | 18 | 4 | 22.2% |
| distinct | 10 | 3 | 30.0% |
| match | 50 | 14 | 28.0% |
| node_label | 50 | 14 | 28.0% |
| ordering | 9 | 0 | 0.0% |
| pagination | 10 | 0 | 0.0% |
| property_filter | 38 | 13 | 34.2% |
| relationship_pattern | 37 | 10 | 27.0% |
| return | 50 | 14 | 28.0% |
| where | 27 | 8 | 29.6% |
| with | 12 | 1 | 8.3% |

## Static feature gaps in Cypher-shaped non-matches

Cypher-shaped non-matches: 36

| Gap type | Feature | Count |
|---|---|---:|
| Omitted reference feature | aggregation | 2 |
| Omitted reference feature | distinct | 4 |
| Omitted reference feature | ordering | 1 |
| Omitted reference feature | pagination | 2 |
| Omitted reference feature | relationship_pattern | 5 |
| Omitted reference feature | where | 3 |
| Omitted reference feature | with | 2 |
| Introduced feature | distinct | 1 |
| Introduced feature | property_filter | 2 |
| Introduced feature | relationship_pattern | 3 |
| Introduced feature | where | 7 |
| Introduced feature | with | 2 |

## Execution-match confusion matrix

- Samples: 50
- Execution-evaluated samples: 3
- Definition: True positives are lexical exact matches or execution matches. True negatives are non-exact lexical matches without an execution match. False positives and false negatives are unavailable because the artifact has no independent ground-truth semantic-equivalence label. A null execution_match is treated as not execution-matched.

| Category | Count |
|---|---:|
| true positives | 15 |
| true negatives | 35 |
| false positives | 0 |
| false negatives | 0 |

### True Positives examples

#### instance_id_11856

- Execution match: None
- Token F1: 1.000

Question:

List the types of relationships and their counts connected to Article for which article_id is 1071!

Reference Cypher:

````cypher
MATCH (a:Article{article_id:'1071'})-[r]->() RETURN TYPE(r) AS Relations, COUNT(r) AS Counts
````

Generated output:

````text
MATCH (a:Article{article_id:'1071'})-[r]->() RETURN TYPE(r) AS Relations, COUNT(r) AS Counts
````
#### instance_id_12057

- Execution match: None
- Token F1: 1.000

Question:

List the types of relationships and their counts connected to Article for which comments is Published by Geometry and Topology at
  http://www.maths.warwick.ac.uk/gt/GTVol4/paper14.abs.html!

Reference Cypher:

````cypher
MATCH (a:Article{comments:'Published by Geometry and Topology at   http://www.maths.warwick.ac.uk/gt/GTVol4/paper14.abs.html'})-[r]->() RETURN TYPE(r) AS Relations, COUNT(r) AS Counts
````

Generated output:

````text
MATCH (a:Article{comments:'Published by Geometry and Topology at   http://www.maths.warwick.ac.uk/gt/GTVol4/paper14.abs.html'})-[r]->() RETURN TYPE(r) AS Relations, COUNT(r) AS Counts
````
#### instance_id_12334

- Execution match: None
- Token F1: 1.000

Question:

Enumerate the properties of nodes that are either directly or indirectly connected to Author for which last_name is Mason!

Reference Cypher:

````cypher
MATCH (a:Author{last_name:'Mason'})-[*]->(n) RETURN DISTINCT properties(n) AS Properties
````

Generated output:

````text
MATCH (a:Author{last_name:'Mason'})-[*]->(n) RETURN DISTINCT properties(n) AS Properties
````
#### instance_id_12826

- Execution match: None
- Token F1: 1.000

Question:

List the distinct properties of nodes that are 2 hops away from Report with report_no equal to PAM-780!

Reference Cypher:

````cypher
MATCH (a:Report{report_no:'PAM-780'})-[*2]->(n) RETURN DISTINCT properties(n) AS props
````

Generated output:

````text
MATCH (a:Report{report_no:'PAM-780'})-[*2]->(n) RETURN DISTINCT properties(n) AS props
````
#### instance_id_16927

- Execution match: None
- Token F1: 1.000

Question:

Are there any nodes that are connected with Article where title is Free Field Construction for the ABF Models in Regime II and share a common property with UpdateDate, for which update_date equals 2008-01-29?

Reference Cypher:

````cypher
MATCH (a:Article{title:'Free Field Construction for the ABF Models in Regime II'})-[r]->(n), (d:UpdateDate{update_date:'2008-01-29'}) WHERE ANY(key in keys(n) WHERE n[key] = d[key]) RETURN n
````

Generated output:

````text
MATCH (a:Article{title:'Free Field Construction for the ABF Models in Regime II'})-[r]->(n), (d:UpdateDate{update_date:'2008-01-29'}) WHERE ANY(key in keys(n) WHERE n[key] = d[key]) RETURN n
````

### True Negatives examples

#### instance_id_14109

- Execution match: None
- Token F1: 1.000

Question:

Find the Article for which comments is 21 pages, AMS-LaTeX!

Reference Cypher:

````cypher
MATCH (n:Article {comments:'21 pages, AMS-LaTeX'}) RETURN n
````

Generated output:

````text
MATCH (n:Article {comments: '21 pages, AMS-LaTeX'}) RETURN n
````
#### instance_id_43324

- Execution match: None
- Token F1: 1.000

Question:

Which streams have the most distinct games played? List the top 5.

Reference Cypher:

````cypher
MATCH (s:Stream)-[:PLAYS]->(g:Game) WITH s, COUNT(DISTINCT g) AS distinctGames ORDER BY distinctGames DESC LIMIT 5 RETURN s.name AS streamName, distinctGames
````

Generated output:

````text
MATCH (s:Stream)-[:PLAYS]->(g:Game) WITH s, count(DISTINCT g) AS distinctGames ORDER BY distinctGames DESC LIMIT 5 RETURN s.name AS streamName, distinctGames
````
#### instance_id_9530

- Execution match: None
- Token F1: 1.000

Question:

Which nodes have a common property with Article where article_id is 2007 and are PUBLISHED_IN linked to a Journal?

Reference Cypher:

````cypher
MATCH (a:Article {article_id:'2007'})-[r:PUBLISHED_IN]->(b:Journal) WHERE ANY(key IN keys(a) WHERE a[key] = b[key]) RETURN b
````

Generated output:

````text
MATCH (a:Article{article_id:'2007'})-[r:PUBLISHED_IN]->(b:Journal) WHERE ANY(key IN keys(a) WHERE a[key] = b[key]) RETURN b
````
#### instance_id_15057

- Execution match: None
- Token F1: 0.957

Question:

How many unique relationships originate from Article where abstract is   The Wakimoto construction for the quantum affine algebra U_q(\hat{sl}_2)
admits a reduction to the q-deformed parafermion algebras. We interpret the
latter theory as a free field realization of the Andrews-Baxter-Forrester
models in regime II. We give multi-particle form factors of some local
operators on the lattice and compute their scaling limit, where the models are
described by a massive field theory with Z_k symmetric minimal scattering
matrices.
?

Reference Cypher:

````cypher
MATCH (a:Article{abstract:'  The Wakimoto construction for the quantum affine algebra U_q(\hat{sl}_2) admits a reduction to the q-deformed parafermion algebras. We interpret the latter theory as a free field realization of the Andrews-Baxter-Forrester models in regime II. We give multi-particle form factors of some local operators on the lattice and compute their scaling limit, where the models are described by a massive field theory with Z_k symmetric minimal scattering matrices. '})-[r]->() RETURN COUNT(DISTINCT TYPE(r)) AS rels, TYPE(r)
````

Generated output:

````text
MATCH (a:Article{abstract:'  The Wakimoto construction for the quantum affine algebra U_q(\hat{sl}_2) admits a reduction to the q-deformed parafermion algebras. We interpret the latter theory as a free field realization of the Andrews-Baxter-Forrester models in regime II. We give multi-particle form factors of some local operators on the lattice and compute their scaling limit, where the models are described by a massive field theory with Z_k symmetric minimal scattering matrices. "})-[r]->() RETURN count(DISTINCT r)
````
#### instance_id_22944

- Execution match: None
- Token F1: 0.933

Question:

Identify characters who belong to community 579.

Reference Cypher:

````cypher
MATCH (c:Character) WHERE c.community = 579 RETURN c
````

Generated output:

````text
MATCH (c:Character) WHERE c.community = 579 RETURN c.name
````

### False Positives examples

No examples.

### False Negatives examples

No examples.

## Database-alias breakdown

| Alias | Samples | Exact lexical matches | Exact-match rate |
|---|---:|---:|---:|
| <unset> | 32 | 13 | 40.6% |
| neo4jlabs_demo_db_bluesky | 1 | 1 | 100.0% |
| neo4jlabs_demo_db_buzzoverflow | 3 | 0 | 0.0% |
| neo4jlabs_demo_db_gameofthrones | 2 | 0 | 0.0% |
| neo4jlabs_demo_db_movies | 3 | 0 | 0.0% |
| neo4jlabs_demo_db_twitch | 9 | 0 | 0.0% |

## Reference-complexity breakdown

| Recognized reference features | Samples | Exact lexical matches | Exact-match rate |
|---:|---:|---:|---:|
| 3 | 1 | 0 | 0.0% |
| 4 | 7 | 0 | 0.0% |
| 5 | 11 | 4 | 36.4% |
| 6 | 15 | 9 | 60.0% |
| 7 | 4 | 1 | 25.0% |
| 8 | 4 | 0 | 0.0% |
| 9 | 5 | 0 | 0.0% |
| 10 | 3 | 0 | 0.0% |

## Generation errors

- None

## Representative examples

### Complex Exact Matches

#### instance_id_8575 — exact_lexical_match

- Token F1: 1.000
- Reference features: aggregation, match, node_label, property_filter, relationship_pattern, return, where
- Predicted features: aggregation, match, node_label, property_filter, relationship_pattern, return, where
- Omitted reference features: none
- Introduced features: none

Question:

Find comments of the Article and return it along with the count of Journal that are linked via PUBLISHED_IN where pages is 641-672!

Reference Cypher:

````cypher
MATCH (n:Article) -[r:PUBLISHED_IN]->(m:Journal) WHERE r.pages = '641-672' RETURN n.comments AS comments, count(m) AS count
````

Generated output:

````text
MATCH (n:Article) -[r:PUBLISHED_IN]->(m:Journal) WHERE r.pages = '641-672' RETURN n.comments AS comments, count(m) AS count
````

#### instance_id_11856 — exact_lexical_match

- Token F1: 1.000
- Reference features: aggregation, match, node_label, property_filter, relationship_pattern, return
- Predicted features: aggregation, match, node_label, property_filter, relationship_pattern, return
- Omitted reference features: none
- Introduced features: none

Question:

List the types of relationships and their counts connected to Article for which article_id is 1071!

Reference Cypher:

````cypher
MATCH (a:Article{article_id:'1071'})-[r]->() RETURN TYPE(r) AS Relations, COUNT(r) AS Counts
````

Generated output:

````text
MATCH (a:Article{article_id:'1071'})-[r]->() RETURN TYPE(r) AS Relations, COUNT(r) AS Counts
````

#### instance_id_12057 — exact_lexical_match

- Token F1: 1.000
- Reference features: aggregation, match, node_label, property_filter, relationship_pattern, return
- Predicted features: aggregation, match, node_label, property_filter, relationship_pattern, return
- Omitted reference features: none
- Introduced features: none

Question:

List the types of relationships and their counts connected to Article for which comments is Published by Geometry and Topology at
  http://www.maths.warwick.ac.uk/gt/GTVol4/paper14.abs.html!

Reference Cypher:

````cypher
MATCH (a:Article{comments:'Published by Geometry and Topology at   http://www.maths.warwick.ac.uk/gt/GTVol4/paper14.abs.html'})-[r]->() RETURN TYPE(r) AS Relations, COUNT(r) AS Counts
````

Generated output:

````text
MATCH (a:Article{comments:'Published by Geometry and Topology at   http://www.maths.warwick.ac.uk/gt/GTVol4/paper14.abs.html'})-[r]->() RETURN TYPE(r) AS Relations, COUNT(r) AS Counts
````

#### instance_id_12334 — exact_lexical_match

- Token F1: 1.000
- Reference features: distinct, match, node_label, property_filter, relationship_pattern, return
- Predicted features: distinct, match, node_label, property_filter, relationship_pattern, return
- Omitted reference features: none
- Introduced features: none

Question:

Enumerate the properties of nodes that are either directly or indirectly connected to Author for which last_name is Mason!

Reference Cypher:

````cypher
MATCH (a:Author{last_name:'Mason'})-[*]->(n) RETURN DISTINCT properties(n) AS Properties
````

Generated output:

````text
MATCH (a:Author{last_name:'Mason'})-[*]->(n) RETURN DISTINCT properties(n) AS Properties
````

#### instance_id_12826 — exact_lexical_match

- Token F1: 1.000
- Reference features: distinct, match, node_label, property_filter, relationship_pattern, return
- Predicted features: distinct, match, node_label, property_filter, relationship_pattern, return
- Omitted reference features: none
- Introduced features: none

Question:

List the distinct properties of nodes that are 2 hops away from Report with report_no equal to PAM-780!

Reference Cypher:

````cypher
MATCH (a:Report{report_no:'PAM-780'})-[*2]->(n) RETURN DISTINCT properties(n) AS props
````

Generated output:

````text
MATCH (a:Report{report_no:'PAM-780'})-[*2]->(n) RETURN DISTINCT properties(n) AS props
````

### Closest Cypher Non Matches

#### instance_id_43324 — cypher_shaped_non_match

- Token F1: 1.000
- Reference features: aggregation, distinct, match, node_label, ordering, pagination, relationship_pattern, return, with
- Predicted features: aggregation, distinct, match, node_label, ordering, pagination, relationship_pattern, return, with
- Omitted reference features: none
- Introduced features: none

Question:

Which streams have the most distinct games played? List the top 5.

Reference Cypher:

````cypher
MATCH (s:Stream)-[:PLAYS]->(g:Game) WITH s, COUNT(DISTINCT g) AS distinctGames ORDER BY distinctGames DESC LIMIT 5 RETURN s.name AS streamName, distinctGames
````

Generated output:

````text
MATCH (s:Stream)-[:PLAYS]->(g:Game) WITH s, count(DISTINCT g) AS distinctGames ORDER BY distinctGames DESC LIMIT 5 RETURN s.name AS streamName, distinctGames
````

#### instance_id_9530 — cypher_shaped_non_match

- Token F1: 1.000
- Reference features: match, node_label, property_filter, relationship_pattern, return, where
- Predicted features: match, node_label, property_filter, relationship_pattern, return, where
- Omitted reference features: none
- Introduced features: none

Question:

Which nodes have a common property with Article where article_id is 2007 and are PUBLISHED_IN linked to a Journal?

Reference Cypher:

````cypher
MATCH (a:Article {article_id:'2007'})-[r:PUBLISHED_IN]->(b:Journal) WHERE ANY(key IN keys(a) WHERE a[key] = b[key]) RETURN b
````

Generated output:

````text
MATCH (a:Article{article_id:'2007'})-[r:PUBLISHED_IN]->(b:Journal) WHERE ANY(key IN keys(a) WHERE a[key] = b[key]) RETURN b
````

#### instance_id_14109 — cypher_shaped_non_match

- Token F1: 1.000
- Reference features: match, node_label, property_filter, return
- Predicted features: match, node_label, property_filter, return
- Omitted reference features: none
- Introduced features: none

Question:

Find the Article for which comments is 21 pages, AMS-LaTeX!

Reference Cypher:

````cypher
MATCH (n:Article {comments:'21 pages, AMS-LaTeX'}) RETURN n
````

Generated output:

````text
MATCH (n:Article {comments: '21 pages, AMS-LaTeX'}) RETURN n
````

#### instance_id_15057 — cypher_shaped_non_match

- Token F1: 0.957
- Reference features: aggregation, distinct, match, node_label, pagination, property_filter, relationship_pattern, return, where, with
- Predicted features: aggregation, distinct, match, node_label, pagination, property_filter, relationship_pattern, return, where, with
- Omitted reference features: none
- Introduced features: none

Question:

How many unique relationships originate from Article where abstract is   The Wakimoto construction for the quantum affine algebra U_q(\hat{sl}_2)
admits a reduction to the q-deformed parafermion algebras. We interpret the
latter theory as a free field realization of the Andrews-Baxter-Forrester
models in regime II. We give multi-particle form factors of some local
operators on the lattice and compute their scaling limit, where the models are
described by a massive field theory with Z_k symmetric minimal scattering
matrices.
?

Reference Cypher:

````cypher
MATCH (a:Article{abstract:'  The Wakimoto construction for the quantum affine algebra U_q(\hat{sl}_2) admits a reduction to the q-deformed parafermion algebras. We interpret the latter theory as a free field realization of the Andrews-Baxter-Forrester models in regime II. We give multi-particle form factors of some local operators on the lattice and compute their scaling limit, where the models are described by a massive field theory with Z_k symmetric minimal scattering matrices. '})-[r]->() RETURN COUNT(DISTINCT TYPE(r)) AS rels, TYPE(r)
````

Generated output:

````text
MATCH (a:Article{abstract:'  The Wakimoto construction for the quantum affine algebra U_q(\hat{sl}_2) admits a reduction to the q-deformed parafermion algebras. We interpret the latter theory as a free field realization of the Andrews-Baxter-Forrester models in regime II. We give multi-particle form factors of some local operators on the lattice and compute their scaling limit, where the models are described by a massive field theory with Z_k symmetric minimal scattering matrices. "})-[r]->() RETURN count(DISTINCT r)
````

#### instance_id_22944 — cypher_shaped_non_match

- Token F1: 0.933
- Reference features: match, node_label, property_filter, return, where
- Predicted features: match, node_label, property_filter, return, where
- Omitted reference features: none
- Introduced features: none

Question:

Identify characters who belong to community 579.

Reference Cypher:

````cypher
MATCH (c:Character) WHERE c.community = 579 RETURN c
````

Generated output:

````text
MATCH (c:Character) WHERE c.community = 579 RETURN c.name
````

## Limitations

- Exact match and token overlap are lexical metrics, not semantic or execution equivalence.
- Feature extraction uses conservative regular-expression rules, not a Cypher parser.
- A non-exact result can still be semantically valid; this report does not determine that.
