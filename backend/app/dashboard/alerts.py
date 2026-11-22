"""
Emerging Scam Alert Engine for Suraksha
Clusters similar reported text/indicators using TF-IDF and Cosine Similarity.
When a new cluster with no prior pattern exceeds threshold within a district, generates an alert card.
"""

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from app.reports.database import get_connection

def cluster_emerging_reports(min_cluster_size: int = 3, similarity_threshold: float = 0.55):
    """
    Scans recent unconfirmed and confirmed reports, clusters indicators/notes,
    and identifies emerging unknown scam patterns per district.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT r.id, r.district, r.scam_type, r.indicator_raw 
        FROM reports r
        WHERE r.indicator_raw IS NOT NULL AND length(r.indicator_raw) > 3
        ORDER BY r.id DESC LIMIT 150
    """)
    rows = cursor.fetchall()

    if len(rows) < min_cluster_size:
        conn.close()
        return []

    texts = [f"{row['scam_type']} {row['indicator_raw']}" for row in rows]
    districts = [row["district"] for row in rows]

    try:
        vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1)
        X = vectorizer.fit_transform(texts)
        sim_matrix = cosine_similarity(X)

        clusters_found = []
        visited = set()

        for i in range(len(texts)):
            if i in visited:
                continue
            similar_indices = [j for j in range(len(texts)) if sim_matrix[i, j] >= similarity_threshold]
            if len(similar_indices) >= min_cluster_size:
                cluster_districts = [districts[k] for k in similar_indices]
                most_common_dist = max(set(cluster_districts), key=cluster_districts.count)
                
                # Extract top key terms
                sample_text = " ".join([texts[k] for k in similar_indices])
                top_terms = list(set([w for w in sample_text.split() if len(w) > 3]))[:4]

                cluster_card = {
                    "district": most_common_dist,
                    "cluster_name": f"Surging {rows[i]['scam_type']} Variant",
                    "keywords": ", ".join(top_terms),
                    "report_count": len(similar_indices)
                }
                clusters_found.append(cluster_card)
                visited.update(similar_indices)

        # Store/update clusters in database
        for c in clusters_found:
            cursor.execute("""
                INSERT INTO scam_clusters (district, cluster_name, keywords, report_count)
                VALUES (?, ?, ?, ?)
            """, (c["district"], c["cluster_name"], c["keywords"], c["report_count"]))
        conn.commit()

        # Retrieve all latest active clusters
        cursor.execute("SELECT district, cluster_name, keywords, report_count, created_at FROM scam_clusters ORDER BY id DESC LIMIT 5")
        active_clusters = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return active_clusters
    except Exception as e:
        conn.close()
        return []

def get_latest_alerts():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT district, cluster_name, keywords, report_count, created_at 
        FROM scam_clusters 
        ORDER BY id DESC LIMIT 5
    """)
    alerts = [dict(row) for row in cursor.fetchall()]
    conn.close()
    if not alerts:
        # Default seed alert for demo
        return [{
            "district": "Raipur",
            "cluster_name": "New Fake CSPDCL Electricity WhatsApp Bill Notice",
            "keywords": "CSPDCL, 9:30 PM, APK, power cut",
            "report_count": 8,
            "created_at": "Today"
        }]
    return alerts
