import networkx as nx
from itertools import combinations, groupby
import random

# selbst definierte Klasse Layer, auf die mehrmals im Laufe des Erstellen der Netzwerke, als auch beim restlichen
# Durchlaufen des Codes zurückgegriffen wird
class Layer():
    # Diese Klassenliste beinhaltet alle erzeugten Layerobjekte mit ihren Eigenschaften
    list_of_layers = []

    def __init__(self, id, name, nn, sr, bu, connect, ed_time, ld, p_gen_agent, hubs, max_queue_cost, colour=None):
        self.id = id
        self.name = name
        self.number_of_nodes = nn
        self.service_rate = sr
        self.buffer = bu
        self.connectivity = connect
        self.edge_time = ed_time
        self.load = ld
        self.probability_gen_agent = p_gen_agent
        self.node_list = []
        self.hubs = hubs
        self.h_init_gen_p = 0 # Häufigkeit initialer Durchlauf zur Agentengenerierung, für Layerloadanpassung
        self.colour = colour
        self.max_queue_cost = max_queue_cost
        # Netzwerk erstellen; connectivity = Wahrscheinlichkeit zur Kantenerzeugung im Layer
        # self.network = nx.fast_gnp_random_graph(self.number_of_nodes, self.connectivity, seed=None, directed=True)
        self.network = Layer.gnp_random_connected_graph(self.number_of_nodes,self.connectivity)
        Layer.list_of_layers.append(self)

    # folgende Methode zur Erstellung eines Netzwerkes, das unseren Vorstellung am ehesten Entsprach
    # Quelle: https://stackoverflow.com/questions/61958360/how-to-create-random-graph-where-each-node-has-at-least-1-edge-using-networkx
    def gnp_random_connected_graph(n, p):
        """
        Generates a random directed graph, similarly to an Erdős-Rényi
        graph, but enforcing that the resulting graph is conneted
        """
        edges = combinations(range(n), 2)
        G = nx.DiGraph()
        G.add_nodes_from(range(n))
        if p <= 0:
            return G
        if p >= 1:
            return nx.complete_graph(n, create_using=G)
        for _, node_edges in groupby(edges, key=lambda x: x[0]):
            node_edges = list(node_edges)
            random_edge = random.choice(node_edges)
            G.add_edge(*random_edge)
            for e in node_edges:
                if random.random() < p:
                    G.add_edge(*e)
        for ed in G.edges:
            G.add_edge(ed[1], ed[0])

        return G