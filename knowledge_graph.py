import os
import glob
import spacy
import networkx as nx
from pyvis.network import Network
from collections import defaultdict
from spacy.lang.en.stop_words import STOP_WORDS

from tqdm import tqdm
import pickle

# Load the English language model for spaCy
nlp = spacy.load('en_core_web_sm')

def extract_concepts(text):
    """
    Extract multi-word concepts and phrases from text using noun chunks.
    Returns a list of tuples containing sentence index and concepts within that sentence.
    """
    doc = nlp(text)
    sentence_concepts = []
    for sent_idx, sent in enumerate(doc.sents):
        concepts = set()
        for chunk in sent.noun_chunks:
            concept = chunk.text.lower().strip()
            # Filter out concepts that are stop words or too short
            if concept in STOP_WORDS or len(concept) <= 2:
                continue
            concepts.add(concept)
        if concepts:
            sentence_concepts.append((sent_idx, concepts))
    return sentence_concepts

def build_concept_graph(concept_sentences):
    """
    Build a graph where nodes are concepts and edges represent co-occurrence in sentences.
    """
    G = nx.Graph()
    concept_frequency = defaultdict(int)

    for sentence_idx, concepts in tqdm(concept_sentences):
        for concept in concepts:
            concept_frequency[concept] += 1
            if not G.has_node(concept):
                G.add_node(concept)

        # Add edges between concepts within the same sentence
        for concept1 in concepts:
            for concept2 in concepts:
                if concept1 != concept2:
                    if G.has_edge(concept1, concept2):
                        G[concept1][concept2]['weight'] += 1
                    else:
                        G.add_edge(concept1, concept2, weight=1)
    return G, concept_frequency

def limit_graph_nodes(G, concept_frequency, max_nodes):
    """
    Limit the number of nodes in the graph to a maximum number by removing nodes with the least frequency.
    """
    if G.number_of_nodes() <= max_nodes:
        return G

    # Sort nodes by frequency (in ascending order)
    sorted_nodes = sorted(concept_frequency.items(), key=lambda item: item[1])

    nodes_to_remove = []
    nodes_to_keep = set()
    total_nodes = G.number_of_nodes()

    # Collect nodes to remove until total_nodes <= max_nodes
    for concept, freq in sorted_nodes:
        if total_nodes <= max_nodes:
            break
        nodes_to_remove.append(concept)
        total_nodes -= 1

    # Remove nodes with the least frequency
    G.remove_nodes_from(nodes_to_remove)

    # Update the concept_frequency dictionary to reflect removed nodes
    for node in nodes_to_remove:
        del concept_frequency[node]

    return G

def limit_node_degree(G, max_degree):
    """
    Limit the number of connections (degree) each node can have to max_degree.
    """
    for node in list(G.nodes()):
        degree = G.degree(node)
        if degree > max_degree:
            # Get all edges connected to this node
            edges = list(G.edges(node, data=True))
            # Sort edges by weight (descending)
            edges = sorted(edges, key=lambda x: x[2].get('weight', 1), reverse=True)
            # Keep only the top max_degree edges
            edges_to_keep = edges[:max_degree]
            edges_to_remove = edges[max_degree:]
            # Remove edges from the graph
            for edge in edges_to_remove:
                G.remove_edge(edge[0], edge[1])
    return G

def visualize_graph(G, concept_frequency, file_path, min_frequency=3, max_nodes=100, max_degree=10):
    """
    Visualize the concept graph using pyvis with node size based on connections.
    Filters out nodes with frequency less than min_frequency, limits total nodes to max_nodes,
    and limits the degree of each node to max_degree.
    """
    # Remove nodes with frequency less than min_frequency
    low_frequency_nodes = [node for node, freq in concept_frequency.items() if freq < min_frequency]
    G.remove_nodes_from(low_frequency_nodes)

    # Update the concept_frequency dictionary to reflect removed nodes
    for node in low_frequency_nodes:
        del concept_frequency[node]

    # Limit the number of nodes in the graph
    G = limit_graph_nodes(G, concept_frequency, max_nodes)

    # Limit the degree of each node
    G = limit_node_degree(G, max_degree)

    print(f"Number of nodes in the graph after limiting: {G.number_of_nodes()}")
    print(f"Number of edges in the graph after limiting: {G.number_of_edges()}")

    net = Network(height='100vh', notebook=True)
    net.from_nx(G)

    # Adjust node size and tooltip based on degree and frequency
    for node in net.nodes:
        degree = G.degree(node['id'])
        frequency = concept_frequency[node['id']]
        node['value'] = degree
        node['title'] = (f"<b>{node['id'].title()}</b><br>"
                         f"Connections: {degree}<br>"
                         f"Frequency: {frequency}")
        node['label'] = node['id'].title()
        node['size'] = degree * 5  # Adjust the multiplier as needed
    for edge in net.edges:
        edge['width'] = 1

    # Customize physics for better visualization
    # net.set_options("""
    # var options = {
    #   "physics": {
    #     "barnesHut": {
    #       "gravitationalConstant": -80000,
    #       "centralGravity": 0.3,
    #       "springLength": 95,
    #       "springConstant": 0.04,
    #       "damping": 0.09,
    #       "avoidOverlap": 1
    #     },
    #     "maxVelocity": 146,
    #     "minVelocity": 0.75
    #   }
    # }
    # """)
    # Disable physics during initial rendering to speed up performance
    net.toggle_physics(False)
    net.show(file_path)

def main():
    folder_path = './LastDays_captions'
    working_dir = './graph_lastdays'
    max_files = 1000
    os.makedirs(working_dir, exist_ok=True)

    concept_sentences = []
    file_paths = glob.glob(os.path.join(folder_path, '*.txt'), )
    file_paths = file_paths[:max_files]

    file_count = len(file_paths)
    print(f"Processing {file_count} files...")

    for file_path in tqdm(file_paths, total=file_count):
        with open(file_path, 'r') as f:
            text = f.read()
        sentence_concepts = extract_concepts(text)
        concept_sentences.extend(sentence_concepts)

    # Build the concept graph
    print('Building Graph...')
    G, concept_frequency = build_concept_graph(concept_sentences)

    # Save the data for furture uses
    print('Saving Data...')
    nx.write_graphml(G, path=os.path.join(working_dir, 'graph.graphml'))
    with open(os.path.join(working_dir, 'concept_frequency.pkl'), 'wb') as f:
        pickle.dump(concept_frequency, f)
    
    # Visualize the graph
    print('Visualizing...')
    visualize_graph(G, concept_frequency, file_path=os.path.join(working_dir, 'knowledge_graph.html'), min_frequency=3, max_nodes=100)

if __name__ == "__main__":
    main()