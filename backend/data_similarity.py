import re
import os
import json
import logging
import numpy as np
from typing import Any
from chroma_client import ChromaClient
import umap
from sklearn.cluster import AgglomerativeClustering
from sklearn.neighbors import LocalOutlierFactor
from sklearn.preprocessing import MinMaxScaler
from sklearn.feature_extraction.text import TfidfVectorizer
from utils import unformat_text

logger = logging.getLogger("uvicorn.error")


def save_toc_structure(structure) -> None:
        """
        Save the table of contents structure to a cache file for future use.
        
        This function serializes the hierarchical structure data and stores it in
        a JSON file so that the expensive generation process doesn't need to be
        repeated on every application startup or refresh.
        
        Args:
            structure (list[dict]): The hierarchical structure data to be cached.
                This should be the output from DataSimilarity.generate_toc_structure().
                
        Returns:
            None
        """
        try:
            # Save the raw structure data (which is JSON serializable)
            with open(os.getenv('TOC_CACHE_PATH'), 'w') as f:
                json.dump(structure, f)
        except Exception as e:
            logger.error(f"Error saving TOC structure: {e}")

def load_toc_structure():
    """
    Load the table of contents structure from cache file if it exists.
    
    This function attempts to read previously cached structure data from
    the cache file. If the file doesn't exist or is corrupted, it returns None.
    
    Returns:
        list[dict] or None: The cached structure data if available and valid,
            or None if no cache exists or if there was an error loading it.
    """
    try:
        if os.path.exists(os.getenv('TOC_CACHE_PATH')):
            with open(os.getenv('TOC_CACHE_PATH'), 'r') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Error loading TOC structure: {e}")
    return None

class DataSimilarity:
    """
    A class for ordering ideas.
    """
    
    def generate_toc_structure(self) -> list:
        """
        Generate a hierarchical table of contents structure from all data.
        
        Creates a tree-like structure organizing all data items hierarchically
        based on semantic similarities using clustering techniques.
        
        Returns:
            list: Hierarchical structure of data items
        """
        # Stream data in chunks to limit memory usage
        client = ChromaClient()
        data = client.get_all_ideas()
        logger.debug("generate originality score")
        originalities = self.generate_originality_score(data['embeddings'])
        
        logger.debug("generate toc tree")
        toc = self._generate_toc_structure(data['documents'], data['ids'], data['embeddings'], originalities)
        save_toc_structure(toc)

        return toc

    def generate_originality_score(self, embeddings) -> list[float]:
        """
        Generate originality scores for documents using UMAP dimensionality reduction
        and Local Outlier Factor analysis.
        
        This method reduces the dimensionality of embeddings using UMAP and then
        applies Local Outlier Factor to identify outliers (unique/creative documents)
        which are considered more original.
        
        Args:
            embeddings: List of document embeddings to analyze
            
        Returns:
            list[float]: Normalized originality scores for each document (higher = more original)
        """
        X = np.array(embeddings).astype('float32')

        reducer = umap.UMAP(
            n_neighbors=10,      # Controls local vs. global structure
            n_components=10,     # Target dimensions for clustering
            metric='cosine',     # Use cosine for RoBERTa embeddings
            low_memory=True      # Helps with very large datasets
        )

        reduced_X = reducer.fit_transform(X)

        lof = LocalOutlierFactor(n_neighbors=10)
        lof.fit_predict(reduced_X)
        score_density = -lof.negative_outlier_factor_
        return MinMaxScaler().fit_transform(score_density.reshape(-1, 1)).flatten()


    def _generate_toc_structure(self, docs: list[str], ids: list[str], embeddings, originalities: list[float], level: int = 1, max_depth: int = 3) -> list[dict[str, Any]] | list[Any]:
        """
        Recursively generate a hierarchical table of contents structure.
        
        This private method creates a hierarchical organization of data items
        by applying clustering at different levels based on semantic similarities.
        
        Args:
            docs (list[str]): List of document texts
            ids (list[str]): List of document IDs
            embeddings: List of document embeddings
            originalities (list[float]): Originality scores for each document
            level (int, optional): Current hierarchy level. Defaults to 1.
            max_depth (int, optional): Maximum recursion depth. Defaults to 3.
            
        Returns:
            list[dict[str, Any]] | list[Any]: Hierarchical structure at current level
        """
        X = np.array(embeddings)

        if len(X) <= 2 or level > max_depth:
            entries = [{"title": id,
                        "text": unformat_text(id, doc),
                        "type": "idea",
                        "id": id,
                        "originality": str(int(originality * 100)) + "%"} for doc, id, originality in zip(docs, ids, originalities)]
            return entries

        n_clusters = max(2, int(np.sqrt(len(X))))

        clustering = AgglomerativeClustering(
            n_clusters=n_clusters,
            metric='cosine',
            linkage='average'
        )
        labels = clustering.fit_predict(X)

        toc = []
        for label in np.unique(labels):
            indices = np.where(labels == label)[0]

            cluster_embeddings = [embeddings[i] for i in indices]
            cluster_docs = [docs[i] for i in indices]
            cluster_ids = [ids[i] for i in indices]
            cluster_originalities = [originalities[i] for i in indices]

            # Compute average originality score for the cluster
            avg_cluster_originality = np.mean(cluster_originalities) if cluster_originalities else 0

            title_text = self.generate_synthetic_title(cluster_docs)

            children = self._generate_toc_structure(
                cluster_docs,
                cluster_ids,
                cluster_embeddings,
                cluster_originalities,
                level + 1,
                max_depth
            )

            heading_entry = {
                "title": title_text,
                "type": "heading",
                "level": level,
                "children": children,
                "originality": str(int(avg_cluster_originality * 100)) + "%"
            }
                        
            toc.append(heading_entry)

        return toc
    
    def generate_synthetic_title(self, cluster_docs: list[str]) -> str:
        """
        Generate a synthetic title from a cluster of ideas using TF-IDF analysis.
        
        This method analyzes a group of related documents to extract the most
        significant terms and create a coherent, descriptive title that represents
        the semantic content of the cluster.
        
        Args:
            cluster_docs (list[str]): List of document texts in the cluster
            
        Returns:
            str: Generated synthetic title for the cluster
        """
        if not cluster_docs:
            return "New Section"
        
        clean_docs = [re.sub(r'[^\w\s]', ' ', doc.lower()) for doc in cluster_docs]

        try:
            # Extract a bit more terms to have choices after filtering
            vectorizer = TfidfVectorizer(
                stop_words='english', 
                ngram_range=(1, 2), 
                max_features=30 
            )
            
            tfidf_matrix = vectorizer.fit_transform(clean_docs)
            scores = np.asarray(tfidf_matrix.sum(axis=0)).flatten()
            terms = vectorizer.get_feature_names_out()
            
            # Sort terms by TF-IDF score in descending order
            sorted_indices = np.argsort(scores)[::-1]
            sorted_terms = [terms[i] for i in sorted_indices]
            
            final_selection = []
            
            for term in sorted_terms:
                # Safety: Limit to 2 or 3 key concepts for the title
                if len(final_selection) >= 2:
                    break
                
                # Check if words from current term are already present
                # in already selected terms (and vice versa)
                words_in_term = set(term.split())
                is_redundant = False
                
                for selected in final_selection:
                    words_in_selected = set(selected.split())
                    # Si intersection non vide (ex: 'hardware' et 'hardware recommendation')
                    if words_in_term.intersection(words_in_selected):
                        is_redundant = True
                        break
                
                if not is_redundant:
                    final_selection.append(term)

            # Mise en forme
            title = " & ".join([t.capitalize() for t in final_selection])
            logger.debug(f"generate_synthetic_title: {title}")
            return title if len(title) > 2 else "Divers & " + cluster_docs[0][:20]

        except Exception:
            return "Section : " + cluster_docs[0][:30] + "..."
        
    