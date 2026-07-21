# Evaluation Run Comparison

## Aggregate metrics

| Run | Samples | Exact match | Token precision | Token recall | Token F1 | Failed generations |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| with-syntax-check (baseline) | 50 | 0.0000 | 0.1290 | 0.3486 | 0.1732 | 0 |
| with-syntax-check (trained) | 50 | 0.4400 | 0.9152 | 0.9211 | 0.9115 | 0 |
| without-syntax-check (baseline) | 50 | 0.0000 | 0.1290 | 0.3486 | 0.1732 | 0 |
| without-syntax-check (trained) | 50 | 0.2800 | 0.8494 | 0.8452 | 0.8273 | 0 |

## Pairwise changes

### with-syntax-check (trained) minus with-syntax-check (baseline)

Shared samples: 50

| Exact-match change | Token F1 change | New matches | Lost matches |
| ---: | ---: | ---: | ---: |
| +0.4400 | +0.7383 | 22 | 0 |

### without-syntax-check (baseline) minus with-syntax-check (baseline)

Shared samples: 50

| Exact-match change | Token F1 change | New matches | Lost matches |
| ---: | ---: | ---: | ---: |
| +0.0000 | +0.0000 | 0 | 0 |

### without-syntax-check (trained) minus with-syntax-check (baseline)

Shared samples: 50

| Exact-match change | Token F1 change | New matches | Lost matches |
| ---: | ---: | ---: | ---: |
| +0.2800 | +0.6542 | 14 | 0 |

### without-syntax-check (baseline) minus with-syntax-check (trained)

Shared samples: 50

| Exact-match change | Token F1 change | New matches | Lost matches |
| ---: | ---: | ---: | ---: |
| -0.4400 | -0.7383 | 0 | 22 |

### without-syntax-check (trained) minus with-syntax-check (trained)

Shared samples: 50

| Exact-match change | Token F1 change | New matches | Lost matches |
| ---: | ---: | ---: | ---: |
| -0.1600 | -0.0841 | 1 | 9 |

### without-syntax-check (trained) minus without-syntax-check (baseline)

Shared samples: 50

| Exact-match change | Token F1 change | New matches | Lost matches |
| ---: | ---: | ---: | ---: |
| +0.2800 | +0.6542 | 14 | 0 |

## Limitation

These comparisons measure lexical metrics. A lexical gain does not by itself establish execution or semantic equivalence.
