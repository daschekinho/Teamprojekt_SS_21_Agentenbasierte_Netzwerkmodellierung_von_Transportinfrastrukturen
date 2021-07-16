from io import open
import networkx as nx
import csv
import random as rm
import copy

file_agents = 'Agents.csv'
with open(file_agents, "w+") as agent_file:
    writer=csv.writer(agent_file)
    writer.writerow(['ID','Load','SO','Start','Dest','Route','Cost','Actual Route cost','Route Changes','Time','State',
                     'T-Edge','T-Node','Cost Next Edge','T-Edge max','Graph'])

# selbst definierte Klasse agent()
class agent():

    def __init__(self,G,ID,load,start):
        self.mg_ag = G  # Verweis auf Multilayer-Graph
        self.ID = ID  # Ident-Nr. des Agenten
        self.load = load  # Ladeeinheiten
        self.so = start  # Standort des Agenten zum Zeitpunkt t
        self.start = start  # Startknoten des Agenten
        self.dest = self.get_destination(self.mg_ag.nodes, self.start)  # Endknoten des Agenten
        self.t = 0  # Zeit, die ag in System ist
        self.t_at_node = 0  # Zeit, die ag am SO ist
        self.t_at_edge = 0  # Zeit, die ag auf einer Kante ist
        self.cost_next_edge = 0
        self.t_at_edge_max = 0  # Zeit, die ag max. auf einer Kante ist
        self.at_edge = False
        self.state = "generated"
        self.route = dict()  # self.get_route()  #Verweis auf Route des Agenten
        self.route = {'path': False, 'cost': 0, 'time': 0}
        # Kosten und Zeitbetrachtung; Routenabhängig
        self.actual_route_cost = 0
        self.waiting_cost = 0
        self.route_changes = 0
        # Verweise auf das Netzwerk
        self.mg_ag.node_queue[start].append(self)
        self.mg_ag.agent_list.append(self)
        self.mg_ag.agent_count = self.mg_ag.agent_count + 1
        self.mg_ag.agents_generated_list.append(self)
        self.mg_ag.agents_generated_count += 1
        self.mg_ag.count_on_tour += 1

    # liefert einen zufällig vom aktuellen Standort des Agenten verschiedenen Knoten als Ziel der Route
    # Es wird dabei nicht unterschieden in welchem Layer dieser Knoten liegen soll
    def get_destination(self, d, s):
            temp = copy.deepcopy(list(d))
            temp.remove(s)
            dest = rm.choice(list(temp))
            if nx.has_path(self.mg_ag, s, dest):
                return dest
            else:
                self.get_destination(d, s)

    # liefert die nach dem Dijkstra-Algorithmus gefundene günstigste Route vom aktuelen Standort zum Zielknoten
    # Die Gewichte der Kanetn sind dabei die Kantenkosten, die unter anderem in update_edges() aktualisiert werden
    def get_route(self):
            if nx.has_path(self.mg_ag, self.so, self.dest):
                self.route['path'] = nx.shortest_path(self.mg_ag, source=self.so, target=self.dest, weight='Kosten')
                self.route['cost'] = nx.shortest_path_length(self.mg_ag, self.so, self.dest, 'Kosten')
                # Sollte dies die initiale Routenberechnung sein, dann werden die Kosten für diese erste Route
                # self.route['path'] gespeichert, um später einen Kostenvergleich durchführen zu können
                if self.t == 0:
                    edge_time = 0
                    path = self.route['path']
                    for i in path:
                        index = path.index(i)
                        if index + 1 < len(path):
                            edge_time += self.mg_ag.edge_transport_time[(i, path[index + 1], 0)]
                    self.route['time'] = edge_time
                print(f'ROUTE von Agent {self.ID}: {self.route}')
            else:
                self.route['path'] = False
                self.route['cost'] = False
                self.route['time'] = False
            return self.route

    # diese Methode wird in der Main aufgerufen, wenn die Agenten von einem Knoten abgearbeitet wurden und sich auf den
    # Weg zum nächsten Knoten machen, dieser Knoten muss allerdings verfügbar sein neue Agenten aufzunehmen
    def go_next(self):
            self.t_at_edge = 0
            self.at_edge = False
            next_SO = self.route['path'][1]
            self.so = next_SO

            self.mg_ag.node_traffic.append(self.so)  # An Liste anhägen für Zentralitätsplot
            self.mg_ag.load_per_node[self.so] += self.load

            if next_SO in self.mg_ag.nodes:
                self.t_at_node = 0
                print('Agent', self.ID, 'geht zu', next_SO)
                self.mg_ag.node_traffic.append(next_SO) # wichtig für Plot für Agententraffic
                self.mg_ag.node_queue[next_SO].append(self)  # in Warteschlange des Folgeknotens
                del self.route['path'][0]
            else:
                self.fail('NO NEXT')

    # die Methode wird aufgerufen wenn der nächste Standort in der Route mit dem Zielknoten eines Agenten übereinstimmt
    # Es werden dabei Zähler und Eigenschaften angepasst, um Konsistenz zu gewährleisten und Plots anzufertigen
    def reach_destination(self):
            print('NO.', self.ID, "arrived")  #VERÄNDERT
            self.state = "arrived"
            agent_layer_id = self.mg_ag.node_layer[self.start]
            initial_cost = self.route['time']
            actual_cost = self.actual_route_cost
            waiting_cost = self.waiting_cost # Kosten = 1, für jede Periode, die Agent an Knoten im Queue warten muss, weil er nicht abgefertigt werden konnte.
            total_cost = self.actual_route_cost + self.waiting_cost
            self.mg_ag.route_cost_comp.append((agent_layer_id, initial_cost, actual_cost, waiting_cost, total_cost))
            self.mg_ag.node_queue[self.so].remove(self)
            self.mg_ag.agents_delivered.append(self)
            self.mg_ag.agent_list.remove(self)
            self.mg_ag.agents_delivered_count += 1
            self.mg_ag.agent_count -= 1
            self.mg_ag.count_on_tour -= 1
            print('delivered:', str(self.mg_ag.agents_delivered_count))

    # wird aufgerufen, falls beim Abarbeiten des Codes an irgendeiner Stelle ein Agent failen sollte
    # Dabei werden dem Fail-Reason entsprechende Listen und Zähler angepasst
    # Wann genau die einzelnen Fail-Reasons auftreten können sind im Bericht beschrieben
    def fail(self, reason):
            self.state = "FAILED: " + reason
            self.route['path'] = False
            print('NO.', self.ID, str(self.state))
            #IF-Schleifen für Counter zum Plotten
            if reason == 'NO NEXT':
                self.mg_ag.count_failed_no_next += 1
            elif reason == 'GEN AT DISRUPTED NODE':
                self.mg_ag.count_failed_gen += 1
            elif reason == 'DISRUPT':
                self.mg_ag.count_failed_disrupt += 1
            elif reason == 'COST':
                self.mg_ag.count_failed_cost += 1
            elif reason == 'PFAD':
                self.mg_ag.count_failed_pfad += 1
            elif reason == 'QUEUE':
                self.mg_ag.count_failed_queue += 1
            elif reason == 'GEN AT FULL BUFFER':
                self.mg_ag.count_failed_gen_full_buffer += 1
                self.mg_ag.agents_generated_list.remove(self)

            #Layer-ID abrufen für Pie-Chart
            lyr_id = self.mg_ag.node_layer[self.so]
            self.mg_ag.lyr_id_fail.append(lyr_id)

            self.mg_ag.nodes_waf.append(self.so) # An List anhängen für Knoten wo Agenten Failen

            # Aus Warteschlangen entfernen
            self.mg_ag.node_queue_load[self.so] = self.mg_ag.node_queue_load[self.so] - self.load
            if self in self.mg_ag.node_queue[self.so]:
                self.mg_ag.node_queue[self.so].remove(self)

            self.mg_ag.agents_failed.append(self)
            self.display_agent()
            self.mg_ag.agent_list.remove(self)
            self.mg_ag.agents_failed_count += 1
            self.mg_ag.agent_count -= 1
            del self


    def display_count(self):
            print("There are " + str(agent.agent_count) + " agents in the network ")

    # Ausgabe der Agenten-Eigenschaften und -Zählern in einer CSV-Datei
    def display_agent(self):
        datei = open(file_agents, 'a')
        with datei:
            writer = csv.writer(datei)
            writer.writerow([str(self.ID), str(self.load), str(self.so),str(self.start), str(self.dest),
                            str(self.route['path']), str(self.route['cost']), str(self.route['time']),
                            str(self.actual_route_cost),str(self.route_changes),str(self.t), str(self.state),
                            str(self.t_at_edge), str(self.t_at_node), str(self.cost_next_edge),
                            str(self.t_at_edge_max), str(self.mg_ag.ID)])