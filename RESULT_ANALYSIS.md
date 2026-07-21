# Result analysis

## Run comparison

```
$ make compare-runs
PYTHONPATH=/home/demo/Documents/260717_fraunhofer_iais uv run python scripts/compare_runs.py --runs-dir outputs/runs --output-dir outputs/runs/comparisons
Compared 4 runs.
Run                              Exact match  Precision  Recall      F1
-------------------------------  -----------  ---------  ------  ------
with-syntax-check (baseline)          0.0000     0.1290  0.3486  0.1732
with-syntax-check (trained)           0.4400     0.9152  0.9211  0.9115
without-syntax-check (baseline)       0.0000     0.1290  0.3486  0.1732
without-syntax-check (trained)        0.2800     0.8494  0.8452  0.8273
```

## Baseline evaluation

None of the generated Cyphers are Cypher only, i.e., zero exact matches, zero syntax checks passed.

```json
  "question": "What are the top 5 tags used in questions with a score less than zero?",
  "reference_cypher": "MATCH (q:Question)-[:TAGGED]->(t:Tag) WHERE q.score < 0 RETURN t.name, count(q) AS usage ORDER BY usage DESC LIMIT 5",
  "database_reference_alias": "neo4jlabs_demo_db_buzzoverflow",
  "predicted_cypher": "Based on the schema, the top 5 tags used in questions with a score less than zero are: ..."
```

## Observed examples in outputs/runs/with-syntax-check/trained_results.md

### True positive: Exact match or eval match, correct cypher

All good ones, e.g.,

#### Example 1: Exact match

```json
  "instance_id": "instance_id_13430",
  "question": "Which nodes are connected to UpdateDate where update_date is 2008-01-29, and also to another node?",
  "schema": "Graph schema: Relevant node labels and their properties (with datatypes) are:
UpdateDate {update_date: DATE}",
  "reference_cypher": "MATCH (a:UpdateDate{update_date:'2008-01-29'})-[r]->(n), (n)-[s]->(m) RETURN labels(n) AS Interim, labels(m) AS Target",
  "predicted_cypher": "MATCH (a:UpdateDate{update_date:'2008-01-29'})-[r]->(n), (n)-[s]->(m) RETURN labels(n) AS Interim, labels(m) AS Target",
  "metrics": {
    "exact_match": true,
    "token_precision": 1,
    "token_recall": 1,
    "token_f1": 1,
    "execution_match": null
  },
```

#### Example 2: Eval match

Unnecessary additions were invented, but the query works.

```json
  "instance_id": "instance_id_23366",
  "question": "List the top 5 movies with a tagline containing 'football'.",
  "schema": "Node properties:
- **Movie**
  - `title`: STRING Example: \"The Matrix\"
  - `votes`: INTEGER Min: 1, Max: 5259
  - `tagline`: STRING Example: \"Welcome to the Real World\"
  - `released`: INTEGER Min: 1975, Max: 2012
- **Person**
  - `born`: INTEGER Min: 1929, Max: 1996
  - `name`: STRING Example: \"Keanu Reeves\"
Relationship properties:
- **ACTED_IN**
  - `roles: LIST` Min Size: 1, Max Size: 6
- **REVIEWED**
  - `summary: STRING` Available options: ['Pretty funny at times', 'A solid romp', 'Silly, but fun', 'You had me at Jerry', 'An amazing journey', 'Slapstick redeemed only by the Robin Williams and ', 'Dark, but compelling', 'The coolest football movie ever', 'Fun, but a little far fetched']
  - `rating: INTEGER` Min: 45, Max:  100
The relationships:
(:Person)-[:ACTED_IN]->(:Movie)
(:Person)-[:DIRECTED]->(:Movie)
(:Person)-[:PRODUCED]->(:Movie)
(:Person)-[:WROTE]->(:Movie)
(:Person)-[:FOLLOWS]->(:Person)
(:Person)-[:REVIEWED]->(:Movie)",
  "reference_cypher": "MATCH (m:Movie) WHERE m.tagline CONTAINS 'football' RETURN m ORDER BY m.released DESC LIMIT 5",
  "predicted_cypher": "MATCH (m:Movie) WHERE m.tagline CONTAINS 'football' RETURN m.title, m.tagline, m.released, m.votes ORDER BY m.votes DESC LIMIT 5",
  "metrics": {
    "exact_match": false,
    "token_precision": 0.6111111111111112,
    "token_recall": 1,
    "token_f1": 0.7586206896551725,
    "execution_match": true
  },
```

### True negative: No exact match and no eval match, wrong cypher

All bad ones, e.g.,

#### Example 1: Wrong LIMIT added

```json
  "instance_id": "instance_id_33953",
  "question": "Find the streams that were created before 2018 and have more than 5,000 followers.",
  "schema": "Node properties:
- **Stream**
  - `createdAt`: DATE_TIME Min: 2007-05-22T10:39:53.259969Z, Max: 2021-05-09T14:16:40.370294Z
  - `id`: STRING Example: \"129004176\"
  - `description`: STRING Example: \"Welcome to my Channel, I'm Big Chase, 31 living in\"
  - `url`: STRING Example: \"https://www.twitch.tv/itsbigchase\"
  - `name`: STRING Example: \"itsbigchase\"
  - `followers`: INTEGER Min: 0, Max: 10243195
  - `total_view_count`: INTEGER Min: 21, Max: 1451487256
- **Game**
  - `name`: STRING Example: \"Rust\"
- **Language**
  - `name`: STRING Example: \"en\"
- **User**
  - `name`: STRING Example: \"itsbigchase\"
- **Team**
  - `createdAt`: DATE_TIME Min: 2011-10-11T23:59:43.548701Z, Max: 2021-05-07T17:19:09.946382Z
  - `name`: STRING Example: \"ESO Stream Team\"
  - `id`: STRING Example: \"5893\"
Relationship properties:

The relationships:
(:Stream)-[:PLAYS]->(:Game)
(:Stream)-[:HAS_LANGUAGE]->(:Language)
(:Stream)-[:MODERATOR]->(:Stream)
(:Stream)-[:MODERATOR]->(:User)
(:Stream)-[:CHATTER]->(:Stream)
(:Stream)-[:CHATTER]->(:User)
(:Stream)-[:HAS_TEAM]->(:Team)
(:Stream)-[:VIP]->(:Stream)
(:Stream)-[:VIP]->(:User)
(:User)-[:CHATTER]->(:Stream)
(:User)-[:CHATTER]->(:User)
(:User)-[:MODERATOR]->(:Stream)
(:User)-[:MODERATOR]->(:User)",
  "reference_cypher": "MATCH (s:Stream) WHERE s.createdAt < datetime('2018-01-01T00:00:00.000000Z') AND s.followers > 5000 RETURN s",
  "database_reference_alias": "neo4jlabs_demo_db_twitch",
  "predicted_cypher": "MATCH (s:Stream) WHERE s.createdAt < datetime('2018-01-01T00:00:00Z') AND s.followers > 5000 RETURN s.name AS stream_name, count(s) AS stream_count ORDER BY stream_count DESC LIMIT 1",
  "metrics": {
    "exact_match": false,
    "token_precision": 0.64,
    "token_recall": 0.9696969696969697,
    "token_f1": 0.7710843373493975,
    "execution_match": null
  },
```

#### Example 2: Wrong relations

```json
{
  "instance_id": "instance_id_26310",
  "question": "What are the top 5 tags used in questions with a score less than zero?",
  "schema": "Node properties:
- **Question**
  - `favorites`: INTEGER Example: \"0\"
  - `answered`: BOOLEAN
  - `text`: STRING Example: \"### This is:  Bug    ### Specifications  OS: Win10\"
  - `link`: STRING Example: \"https://stackoverflow.com/questions/62224586/playg\"
  - `createdAt`: DATE_TIME Min: 2020-06-05T16:57:19Z, Max: 2020-06-05T21:49:16Z
  - `title`: STRING Example: \"Playground is not loading with apollo-server-lambd\"
  - `id`: INTEGER Min: 62220505, Max: 62224586
  - `upVotes`: INTEGER Example: \"0\"
  - `score`: INTEGER Example: \"-1\"
  - `downVotes`: INTEGER Example: \"1\"
- **Tag**
  - `name`: STRING Example: \"aws-lambda\"
- **User**
  - `image`: STRING Example: \"https://lh3.googleusercontent.com/-NcFYSuXU0nk/AAA\"
  - `link`: STRING Example: \"https://stackoverflow.com/users/10251021/alexandre\"
  - `id`: INTEGER Min: 751, Max: 13681006
  - `reputation`: INTEGER Min: 1, Max: 420137
  - `display_name`: STRING Example: \"Alexandre Le\"
Relationship properties:

The relationships:
(:Question)-[:TAGGED]->(:Tag)
(:User)-[:ASKED]->(:Question)",
  "reference_cypher": "MATCH (q:Question)-[:TAGGED]->(t:Tag) WHERE q.score < 0 RETURN t.name, count(q) AS usage ORDER BY usage DESC LIMIT 5",
  "predicted_cypher": "MATCH (q:Question) WHERE q.score < 0 RETURN q.name, q.tag ORDER BY q.score DESC LIMIT 5",
  "metrics": {
    "exact_match": false,
    "token_precision": 0.8214285714285714,
    "token_recall": 0.5609756097560976,
    "token_f1": 0.6666666666666667,
    "execution_match": null
  },
```

#### Example 3: Wrong relations

```json
  "instance_id": "instance_id_36940",
  "question": "Identify streams that have moderators who are also VIPs.",
  "schema": "Node properties:
- **Stream**
  - `createdAt`: DATE_TIME Min: 2007-05-22T10:39:53.259969Z, Max: 2021-05-09T14:16:40.370294Z
  - `id`: STRING Example: \"129004176\"
  - `description`: STRING Example: \"Welcome to my Channel, I'm Big Chase, 31 living in\"
  - `url`: STRING Example: \"https://www.twitch.tv/itsbigchase\"
  - `name`: STRING Example: \"itsbigchase\"
  - `followers`: INTEGER Min: 0, Max: 10243195
  - `total_view_count`: INTEGER Min: 21, Max: 1451487256
- **Game**
  - `name`: STRING Example: \"Rust\"
- **Language**
  - `name`: STRING Example: \"en\"
- **User**
  - `name`: STRING Example: \"itsbigchase\"
- **Team**
  - `createdAt`: DATE_TIME Min: 2011-10-11T23:59:43.548701Z, Max: 2021-05-07T17:19:09.946382Z
  - `name`: STRING Example: \"ESO Stream Team\"
  - `id`: STRING Example: \"5893\"
Relationship properties:

The relationships:
(:Stream)-[:PLAYS]->(:Game)
(:Stream)-[:HAS_LANGUAGE]->(:Language)
(:Stream)-[:MODERATOR]->(:Stream)
(:Stream)-[:MODERATOR]->(:User)
(:Stream)-[:CHATTER]->(:Stream)
(:Stream)-[:CHATTER]->(:User)
(:Stream)-[:HAS_TEAM]->(:Team)
(:Stream)-[:VIP]->(:Stream)
(:Stream)-[:VIP]->(:User)
(:User)-[:CHATTER]->(:Stream)
(:User)-[:CHATTER]->(:User)
(:User)-[:MODERATOR]->(:Stream)
(:User)-[:MODERATOR]->(:User)",
  "reference_cypher": "MATCH (s:Stream)<-[:MODERATOR]-(m:User)-[:VIP]->(s) RETURN s.name AS stream, m.name AS moderator_and_vip",
  "predicted_cypher": "MATCH (s:Stream)-[:MODERATOR]->(m:VIP) WHERE m.name =~'^[vip]->(:Stream)' RETURN s",
  "metrics": {
    "exact_match": false,
    "token_precision": 0.8823529411764706,
    "token_recall": 0.75,
    "token_f1": 0.8108108108108107,
    "execution_match": null
  },
```

#### Example 4: Wrong relations; failed eval match available

```json
  "instance_id": "instance_id_38257",
  "question": "List the movies that have been both directed and produced by the same person.",
  "schema": "Node properties:
- **Movie**
  - `title`: STRING Example: \"The Matrix\"
  - `votes`: INTEGER Min: 1, Max: 5259
  - `tagline`: STRING Example: \"Welcome to the Real World\"
  - `released`: INTEGER Min: 1975, Max: 2012
- **Person**
  - `born`: INTEGER Min: 1929, Max: 1996
  - `name`: STRING Example: \"Keanu Reeves\"
Relationship properties:
- **ACTED_IN**
  - `roles: LIST` Min Size: 1, Max Size: 6
- **REVIEWED**
  - `summary: STRING` Available options: ['Pretty funny at times', 'A solid romp', 'Silly, but fun', 'You had me at Jerry', 'An amazing journey', 'Slapstick redeemed only by the Robin Williams and ', 'Dark, but compelling', 'The coolest football movie ever', 'Fun, but a little far fetched']
  - `rating: INTEGER` Min: 45, Max:  100
The relationships:
(:Person)-[:ACTED_IN]->(:Movie)
(:Person)-[:DIRECTED]->(:Movie)
(:Person)-[:PRODUCED]->(:Movie)
(:Person)-[:WROTE]->(:Movie)
(:Person)-[:FOLLOWS]->(:Person)
(:Person)-[:REVIEWED]->(:Movie)",
  "reference_cypher": "MATCH (p:Person)-[:DIRECTED]->(m:Movie)<-[:PRODUCED]-(p) RETURN m.title AS movie",
  "predicted_cypher": "MATCH (p:Person)-[:DIRECTED]->(m:Movie) WHERE p.name = 'Keanu Reeves' AND m.title = 'The Matrix' RETURN m.title",
  "metrics": {
    "exact_match": false,
    "token_precision": 0.6388888888888888,
    "token_recall": 0.6764705882352942,
    "token_f1": 0.6571428571428571,
    "execution_match": false
  },
```

### False negative: No exact match and no eval match, but correct cypher

Exact matches often miss correct cyphers. If eval matches were possible for all Cyphers, this would be resolved.

#### Example 1

```json
  "instance_id": "instance_id_3190",
  "question": "What are the names and ages of editors?",
  "schema": "{\"Editor\": {\"count\": 9, \"labels\": [], \"properties\": {\"Name\": {\"unique\": false, \"indexed\": false, \"type\": \"STRING\", \"existence\": false}, \"Age\": {\"unique\": false, \"indexed\": false, \"type\": \"FLOAT\", \"existence\": false}, \"Editor_ID\": {\"unique\": false, \"indexed\": false, \"type\": \"INTEGER\", \"existence\": false}}, \"type\": \"node\", \"relationships\": {\"EDited_BY\": {\"count\": 7, \"direction\": \"in\", \"labels\": [\"Journal\"], \"properties\": {\"Work_Type\": {\"indexed\": false, \"type\": \"STRING\", \"existence\": false, \"array\": false}}}}}, \"Journal\": {\"count\": 16, \"labels\": [], \"properties\": {\"Sales\": {\"unique\": false, \"indexed\": false, \"type\": \"INTEGER\", \"existence\": false}, \"Theme\": {\"unique\": false, \"indexed\": false, \"type\": \"STRING\", \"existence\": false}, \"Date\": {\"unique\": false, \"indexed\": false, \"type\": \"STRING\", \"existence\": false}, \"Journal_ID\": {\"unique\": false, \"indexed\": false, \"type\": \"INTEGER\", \"existence\": false}}, \"type\": \"node\", \"relationships\": {\"EDited_BY\": {\"count\": 0, \"direction\": \"out\", \"labels\": [\"Editor\"], \"properties\": {\"Work_Type\": {\"indexed\": false, \"type\": \"STRING\", \"existence\": false, \"array\": false}}}}}, \"EDited_BY\": {\"count\": 7, \"properties\": {\"Work_Type\": {\"indexed\": false, \"type\": \"STRING\", \"existence\": false, \"array\": false}}, \"type\": \"relationship\"}}",
  "reference_cypher": "MATCH (e:Editor) RETURN e.Name, e.Age",
  "predicted_cypher": "MATCH (e:Editor) RETURN e.Name AS Editor_Name, e.Age AS Editor_Age",
  "metrics": {
    "exact_match": false,
    "token_precision": 0.7777777777777778,
    "token_recall": 1,
    "token_f1": 0.8750000000000001
  },
```

  Possible code improvement for exact matching: Remove aliases from cyphers before comparison, flag as alias mismatch.
  Possible improvement for eval matching: Ensure there are reference databases for all reference cyphers.

#### Example 2

```json
  "instance_id": "instance_id_14109",
  "question": "Find the Article for which comments is 21 pages, AMS-LaTeX!",
  "schema": "Graph schema: Relevant node labels and their properties (with datatypes) are:
Article {comments: STRING}",
  "reference_cypher": "MATCH (n:Article {comments:'21 pages, AMS-LaTeX'}) RETURN n",
  "predicted_cypher": "MATCH (n:Article {comments: '21 pages, AMS-LaTeX'}) RETURN n",
  "metrics": {
    "exact_match": false,
    "token_precision": 1,
    "token_recall": 1,
    "token_f1": 1,
    "execution_match": null
  },
```

  Possible code improvement for exact matching: Remove whitespaces, flag as formatting mismatch.

### False positive: Eval match, but wrong Cypher.

False positive: Generated Cypher gives correct results by coincidence and passes the evaluation match.
Measures: Generate random or better systematic evaluation match test sets to avoid coincidental matches, or use multiple database references specifically designed to catch false positives.

Current status: No false positives observed with the few database executions that were done, insufficient data.