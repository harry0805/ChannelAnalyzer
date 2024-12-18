import networkx as nx
from knowledge_graph import visualize_graph
import pickle
import os

def main():
    working_dir = './draw_graph'
    print('Loading Data...')
    G = nx.read_graphml(os.path.join(working_dir, 'graph.graphml'))
    with open(os.path.join(working_dir, 'concept_frequency.pkl'), 'rb') as f:
        concept_frequency = pickle.load(f)

    # Visualize the graph
    print('Visualizing...')
    visualize_graph(G, concept_frequency, file_path=os.path.join(working_dir, 'knowledge_graph.html'), min_frequency=3, max_nodes=200)

if __name__ == "__main__":
    main()