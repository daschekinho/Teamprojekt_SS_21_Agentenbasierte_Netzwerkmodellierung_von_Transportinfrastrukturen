from io import open
import csv
import networkx as nx
import random as rm
import numpy as np
from scipy.sparse import lil_matrix
from layer import Layer


file_networks = "All_Networks.csv"
with open(file_networks, "w+") as file_all:
    writer = csv.writer(file_all)
    writer.writerow(['ID','Disrupted','Timesteps','Perf_agent','Agent gen zur Laufzeit','OnTour','Delivered','Lost','Gen at dis_node','Layer-Load align','Disruption Value','Disrupt change','Buffer capacity','Service Rate capacity','Slow reset','Disruption Time','Disruption interval'])


# Eigene Klasse MultiLayerGraph, erbt von MultiDiGraph aus Networkx
# Modellierung der Netzwerke
class MultiLayerGraph (nx.MultiDiGraph):
    mlg_list = []
    mlg_count = 0
    mlg_id = 0

    def __init__(self, id, lyr):
        # Das erste Netzwerk mit ID=0, dient nur der Überschriften-Initialisierung
        if id == 0:
            print('initialisiere mlg')
            self.ID = 'ID'
            self.agents_on_tour = 'OnTour'
            self.agents_delv = 'Delivered'
            self.agents_lost = 'Lost'
            print('id = 0 -> initialisiert')
        elif id > 0:
            # Initialisieren diverser Counts, Listen und Eigenschaften des Netzwerks
            print('id > 0 -> initialisiert')
            self.ID = id
            self.agents_on_tour = 0
            self.agents_delv = 0
            self.agents_lost = 0

            self.agent_list = []
            self.agents_delivered = []
            self.agents_failed = []
            self.agents_generated_list = []

            self.agent_count = 0
            self.agents_delivered_count = 0
            self.agents_failed_count = 0
            self.count_on_tour = 0
            self.agents_generated_count = 0
            self.count_failed_no_next = 0
            self.count_failed_disrupt = 0
            self.count_failed_pfad = 0
            self.count_failed_queue = 0
            self.count_failed_gen = 0
            self.count_failed_gen_full_buffer = 0
            self.count_failed_cost = 0
            self.lyr_id_fail = []

            self.nodes_waf = []
            self.node_traffic = []
            # Zählt Anzahl an Knoten im gesamtem Netzwerk für Liste mit Load pro Node
            quantity_nodes = 0
            for i in Layer.list_of_layers:
                quantity_nodes += i.number_of_nodes
            self.load_per_node = [0] * quantity_nodes

            #Zählt Anzahl an Knoten im gesamtem Netzwerk für Liste mit Load pro Node
            quantity_nodes = 0
            for i in Layer.list_of_layers:
                quantity_nodes += i.number_of_nodes
            self.load_per_node = [0] * quantity_nodes

            #abfrage zur desruption eingebaut
            self.disrupted = False
            self.disruptions = []
            self.disrupted_nodes = []
            self.count_disrupted_nodes = 0

            # Liste initial vs. actual route cost/time
            self.route_cost_comp = []

            # Matrixgenerierung aus Layern zur Graphenerstellung
            self.__matrix = self.generate_matrix(lyr)
            self.__GraphTemp = nx.from_numpy_matrix(self.__matrix, parallel_edges=True, create_using=nx.MultiDiGraph)
            super().__init__(self.__GraphTemp)

            self._set_node_list(lyr)
            self._set_inter_layer_edges(lyr)
            # mirror_edges() sollte bei einer anderen Erzeugung der Layernetzwerke benutzt werden
            # darauf achten, ob inter_layer_edges auch gespeigelt sind
            # self._mirror_edges()

            # Erstellen eines Textfiles mit dem Array der Adjazenzmatrix
            self.__A = nx.adjacency_matrix(self).toarray()
            str_name = "network" + str(self.ID) + "_adj_mat" + ".csv"
            np.savetxt(str_name, self.__A, delimiter=",")

            self._set_node_details(lyr)
            self._set_edge_details(lyr)
            # Entferne isolierte Knoten
            self.remove_nodes_from(list(nx.isolates(self)))

            # Graph zeichnen; kann auskommentiert werden um Rechenzeit zu verringern
            color_map = []
            for node in self.nodes:
                color_map.append(self.node_colour[node])
            nx.draw_networkx(self, with_labels=True, node_color=color_map, label='Network ' + str(self.ID)) # + str(self.ID), ) #Zeichnen des Graphen mit matplotlib.pyplot

            # Erstelltes Netzwerk in Liste der Netzwerke anhängen
            MultiLayerGraph.mlg_list.append(self)
            MultiLayerGraph.mlg_count += 1

        else:
            print('FEHLER IN INITIALISIERUNG EINES MULTILAYERGRAPHS')
        print('mlg init mit id', self.ID)

    # Erstellung einer Nodeliste für jeden Layer; Liste wird in _set_inter_layer_edges benötigt
    def _set_node_list(self, lyr):
        nd_list = []
        a = 0
        b = lyr[0].number_of_nodes
        for j in range(0, len(lyr)):
            for nd in list(self.nodes)[a:b]:
                lyr[j].node_list.append(nd)
            a = b
            if j != (len(lyr) - 1):
                b += lyr[j + 1].number_of_nodes
            lyr[j].node_list = list(dict.fromkeys(lyr[j].node_list)) # entfernen von duplikaten in liste, erzeugt durch mehrere netzwerke
            nd_list.append(lyr[j].node_list)
        print('node_list = ', nd_list)

    # Zuweisung von Knoteneigenschaften aus den Layerninformationen
    # Die Knoteneigenschaften sind in dicts in den Knoten gespeichert
    def _set_node_details(self, lyr):
        self.node_id = dict.fromkeys(self, 1)
        self.node_type = dict.fromkeys(self, 1)
        self.node_layer = dict.fromkeys(self, 1)
        self.node_buffer = dict.fromkeys(self, 1)
        self.node_service_rate = dict.fromkeys(self, 1)
        self.node_inter_edge_time = dict.fromkeys(self, 1)
        self.node_load = dict.fromkeys(self, 1)
        self.node_queue = dict.fromkeys(self, 1)
        self.node_queue_load = dict.fromkeys(self)
        self.node_queue_cost = dict.fromkeys(self)
        self.node_p_gen_agent = dict.fromkeys(self)
        self.node_max_queue_cost = dict.fromkeys(self)

        self.node_colour = dict.fromkeys(self)

        self.node_dis = dict.fromkeys(self)
        self.node_disrupted = dict.fromkeys(self)
        self.temp_node_service_rate = dict.fromkeys(self)
        self.temp_node_buffer = dict.fromkeys(self)

        i = 0
        for j in range(0,len(lyr)):
            for nd in lyr[j].node_list:
                self.node_id[nd] = i
                self.node_queue[nd] = []
                i += 1
                self.node_type[nd] = lyr[j].name
                self.node_layer[nd] = lyr[j].id
                self.node_buffer[nd] = lyr[j].buffer
                self.node_service_rate[nd] = lyr[j].service_rate
                self.node_inter_edge_time[nd] = lyr[j].edge_time
                self.node_load[nd] = lyr[j].load
                self.node_p_gen_agent[nd] = lyr[j].probability_gen_agent
                self.node_max_queue_cost[nd] = lyr[j].max_queue_cost
                self.node_colour[nd] = lyr[j].colour
                self.node_disrupted[nd] = False
                self.temp_node_buffer[nd] = self.node_buffer[nd]
                self.temp_node_service_rate[nd] = self.node_service_rate[nd]

        # Zuweisung von dicts zu Knoten und  Festlegung Namen der Knoteneigenschaften
        nx.set_node_attributes(self, self.node_id, 'ID')
        nx.set_node_attributes(self, self.node_type, 'Typ')
        nx.set_node_attributes(self, self.node_layer, 'Layer')
        nx.set_node_attributes(self, self.node_buffer, 'Buffer')
        nx.set_node_attributes(self, self.node_service_rate, 'Service Rate')
        nx.set_node_attributes(self, self.node_queue, 'Queue')
        nx.set_node_attributes(self, self.node_p_gen_agent, 'Prob_Gen_Agent')
        nx.set_node_attributes(self, self.node_colour, 'Colour')

        nx.set_node_attributes(self, self.node_dis, 'disruption')
        nx.set_node_attributes(self, self.node_disrupted, 'Disrupted_status')
        nx.set_node_attributes(self, self.temp_node_buffer, 'temp node buffer')
        nx.set_node_attributes(self, self.temp_node_service_rate, 'temp node service rate')

    # Zuweisung von Kanteneigenschaften aus den Layerninformationen
    # Kanten speichern die Kosteninformationen
    def _set_edge_details(self, lyr):
        #Transportzeit als Kantengewicht
        self.cost_rate = 1  # Faktor der Kosten für eine Zeiteinheit auf allen Kanten, momentan 1
        self.edge_transport_time = dict.fromkeys(self.edges)
        self.edge_transport_cost = dict.fromkeys(self.edges)

        # Transportzeiten festlegen
        for ed in self.edges:
            # Kanten innerhalb eines Layers
            if self.node_layer[ed[0]] == self.node_layer[ed[1]]:
                # Transportation Time in Layern definiert
                self.edge_transport_time[ed] = self.node_inter_edge_time[ed[0]]
            # InterLayer-Kanten
            else:
                # InterLayer Transportation Time zunächst auf 5 gesetzt
                self.edge_transport_time[ed] = 5  # individuell anpassbar
            # Transportation Cost ergeben sich aus dem Produkt der benötigten Zeit und dem festgelegten Faktor
            self.edge_transport_cost[ed] = self.cost_rate * self.edge_transport_time[ed]

        # Zuweisung zu Kantenattributen
        nx.set_edge_attributes(self, self.edge_transport_time, 'Transportzeit')
        nx.set_edge_attributes(self, self.edge_transport_cost, 'Transportkosten')

        # Hier noch keine Werte; werden in update_edges() aufgefüllt
        self.edge_queue_cost = dict.fromkeys(self.edges)
        self.edge_total_cost = dict.fromkeys(self.edges)

    # Spiegelt die gerichteten Kanten im Netzwerk
    # Agenten können sich so in beide Richtungen auf einer Kante bewegen
    def _mirror_edges(self):
        for ed in self.edges:
            self.add_edge(ed[1], ed[0], 0)

    # Erstellt die Verbindungen zwischen den einzelnen Layern
    # Anzahl der Hubs pro Layer sind in den Layereigenschaften festgelegt
    # Es wurden die Knoten mit den höchsten Graden für die Hubs ausgewählt
    def _set_inter_layer_edges(self, lyr):
        hub_list = []  # multidimensional; beinhaltet später die Hubs aller Layer
        last_layer = lyr[-1]
        layer_degree_list = list(self.degree)
        layer_degree_list.sort(key=lambda x: x[1], reverse=True)
        print(f' ==> vor dem Verbinden: layer_degree_list: {layer_degree_list}')
        layer_id = 0
        y = 0 # untere Schranke
        z = lyr[layer_id].number_of_nodes # obere Schranke
        for i in lyr:
            layer_nodes = [item for item in layer_degree_list if item[0] in range(y, z)]
            if i != last_layer:
                layer_id += 1
                y = z
                z = z + lyr[layer_id].number_of_nodes
            layer_nodes.sort(key=lambda x: x[1], reverse=True)
            layer_nodes = layer_nodes[:i.hubs]
            only_node_id = [(a) for a, b in layer_nodes]
            hub_list.append(only_node_id)
        print(f'Hublist: {hub_list}')

        # Erzeugung der Kanten zwischen den gerade gefundenen Hubs
        # Dabei verbindet sich ein Hub mit jeweils einem anderen aus einem anderen Layer
        # Hat der Zielknoten aber schon eine Verbindung aus dem Layer wird ein anderer Knoten probiert
        # So wird verhindert, dass die Konnektivität der Hubs zu stark ist
        for i in hub_list: # für jedes Layer
            temp_list = hub_list.copy()  # Hilfsliste ohne Teilliste, die gerade betrachtet wird
            temp_list.remove(i)
            for j in i: # für jeden Knoten in dem Layer
                for k in temp_list: #für jeden anderen Layer
                    hilfsliste = k.copy()
                    zielknoten = rm.choice(k) # wäle zufällig einen Knoten aus diesem Layer aus
                    while len(hilfsliste) != 0:
                        if (zielknoten, j, 0) in self.edges:
                            hilfsliste.remove(zielknoten)
                            if len(hilfsliste) > 0:
                                zielknoten = rm.choice(hilfsliste)
                        else:
                            self.add_edge(j, zielknoten, 0) # , weight=5)
                            self.add_edge(zielknoten, j, 0)
                            break

    # Aktualisiert die Kosten der Kanten zur Laufzeit
    # Es werden zunächst die Load pro Knoten bestimmt und je nach Füllgrad die Kosten für die Kanten anteilig erhöht
    # Falls es perfekte Agenten gibt, werden die Kantenkosten zu einem disrupted Knoten mit einer gewissen
    # Wahrscheinlickeit (dc_quotient), die sich aus dc_buffer und dc_servicerate zusammensetzen, auf unendlich gesetzt
    # für jeden am Knoten wartenden Agenten wird der Load aufsummiert, bis der Buffer voll ist
    # solange werden die Kosten für die Kante anteilig üfr den Füllgrad des Buffers erhöht
    # ist der Buffer voll, failt der Agent wegen 'QUEUE'
    def update_edges(self, agents, bool_perf_ag=False,dc_verändern=False, dc_quotient=1):
        for nd in self.nodes:
            # Load der Wartschlangen werden bei jedem Aufrufen der Methode neu berechnet
            self.node_queue_load[nd] = 0
            self.node_queue_cost[nd] = 0
            # Durch die Kostenanpassung wählen perf. Agenten eine günstigere Route
            if bool_perf_ag == True and self.node_disrupted[nd]:
                inf_chance = rm.random()
                if dc_verändern == False:
                    self.node_queue_cost[nd] = float('inf')
                elif dc_verändern == True and inf_chance < dc_quotient:
                    self.node_queue_cost[nd] = float('inf')
                else:
                    for el in self.node_queue[nd]:
                        q_temp = self.node_queue_load[nd] + el.load
                        print("NETWORK:", self.ID, "NODE:", nd, "Q_Load =", self.node_queue_load[nd], "QTEMP =", q_temp,
                              "Buffer =", self.node_buffer[nd])
                        if (q_temp > self.node_buffer[nd]):
                            if el.t == 0 and el.start == nd:
                                el.fail('GEN AT FULL BUFFER')
                                self.agents_generated_count -= 1
                            else:
                                el.fail('QUEUE')
                                self.node_queue_cost[nd] = self.node_max_queue_cost[nd]
                        else:
                            self.node_queue_load[nd] = q_temp
                            nenner = self.node_queue_load[nd] / self.node_buffer[nd]
                            self.node_queue_cost[nd] = nenner * self.node_max_queue_cost[nd]

            # Unterschiedung, falls es keine perfekten Agenten gibt und somit Kantenkosten nicht inf. werden können
            else:
                for el in self.node_queue[nd]:
                    q_temp = self.node_queue_load[nd] + el.load
                    print("NETWORK:", self.ID, "NODE:", nd, "Q_Load =", self.node_queue_load[nd], "QTEMP =", q_temp, "Buffer =",self.node_buffer[nd])
                    if (q_temp > self.node_buffer[nd]):
                        if el.t == 0 and el.start == nd:
                            el.fail('GEN AT FULL BUFFER')
                            self.agents_generated_count -= 1
                        else:
                            el.fail('QUEUE')
                            self.node_queue_cost[nd] = self.node_max_queue_cost[nd]
                    else:
                        self.node_queue_load[nd] = q_temp
                        nenner = self.node_queue_load[nd] / self.node_buffer[nd]
                        self.node_queue_cost[nd] = nenner * self.node_max_queue_cost[nd]

        # Transferierem den Kosten von den Knoten zu den Kanten
        for ed in self.edges:
            self.edge_queue_cost[ed] = self.node_queue_cost[ed[1]]  # Kosten der Kante = Kosten des hinteren Knotens
            self.edge_total_cost[ed] = self.edge_transport_cost[ed] + self.edge_queue_cost[ed]
        nx.set_edge_attributes(self, self.edge_total_cost, 'Kosten')


    # Ausgabe der Netzwerk-Eigenschaften in einer CSV-Datei
    def display_network(self, n_timesteps, bool_perf_ag, ag_gen_laufzeit, gen_at_dis_node, lyr_similar_load, dv, dc_verändern, dc_buffer, dc_service_rate, dc_aufhebung, dt, dp):
        datei = open(file_networks, 'a')
        with datei:
            writer = csv.writer(datei)
            writer.writerow([str(self.ID), str(self.disrupted), str(n_timesteps), str(bool_perf_ag),
                             str(ag_gen_laufzeit), str(self.agent_count), str(self.agents_delivered_count),
                             str(self.agents_failed_count), str(gen_at_dis_node), str(lyr_similar_load), (str(dv)),
                             str(dc_verändern), str((1-dc_buffer)), (str(1-dc_service_rate)), str(dc_aufhebung),
                             str(dt), str(dp)])


    # Diese Methode ist dafür verantwortlich zufällig ausgewählte Methoden zu disrupten
    # Dass ein Knoten disrupted kann versch. Auswirkungen auf Agenten haben
    # Dabei wird das entscheidende Flag node_disrupted[nd]=True gesetzt
    # die Disruption wird mit ihren Eigenschaften in einem dict gespeichert
    def disrupt_network(self, t_disruption_start, disruption_value, disruption_time, dc_verändern, dc_buffer, dc_service_rate):
        self.disrupted = True # Netzwerk ist disrupted, falls ein Knoten disrupted ist
        for nd in list(self.nodes):
            if self.node_disrupted[nd] == False: # es werden nur bereits nicht disruptete Knoten betrachtet
                p_disrupt = rm.random()
                if p_disrupt < disruption_value:
                    t_disrupt = disruption_time
                    dis = {'t_start': t_disruption_start,
                           't_ende': t_disruption_start + t_disrupt,
                           't_dauer': t_disrupt,
                           'node': nd,  # vorher war 'node': [nd] (Liste)
                           'edges': self.edges(nd),
                           'lost_agents': [],
                           # falls die Disruption anteilig aufgehoben wird
                           'restore_buffer_value': (self.temp_node_buffer[nd] - (self.temp_node_buffer[nd] * (1 - dc_buffer))) / t_disrupt,
                           'restore_service_rate_value': (self.temp_node_service_rate[nd] - (self.temp_node_service_rate[nd] * (1 - dc_service_rate))) / t_disrupt}

                    print('KNOTEN', nd, 'disrupted, t = ', t_disruption_start)
                    self.node_disrupted[nd] = True
                    self.node_dis[nd] = dis['t_ende']
                    self.disrupted_nodes.append(nd)
                    self.count_disrupted_nodes += 1

                    if dc_verändern==False:
                        for ag in list(self.node_queue[nd]):
                            dis['lost_agents'].append(ag)
                            ag.fail('DISRUPT')
                    # falls dc_verändern==True, so sollen die Agenten nicht direkt failen, sondern die Chance bekommen
                    # mit den verringerten Werten abgefertigt zu werden
                    else:
                        self.node_buffer[nd] = round(self.node_buffer[nd] * (1 - dc_buffer))
                        self.node_service_rate[nd] = round(self.node_service_rate[nd] * (1 - dc_service_rate))

                    self.disruptions.append(dis)

    # Gegenstück zu disrupt_network; hebt die dort angelegten Disruptions wieder auf
    def restore_disruption(self, t, dc_verändern, dc_aufhebung, dc_buffer, dc_service_rate):
        list_remove_nodes = []
        for disruption in self.disruptions:
            if dc_aufhebung == False:
                if t == disruption['t_ende']: # Dauer der Disruption abgelaufen
                    node_to_restore = disruption['node']
                    if dc_verändern==True:
                        # in den temp_variablen waren die ursprünglichen Werte gespeichert
                        self.node_service_rate[node_to_restore] = self.temp_node_service_rate[node_to_restore]
                        self.node_buffer[node_to_restore] = self.temp_node_buffer[node_to_restore]
                    self.node_disrupted[node_to_restore] = False
                    self.count_disrupted_nodes -= 1
                    self.disrupted_nodes.remove(disruption['node'])
                    list_remove_nodes.append(disruption)

            # hier dc_aufhebung==True, bedeutet dass Disruptions nach und nach aufgelöst werden; hier aber auch am Ende
            # also komplettes zurücksetzen auf ursprüngliche Werte
            elif t == (disruption['t_ende']):
                node_to_restore = disruption['node']
                self.node_service_rate[node_to_restore] = self.temp_node_service_rate[node_to_restore]
                self.node_buffer[node_to_restore] = self.temp_node_buffer[node_to_restore]
                self.node_disrupted[node_to_restore] = False
                self.count_disrupted_nodes -= 1
                self.disrupted_nodes.remove(disruption['node'])
                list_remove_nodes.append(disruption)

            # Disruption nach und nach auflösen
            elif t > (disruption['t_start']) and t < (disruption['t_ende']):
                node_to_restore = disruption['node']
                self.node_service_rate[node_to_restore] += disruption['restore_service_rate_value']
                self.node_buffer[node_to_restore] += disruption['restore_buffer_value']

        for dis in list_remove_nodes:
            self.disruptions.remove(dis)

    # Methode zum Darstellen der Netzwerkeigenschaften in der Konsole (print)
    def display_network_konsole(self):
        anzeige = [self.ID, self.agent_count,self.agents_delivered_count,self.agents_failed_count]
        print('agents on network', self.ID, ':', anzeige)

    # Erstellen der zur Erstellung des Netzwerk benötigten Matrix
    # Dabei müssen die Längen der einzelnen Layer beachtet werden
    def generate_matrix(self, lyr):
        self.n_nodes = 0 # Anzahl an Knoten im Netzwerk (über Layer aufsummiert)
        for el in lyr:
            self.n_nodes = self.n_nodes + el.number_of_nodes
        mat = lil_matrix(np.zeros((self.n_nodes, self.n_nodes)))
        a = 0
        b = lyr[0].number_of_nodes
        for i in range (0, len(lyr)):
            mat[a:b, a:b] = nx.adjacency_matrix(lyr[i].network)
            a = b
            if i != (len(lyr)-1):
                b += lyr[i+1].number_of_nodes
        adj_mat = mat.toarray()
        return np.asmatrix(adj_mat)
