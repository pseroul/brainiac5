# Data Science & ML Pipeline

This document explains how Consensia uses machine learning to provide semantic similarity search and automatic Table of Contents generation. It is aimed at developers who want to understand, debug, or extend these features.

---

## Overview

Consensia treats each idea as a semantic unit, not just a text record. Two ML-powered features are built on top of this:

1. **Semantic similarity search** — "Find ideas similar to this one"
2. **Table of Contents generation** — "Automatically cluster all ideas into a meaningful hierarchy"

Both features rely on **dense vector embeddings**: a numerical representation of meaning that allows the system to measure conceptual proximity between ideas.

---

## Text Embedding

### Model

**Model:** `all-distilroberta-v1` (SentenceTransformer)

This is a distilled version of RoBERTa fine-tuned for sentence similarity. It produces 768-dimensional embeddings. It is a good balance between quality and speed/memory on constrained hardware (Raspberry Pi 4).

### Document Construction

Ideas are not embedded as raw text. Instead, the `format_text()` utility in `backend/utils.py` constructs a structured document string:

```python
format_text(title, content, tags)
# → "Title: My idea\nContent: Detailed description\nTags: ai; hardware; robotics"
```

This document is what the model encodes. Weighting all three fields (title, content, tags) in the same string gives the model richer context than title alone.

### Embedding Storage

Embeddings are stored in **ChromaDB** (`backend/chroma_client.py`), a persistent vector database running in-process (no separate server). The collection is named `"Ideas"` and the storage path is configurable via the `CHROMA_DB` environment variable.

Each idea is stored with:
- **ID:** the idea title (string)
- **Document:** the `format_text(...)` output
- **Metadata:** `{"title": idea_title}`

### Write Path

```mermaid
flowchart LR
    API["POST /ideas\nor PUT /ideas/{id}\nor DELETE /ideas/{id}"]
    SQLite["SQLite\n(synchronous)"]
    Pool["ThreadPoolExecutor\n(async)"]
    ChromaDB["ChromaDB\n(async)"]

    API --> SQLite
    API --> Pool
    Pool --> ChromaDB
```

SQLite writes are synchronous (blocking). ChromaDB writes are submitted to a thread pool so they do not block the HTTP response. There is a brief window after a create/update where SQLite and ChromaDB may be out of sync.

---

## Semantic Similarity Search

**Endpoint:** `GET /ideas/similar/{idea}`

**Flow:**

```mermaid
flowchart TD
    A["Request: GET /ideas/similar/My idea title"] --> B
    B["ChromaClient.get_similar_idea(idea, n_results=10)"]
    B --> C["ChromaDB.query(query_texts=[idea], n_results=10)"]
    C --> D["Returns top-10 most similar idea titles"]
    D --> E["data_handler: SELECT ideas WHERE title IN (...)"]
    E --> F["Response: List of IdeaItem"]
```

ChromaDB computes similarity using **cosine distance** between the query embedding and all stored embeddings. The query text is the idea title (not a full document) — ChromaDB re-encodes it at query time using the same `all-distilroberta-v1` model.

---

## Table of Contents Generation Pipeline

The TOC feature (`GET /toc/structure`, `POST /toc/update`) automatically groups all ideas into a two-level hierarchy: **Sections → Chapters → Ideas**.

### Full Pipeline

```mermaid
flowchart TD
    A["POST /toc/update\nor cold GET /toc/structure"] --> B
    B["ChromaClient.get_all_ideas(max_items=500)\n→ all embeddings + documents"]
    B --> C["UMAP\nDimensionality reduction\n768-d → 5-d\n15 neighbors, cosine metric"]
    C --> D["AgglomerativeClustering — Level 1 (Sections)\nWard linkage\nTry k = 5..10\nPick best silhouette score"]
    D --> E{"Section > 5 ideas?"}
    E -- Yes --> F["AgglomerativeClustering — Level 2 (Chapters)\nTry k = 2..4\nPick best silhouette score"]
    E -- No --> G["Ideas become direct children of section"]
    F --> H["TF-IDF Title Generation\nTop-3 non-redundant terms per cluster\nCapitalized: 'Machine Learning & Hardware'"]
    G --> H
    H --> I["TocTreeBuilder\nAssembles nested JSON tree"]
    I --> J["FileTocCache\nSaves to data/toc.json"]
    J --> K["Response: hierarchical list"]
```

### Step-by-step Explanation

#### 1. Fetch all embeddings

```python
ChromaClient.get_all_ideas(max_items=500)
# Returns: chromadb.GetResult with .documents, .ids, .embeddings
```

The raw 768-dimensional embeddings are used for clustering (not the document text).

#### 2. UMAP dimensionality reduction

UMAP (Uniform Manifold Approximation and Projection) reduces 768-d embeddings to 5 dimensions while preserving local structure. This makes clustering faster and more meaningful.

```python
umap.UMAP(n_neighbors=15, n_components=5, metric="cosine")
```

#### 3. Agglomerative clustering — Sections (Level 1)

```python
from sklearn.cluster import AgglomerativeClustering

# Tries k in [5, 10], picks k with highest silhouette score
AgglomerativeClustering(n_clusters=k, linkage="ward")
```

Ward linkage minimises intra-cluster variance, producing compact, well-separated clusters. Every idea is assigned to a cluster — no noise points (unlike HDBSCAN which was used in an earlier version).

#### 4. Agglomerative clustering — Chapters (Level 2)

For sections with more than 5 ideas, a second round of clustering subdivides them into 2–4 chapters:

```python
# Tries k in [2, 4], picks k with highest silhouette score
AgglomerativeClustering(n_clusters=k, linkage="ward")
```

#### 5. TF-IDF title generation

Each cluster is given an automatically generated title using TF-IDF:

```python
TfidfVectorizer(stop_words="english")
# Selects top-3 non-redundant terms by mean TF-IDF score
# Joins with " & ": "Machine Learning & Hardware & Robotics"
```

English stop words are filtered out. Redundancy filtering removes terms that are substrings of each other.

#### 6. Originality score

Each idea receives an **originality score** (0.0–1.0) representing how far it sits from its cluster centroid. Ideas with high originality are conceptually distant from the "typical" idea in their cluster — they may be outliers or uniquely creative.

```python
# originality = normalized distance from centroid within its cluster
```

#### 7. Tree assembly and caching

`TocTreeBuilder` assembles the nested JSON tree. `FileTocCache` writes it to `data/toc.json`. Subsequent `GET /toc/structure` calls serve the cached file without re-running the pipeline.

---

## Caching Strategy

| Event | Cache state |
|---|---|
| `GET /toc/structure` (cache exists) | Served from `data/toc.json` — no ML computation |
| `GET /toc/structure` (no cache) | Pipeline runs, result cached |
| `POST /toc/update` | Pipeline runs, cache overwritten |
| Idea created / updated / deleted | Cache is **not** invalidated automatically |

This means the TOC can be stale after idea mutations. Users must click "Update Structure" to refresh it.

---

## Regenerating Embeddings

If you change the embedding model or need to re-sync ChromaDB after a data migration, run:

```bash
cd backend
source venv/bin/activate
python data_handler.py -e
```

This iterates over all ideas in SQLite and re-inserts their embeddings into ChromaDB. SQLite is the source of truth — ChromaDB is always reconstructable from it.

---

## Design Alternatives Considered

### Why not HDBSCAN?

An earlier version used HDBSCAN (a density-based algorithm). It is still available as `EmbeddingAnalyzer` in `data_similarity.py` for backward compatibility. The current default is `ConstrainedClusteringAnalyzer` (Agglomerative), which was chosen because:

- HDBSCAN produces **noise points** — ideas that don't fit any cluster. These had to be handled as isolated leaf nodes, producing an uneven TOC.
- Agglomerative clustering guarantees every idea is in a cluster, producing a cleaner hierarchy.
- Silhouette-based k selection gives more predictable cluster counts.

### Why `all-distilroberta-v1`?

- Fast inference on CPU-only hardware (Raspberry Pi 4)
- Good multilingual capability
- Small model size vs. larger alternatives like `all-mpnet-base-v2`

To switch models, change the `model_name` in `chroma_client.py`, then run `python data_handler.py -e` to regenerate all embeddings.
