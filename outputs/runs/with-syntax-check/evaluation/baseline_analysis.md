# Evaluation Result Analysis

## Scope

- Source: `outputs/runs/with-syntax-check/evaluation/baseline_results.jsonl`
- Samples: 50
- Interpretation: offline lexical and static analysis; no Cypher parsing or execution equivalence

## Outcome distribution

| Outcome | Count | Rate |
|---|---:|---:|
| cypher_shaped_non_match | 22 | 44.0% |
| prose_or_markdown_output | 7 | 14.0% |
| sql_shaped_output | 21 | 42.0% |

## Lexical overlap among non-exact outputs

| Band | Count | Rate |
|---|---:|---:|
| high_overlap | 1 | 2.0% |
| low_overlap | 48 | 96.0% |
| no_overlap | 1 | 2.0% |

## Reference query features: lexical exact-match rate

| Feature | Samples | Exact matches | Exact-match rate |
|---|---:|---:|---:|
| aggregation | 18 | 0 | 0.0% |
| distinct | 10 | 0 | 0.0% |
| match | 50 | 0 | 0.0% |
| node_label | 50 | 0 | 0.0% |
| ordering | 9 | 0 | 0.0% |
| pagination | 10 | 0 | 0.0% |
| property_filter | 38 | 0 | 0.0% |
| relationship_pattern | 37 | 0 | 0.0% |
| return | 50 | 0 | 0.0% |
| where | 27 | 0 | 0.0% |
| with | 12 | 0 | 0.0% |

## Static feature gaps in Cypher-shaped non-matches

Cypher-shaped non-matches: 22

| Gap type | Feature | Count |
|---|---|---:|
| Omitted reference feature | aggregation | 8 |
| Omitted reference feature | distinct | 2 |
| Omitted reference feature | match | 14 |
| Omitted reference feature | node_label | 19 |
| Omitted reference feature | ordering | 7 |
| Omitted reference feature | pagination | 7 |
| Omitted reference feature | property_filter | 11 |
| Omitted reference feature | relationship_pattern | 11 |
| Omitted reference feature | return | 19 |
| Omitted reference feature | where | 9 |
| Omitted reference feature | with | 2 |
| Introduced feature | property_filter | 1 |
| Introduced feature | relationship_pattern | 1 |
| Introduced feature | where | 1 |
| Introduced feature | with | 9 |
| Introduced feature | write_clause | 2 |

## Execution-match confusion matrix

- Samples: 50
- Execution-evaluated samples: 0
- Definition: True positives are lexical exact matches or execution matches. True negatives are non-exact lexical matches without an execution match. False positives and false negatives are unavailable because the artifact has no independent ground-truth semantic-equivalence label. A null execution_match is treated as not execution-matched.

| Category | Count |
|---|---:|
| true positives | 0 |
| true negatives | 50 |
| false positives | 0 |
| false negatives | 0 |

### True Positives examples

No examples.

### True Negatives examples

#### instance_id_4046

- Execution match: None
- Token F1: 0.650

Question:

Is there a path connecting Author where first_name is Bernhard and Topic, for which description is Focusing on techniques and concepts related to transformations, solutions, and properties of linear equations and matrices, including Jordan normal form, eigenvalues, eigenvectors, diagonalization, and eigenformulations.?

Reference Cypher:

````cypher
MATCH (a:Author{first_name:'Bernhard'}), (b:Topic{description:'Focusing on techniques and concepts related to transformations, solutions, and properties of linear equations and matrices, including Jordan normal form, eigenvalues, eigenvectors, diagonalization, and eigenformulations.'}) RETURN EXISTS((a)-[*]-(b)) AS pathExists
````

Generated output:

````text
Yes, there is a path connecting Author where first_name is Bernhard and Topic, for which description is Focusing on techniques and concepts related to transformations, solutions, and properties of linear equations and matrices, including Jordan normal form, eigenvalues, eigenvectors, diagonalization, and eigenformulations.
````
#### instance_id_40097

- Execution match: None
- Token F1: 0.402

Question:

List the roles played by actors in the first 3 movies directed by Nancy Meyers.

Reference Cypher:

````cypher
MATCH (director:Person {name: "Nancy Meyers"})-[:DIRECTED]->(movie:Movie) WITH movie ORDER BY movie.released LIMIT 3 MATCH (actor:Person)-[actedIn:ACTED_IN]->(movie) RETURN movie.title AS MovieTitle, actor.name AS ActorName, actedIn.roles AS Roles
````

Generated output:

````text
Movie:
- **The Matrix**
- **The Matrix**
- **The Matrix**

Relationship:
(:Person)-[:ACTED_IN]->(:Movie)
(:Person)-[:DIRECTED]->(:Movie)
(:Person)-[:PRODUCED]->(:Movie)
(:Person)-[:WROTE]->(:Movie)
(:Person)-[:FOLLOWS]->(:Person)
(:Person)-[:REVIEWED]->(:Movie)

Answer: The first 3 movies played by Nancy Meyers.
````
#### instance_id_19443

- Execution match: None
- Token F1: 0.382

Question:

Find the title and the comments for those Article where title starts with O!

Reference Cypher:

````cypher
MATCH (n:Article) WHERE n.title STARTS WITH 'O' RETURN n.title AS title, n.comments AS comments
````

Generated output:

````text
Query: MATCH Article {title: "O!"}

Output:
Title: O!
Comments: O!

Explanation: The query MATCH Article {title: "O!"} returns the title and comments for the Article where the title starts with O!.
````
#### instance_id_5413

- Execution match: None
- Token F1: 0.373

Question:

Look for the comments of the Article that is not related  to the Report with the  report_id  5049b80a2935f95cc95cf14dbfb8c610!

Reference Cypher:

````cypher
MATCH (n:Article), (:Report {report_id: '5049b80a2935f95cc95cf14dbfb8c610'}) WHERE NOT (n) --> (:Report) RETURN n.comments
````

Generated output:

````text
The query should return the comments of the Article that is not related to the Report with the report_id 5049b80a2935f95cc95cf14dbfb8c610!

Here is the Cypher query:

```
MATCH (comment)
  CALL (report_id)
  UNWIND (comment)
  CREATE (comment)
  MERGE (comment)
  RETURN
```

This query will return the comments of the Article that is not related to the Report with the report_id 5049b80a2935f95cc95cf14dbfb8c610!
````
#### instance_id_15057

- Execution match: None
- Token F1: 0.361

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
The query is:

"How many unique relationships originate from Article where abstract is The Wakimoto construction for the quantum affine algebra U_q(\hat{sl}_2)
admits a reduction to the q-deformed parafermion algebras."

The query is:

"The Wakimoto construction for the quantum affine algebra U_q(\hat{sl}_2)
admits a reduction to the q-deformed parafermion algebras."

The query is:

"How many unique relationships originate from Article where abstract is The Wakimoto construction for the quantum affine algebra U_q(\hat{sl}_2)
admits a reduction to the q-deformed parafermion algebras."

The query is:

"The Wakimoto construction for the quantum affine algebra U_q(\hat{sl}_2)
admits a reduction to the q-deformed parafermion algebras."

The query is:

"How many unique relationships originate from Article where abstract is The Wakimoto construction for the quantum affine algebra U_q(\hat{sl}_2)
admits a reduction to the
````

### False Positives examples

No examples.

### False Negatives examples

No examples.

## Database-alias breakdown

| Alias | Samples | Exact lexical matches | Exact-match rate |
|---|---:|---:|---:|
| <unset> | 32 | 0 | 0.0% |
| neo4jlabs_demo_db_bluesky | 1 | 0 | 0.0% |
| neo4jlabs_demo_db_buzzoverflow | 3 | 0 | 0.0% |
| neo4jlabs_demo_db_gameofthrones | 2 | 0 | 0.0% |
| neo4jlabs_demo_db_movies | 3 | 0 | 0.0% |
| neo4jlabs_demo_db_twitch | 9 | 0 | 0.0% |

## Reference-complexity breakdown

| Recognized reference features | Samples | Exact lexical matches | Exact-match rate |
|---:|---:|---:|---:|
| 3 | 1 | 0 | 0.0% |
| 4 | 7 | 0 | 0.0% |
| 5 | 11 | 0 | 0.0% |
| 6 | 15 | 0 | 0.0% |
| 7 | 4 | 0 | 0.0% |
| 8 | 4 | 0 | 0.0% |
| 9 | 5 | 0 | 0.0% |
| 10 | 3 | 0 | 0.0% |

## Generation errors

- None

## Representative examples

### Complex Exact Matches

No examples.

### Closest Cypher Non Matches

#### instance_id_4046 — cypher_shaped_non_match

- Token F1: 0.650
- Reference features: match, node_label, property_filter, relationship_pattern, return
- Predicted features: where
- Omitted reference features: match, node_label, property_filter, relationship_pattern, return
- Introduced features: where

Question:

Is there a path connecting Author where first_name is Bernhard and Topic, for which description is Focusing on techniques and concepts related to transformations, solutions, and properties of linear equations and matrices, including Jordan normal form, eigenvalues, eigenvectors, diagonalization, and eigenformulations.?

Reference Cypher:

````cypher
MATCH (a:Author{first_name:'Bernhard'}), (b:Topic{description:'Focusing on techniques and concepts related to transformations, solutions, and properties of linear equations and matrices, including Jordan normal form, eigenvalues, eigenvectors, diagonalization, and eigenformulations.'}) RETURN EXISTS((a)-[*]-(b)) AS pathExists
````

Generated output:

````text
Yes, there is a path connecting Author where first_name is Bernhard and Topic, for which description is Focusing on techniques and concepts related to transformations, solutions, and properties of linear equations and matrices, including Jordan normal form, eigenvalues, eigenvectors, diagonalization, and eigenformulations.
````

#### instance_id_40097 — cypher_shaped_non_match

- Token F1: 0.402
- Reference features: match, node_label, ordering, pagination, property_filter, relationship_pattern, return, with
- Predicted features: node_label, relationship_pattern
- Omitted reference features: match, ordering, pagination, property_filter, return, with
- Introduced features: none

Question:

List the roles played by actors in the first 3 movies directed by Nancy Meyers.

Reference Cypher:

````cypher
MATCH (director:Person {name: "Nancy Meyers"})-[:DIRECTED]->(movie:Movie) WITH movie ORDER BY movie.released LIMIT 3 MATCH (actor:Person)-[actedIn:ACTED_IN]->(movie) RETURN movie.title AS MovieTitle, actor.name AS ActorName, actedIn.roles AS Roles
````

Generated output:

````text
Movie:
- **The Matrix**
- **The Matrix**
- **The Matrix**

Relationship:
(:Person)-[:ACTED_IN]->(:Movie)
(:Person)-[:DIRECTED]->(:Movie)
(:Person)-[:PRODUCED]->(:Movie)
(:Person)-[:WROTE]->(:Movie)
(:Person)-[:FOLLOWS]->(:Person)
(:Person)-[:REVIEWED]->(:Movie)

Answer: The first 3 movies played by Nancy Meyers.
````

#### instance_id_19443 — cypher_shaped_non_match

- Token F1: 0.382
- Reference features: match, node_label, return, where, with
- Predicted features: match, property_filter, where, with
- Omitted reference features: node_label, return
- Introduced features: property_filter

Question:

Find the title and the comments for those Article where title starts with O!

Reference Cypher:

````cypher
MATCH (n:Article) WHERE n.title STARTS WITH 'O' RETURN n.title AS title, n.comments AS comments
````

Generated output:

````text
Query: MATCH Article {title: "O!"}

Output:
Title: O!
Comments: O!

Explanation: The query MATCH Article {title: "O!"} returns the title and comments for the Article where the title starts with O!.
````

#### instance_id_5413 — cypher_shaped_non_match

- Token F1: 0.373
- Reference features: match, node_label, property_filter, return, where
- Predicted features: match, return, with, write_clause
- Omitted reference features: node_label, property_filter, where
- Introduced features: with, write_clause

Question:

Look for the comments of the Article that is not related  to the Report with the  report_id  5049b80a2935f95cc95cf14dbfb8c610!

Reference Cypher:

````cypher
MATCH (n:Article), (:Report {report_id: '5049b80a2935f95cc95cf14dbfb8c610'}) WHERE NOT (n) --> (:Report) RETURN n.comments
````

Generated output:

````text
The query should return the comments of the Article that is not related to the Report with the report_id 5049b80a2935f95cc95cf14dbfb8c610!

Here is the Cypher query:

```
MATCH (comment)
  CALL (report_id)
  UNWIND (comment)
  CREATE (comment)
  MERGE (comment)
  RETURN
```

This query will return the comments of the Article that is not related to the Report with the report_id 5049b80a2935f95cc95cf14dbfb8c610!
````

#### instance_id_7777 — cypher_shaped_non_match

- Token F1: 0.310
- Reference features: aggregation, match, node_label, property_filter, relationship_pattern, return, where
- Predicted features: property_filter, return, where, with
- Omitted reference features: aggregation, match, node_label, relationship_pattern
- Introduced features: with

Question:

Find abstract of the Article and return it along with the count of Journal that are linked via PUBLISHED_IN where year is 2002!

Reference Cypher:

````cypher
MATCH (n:Article) -[r:PUBLISHED_IN]->(m:Journal) WHERE r.year = '2002' RETURN n.abstract AS abstract, count(m) AS count
````

Generated output:

````text
Relevant node labels and their properties (with datatypes) are:
Article {abstract: STRING}
Journal {}

Relevant relationships are:
{'start': Article, 'type': PUBLISHED_IN, 'end': Journal }

Relevant relationship properties (with datatypes) are:
PUBLISHED_IN {year: STRING}

Question:
Find abstract of the Article and return it along with the count of Journal that are linked via PUBLISHED_IN where year is 2002!
````

### Prose Or Markdown Output Examples

#### instance_id_22944 — prose_or_markdown_output

- Token F1: 0.209
- Reference features: match, node_label, property_filter, return, where
- Predicted features: none
- Omitted reference features: match, node_label, property_filter, return, where
- Introduced features: none

Question:

Identify characters who belong to community 579.

Reference Cypher:

````cypher
MATCH (c:Character) WHERE c.community = 579 RETURN c
````

Generated output:

````text
Based on the schema provided, the character who belongs to community 579 is:

```
book45PageRank: 0.15000000000000002, FastFreq: 0.15000000000000002, Community: 579
```

So the character who belongs to community 579 is the character who has the highest Freq (1500) and the highest FastFreq (1500).
````

#### instance_id_8035 — prose_or_markdown_output

- Token F1: 0.086
- Reference features: match, node_label, property_filter, relationship_pattern, return, where, with
- Predicted features: none
- Omitted reference features: match, node_label, property_filter, relationship_pattern, return, where, with
- Introduced features: none

Question:

Search for the journal_id in Journal that is linked through a PUBLISHED_IN relationship with Article where title is Classification of Subsystems for Local Nets with Trivial Superselection
  Structure and PUBLISHED_IN has meta on 217!

Reference Cypher:

````cypher
MATCH (n:Article) -[pu:PUBLISHED_IN {meta : '217'}]->(m) WHERE n.title='Classification of Subsystems for Local Nets with Trivial Superselection   Structure' RETURN m.journal_id
````

Generated output:

````text
Query:
PUBLISHED_IN: PUBLISHED_IN: PUBLISHED_IN: PUBLISHED_IN: PUBLISHED_IN: PUBLISHED_IN: PUBLISHED_IN: PUBLISHED_IN: PUBLISHED_IN: PUBLISHED_IN: PUBLISHED_IN: PUBLISHED_IN: PUBLISHED_IN: PUBLISHED_IN: PUBLISHED_IN: PUBLISHED_IN: PUBLISHED_IN: PUBLISHED_IN: PUBLISHED_IN: PUBLISHED_IN: PUBLISHED_IN: PUBLISHED_IN: PUBLISHED_IN: PUBLISHED_IN: PUBLISHED_IN: PUBLISHED_IN: PUBLISHED_IN: PUBLISHED_IN: PUBLISHED_IN: PUBLISHED_IN: PUBLISHED_IN: PUBLISHED_IN: PUBLISHED_IN: PUBLISHED_IN: PUBLISHED_IN: PUBLISHED_IN: PU
````

#### instance_id_25776 — prose_or_markdown_output

- Token F1: 0.084
- Reference features: aggregation, match, node_label, relationship_pattern, return, where
- Predicted features: none
- Omitted reference features: aggregation, match, node_label, relationship_pattern, return, where
- Introduced features: none

Question:

What are the total view counts for streams that have moderators?

Reference Cypher:

````cypher
MATCH (s:Stream) WHERE exists{(s)-[:MODERATOR]->()} RETURN sum(s.total_view_count) AS totalViewCountForModeratedStreams
````

Generated output:

````text
Based on the schema, the total view counts for streams that have moderators are:

- `:Stream`
- `:Game`
- `:Language`
- `:User`
- `:Team`
- `:Chatter`
- `:HAS_TEAM`
- `:CHATTER`
- `:MODERATOR`
- `:CHATTER`
- `:MODERATOR`
- `:User`
- `:MODERATOR`
- `:Stream`
- `:HAS_TEAM`
- `:CHATTER`
- `:MODERATOR`
- `:CHATTER`
- `:MODERATOR`
- `:User`
- `:MODERATOR`
- `:Stream`
- `:HAS_TEAM`
- `:CHATTER`
- `:MODERATOR`
- `:CHATTER`
- `:MODERATOR`
- `:User`
- `:MODERATOR`
- `:Stream`
- `:HAS_TEAM`
- `:CH
````

#### instance_id_38257 — prose_or_markdown_output

- Token F1: 0.074
- Reference features: match, node_label, relationship_pattern, return
- Predicted features: none
- Omitted reference features: match, node_label, relationship_pattern, return
- Introduced features: none

Question:

List the movies that have been both directed and produced by the same person.

Reference Cypher:

````cypher
MATCH (p:Person)-[:DIRECTED]->(m:Movie)<-[:PRODUCED]-(p) RETURN m.title AS movie
````

Generated output:

````text
Movie:
Movie:
Movie:
Movie:
Movie:
Movie:
Movie:
Movie:
Movie:
Movie:
Movie:
Movie:
Movie:
Movie:
Movie:
Movie:
Movie:
Movie:
Movie:
Movie:
Movie:
Movie:
Movie:
Movie:
Movie:
Movie:
Movie:
Movie:
Movie:
Movie:
Movie:
Movie:
Movie:
Movie:
Movie:
Movie:
Movie:
Movie:
Movie:
Movie:
Movie:
Movie:
Movie:
Movie:
Movie:
Movie:
Movie:
Movie:
Movie:
Movie:
Movie:
Movie:
Movie:
Movie:
Movie:
Movie:
Movie:
Movie:
Movie:
Movie:
Movie:
Movie:
Movie:
Movie:
````

#### instance_id_12057 — prose_or_markdown_output

- Token F1: 0.064
- Reference features: aggregation, match, node_label, property_filter, relationship_pattern, return
- Predicted features: none
- Omitted reference features: aggregation, match, node_label, property_filter, relationship_pattern, return
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
1. Article
2. Article
3. Article
4. Article
5. Article
6. Article
7. Article
8. Article
9. Article
10. Article
11. Article
12. Article
13. Article
14. Article
15. Article
16. Article
17. Article
18. Article
19. Article
20. Article
21. Article
22. Article
23. Article
24. Article
25. Article
26. Article
27. Article
28. Article
29. Article
30. Article
31. Article
32. Article
33. Article
34. Article
35. Article
36. Article
37. Article
38. Article
39. Article
40. Article
41. Article
42. Article
43. Article
44. Article
45. Article
46. Article
47. Article
48. Article
49. Article
50. Article
51. Article
52. Article
53. Article
````

### Sql Shaped Output Examples

#### instance_id_15057 — sql_shaped_output

- Token F1: 0.361
- Reference features: aggregation, distinct, match, node_label, pagination, property_filter, relationship_pattern, return, where, with
- Predicted features: where
- Omitted reference features: aggregation, distinct, match, node_label, pagination, property_filter, relationship_pattern, return, with
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
The query is:

"How many unique relationships originate from Article where abstract is The Wakimoto construction for the quantum affine algebra U_q(\hat{sl}_2)
admits a reduction to the q-deformed parafermion algebras."

The query is:

"The Wakimoto construction for the quantum affine algebra U_q(\hat{sl}_2)
admits a reduction to the q-deformed parafermion algebras."

The query is:

"How many unique relationships originate from Article where abstract is The Wakimoto construction for the quantum affine algebra U_q(\hat{sl}_2)
admits a reduction to the q-deformed parafermion algebras."

The query is:

"The Wakimoto construction for the quantum affine algebra U_q(\hat{sl}_2)
admits a reduction to the q-deformed parafermion algebras."

The query is:

"How many unique relationships originate from Article where abstract is The Wakimoto construction for the quantum affine algebra U_q(\hat{sl}_2)
admits a reduction to the
````

#### instance_id_30277 — sql_shaped_output

- Token F1: 0.293
- Reference features: aggregation, match, node_label, ordering, pagination, property_filter, relationship_pattern, return, where, with
- Predicted features: match, node_label, property_filter, with
- Omitted reference features: aggregation, ordering, pagination, relationship_pattern, return, where
- Introduced features: none

Question:

Find the question with the least number of upvotes and a score greater than the average score of questions tagged with 'aws-lambda'.

Reference Cypher:

````cypher
MATCH (t:Tag {name: 'aws-lambda'})<-[:TAGGED]-(q:Question) WITH avg(q.score) AS average_score MATCH (q:Question) WHERE q.score > average_score WITH q ORDER BY q.upVotes ASC RETURN q LIMIT 1
````

Generated output:

````text
Question:
Find the question with the least number of upvotes and a score greater than the average score of questions tagged with 'aws-lambda'.

Query:

```
MATCH (question)
  LEFT JOIN (
    (:Question)
    LEFT JOIN (
      (:Tag)
      LEFT JOIN (
        (:User)
      )
    )
  ON question.question_id = question.question_id
    AND question.user_id = question.user_id
    AND question.answer_id = question.answer_id
    AND question.score_above_average = question.score_above_average
    AND question.upvotes_above_average > question.upvotes_above_average
    AND question.downvotes_above_average > question.downvotes_above_average
    AND question.question_id = question.question_id
    AND question.user_id = question.user_id
    AND question.answer_id = question.answer_id
    AND question.score_above_average > question.score_above_average
    AND question.upvotes_above_average > question.upvotes_above_average
    AND question.
````

#### instance_id_12826 — sql_shaped_output

- Token F1: 0.271
- Reference features: distinct, match, node_label, property_filter, relationship_pattern, return
- Predicted features: distinct, match, return, where, with, write_clause
- Omitted reference features: node_label, property_filter, relationship_pattern
- Introduced features: where, with, write_clause

Question:

List the distinct properties of nodes that are 2 hops away from Report with report_no equal to PAM-780!

Reference Cypher:

````cypher
MATCH (a:Report{report_no:'PAM-780'})-[*2]->(n) RETURN DISTINCT properties(n) AS props
````

Generated output:

````text
Based on the schema, the distinct properties of nodes that are 2 hops away from Report with report_no equal to PAM-780! are:

```
report_no: "2 hops away from Report"
```

So the query output is:

```
SELECT report_no, MATCH, CALL, WITH, UNWIND, CREATE, MERGE, RETURN
FROM graph_schema.graph_nodes
WHERE report_no = PAM-780;
```
````

#### instance_id_4905 — sql_shaped_output

- Token F1: 0.259
- Reference features: match, node_label, property_filter, relationship_pattern, return
- Predicted features: property_filter, return, where
- Omitted reference features: match, node_label, relationship_pattern
- Introduced features: where

Question:

Is there a path connecting Report where report_id is 3fa3ec8100d88908b00d139dacdedb6a and UpdateDate, for which update_date is 2014-11-11?

Reference Cypher:

````cypher
MATCH (a:Report{report_id:'3fa3ec8100d88908b00d139dacdedb6a'}), (b:UpdateDate{update_date:'2014-11-11'}) RETURN EXISTS((a)-[*]-(b)) AS pathExists
````

Generated output:

````text
Yes, there is a path connecting Report where report_id is 3fa3ec8100d88908b00d139dacdedb6a and UpdateDate is 2014-11-11.

The query would be:

```
SELECT Report.report_id, Report.update_date, UpdateDate.date
FROM Report
WHERE Report.report_id = 3fa3ec8100d88908b00d139dacdedb6a
```

This query will return the report ID, update date, and update date for all reports where the report_id is 3fa3ec8100d88908b00d139dacdedb6a.
````

#### instance_id_19093 — sql_shaped_output

- Token F1: 0.244
- Reference features: distinct, match, node_label, property_filter, return, where
- Predicted features: distinct, ordering, pagination, return, where, write_clause
- Omitted reference features: match, node_label, property_filter
- Introduced features: ordering, pagination, write_clause

Question:

Fetch the distinct values of the report_id from Report where either report_no is none provided or report_id is not null!

Reference Cypher:

````cypher
MATCH (n:Report) WHERE n.report_no = 'none provided' OR n.report_id IS NOT NULL RETURN DISTINCT n.report_id AS report_id
````

Generated output:

````text
```python
def fetch_report_values(graph, report_id):
    query = f"SELECT report_id, report_no FROM {graph.graph_name}"
    query += f" WHERE report_id IS NOT NULL AND report_no IS NOT NULL"
    query += f" ORDER BY report_id DESC LIMIT 1"
    return query.split()
```

This function takes a graph schema and a report ID as input, and returns a list of distinct report IDs. It uses the `split()` method to split the query into a list of strings, and then uses the `ORDER BY` clause to sort the list in descending order based on the report ID. The `limit` parameter is set to 1 to ensure that the query is executed in descending order.
````

## Limitations

- Exact match and token overlap are lexical metrics, not semantic or execution equivalence.
- Feature extraction uses conservative regular-expression rules, not a Cypher parser.
- A non-exact result can still be semantically valid; this report does not determine that.
