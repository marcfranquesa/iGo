import csv
import pickle
import urllib
import collections
import networkx as nx
import osmnx as ox
from staticmap import StaticMap, CircleMarker, Line
from haversine import haversine
import requests
import os

PLACE = 'Barcelona, Catalonia'
GRAPH_FILENAME = 'barcelona.graph'
IGRAPH_FILENAME = 'ibarcelona.graph'
HIGHWAYS_URL = 'https://opendata-ajuntament.barcelona.cat/data/dataset/1090983a-1c40-4609-8620-14ad49aae3ab/resource/1d6c814c-70ef-4147-aa16-a49ddb952f72/download/transit_relacio_trams.csv'
CONGESTIONS_URL = 'https://opendata-ajuntament.barcelona.cat/data/dataset/8319c2b1-4c21-4962-9acd-6db4c5ff1148/resource/2d456eb5-4ea6-4f68-9794-2f3f1a58a933/download'


Highway = collections.namedtuple('Highway', 'id coordinates')
Congestion = collections.namedtuple('Congestion', 'id transit')


def exists_graph(graph_filename):
    '''Returns True if file exists and is a .graph file, returns False
     otherwise.'''
    try:
        f = open(graph_filename)
        return graph_filename[-5:] == 'graph'
    except:
        return False


def download_graph(place):
    '''Returns a graph object from a place, edges are the different streets and
    their weight indicates length.'''
    graph = ox.graph_from_place(place, network_type='drive', simplify=True)
    graph = ox.utils_graph.get_digraph(graph, weight='length')
    return graph


def save_graph(graph, graph_filename):
    '''Saves a graph object into a .graph file.'''
    with open(graph_filename, 'wb') as file:
        pickle.dump(graph, file)


def load_graph(graph_filename):
    '''Returns a graph objects from a .graph file.'''
    with open(graph_filename, 'rb') as file:
        return pickle.load(file)


def plot_graph(graph_filename):
    '''Plots a graph located in a .graph file.'''
    ox.plot_graph(graph_filename)


def download_highways(url):
    '''Reads a CSV file stored online and returns a list of highways. Each highway
    is formed by an id, a description and a list of tuples containing
    coordinates.'''

    # Gets information from url
    url_request = urllib.request.urlopen(url)
    lines = [line.decode('utf-8') for line in url_request.readlines()]
    csv_reader = csv.reader(lines)

    next(csv_reader)  # Skips header
    # Generates list of highways
    highway_list = []
    for line in csv_reader:

        # Grabs the information from the csv_reader
        id, _, coordinates = line

        # Makes a list containing coordinate tuples
        pairs_of_coords = []
        iterable = zip(*[iter(coordinates.split(','))]*2)
        for x, y in iterable:
            pairs_of_coords.append((float(x), float(y)))

        highway = Highway(id, pairs_of_coords)
        highway_list.append(highway)

    highway_list.sort()
    return highway_list


def plot_highways(highway_list, fileName='highways.png', size=500):
    '''Creates/modifies a png file with a map of barcelona and with the highways
    on the highway_list drawn. Variable highway_list is a list of highways,
    each highway is tuple containing an id, a description and coordinates.'''
    map = StaticMap(size, size)
    for highway in highway_list:
        highway = Line(highway.coordinates, 'green', 2)
        map.add_line(highway)
    image = map.render()
    image.save(fileName)


def download_congestions(url):
    '''Reads a file stored online and returns a list of congestions.
    Each congestions is formed  by an id, a time, a transit and a
    future transit.'''

    # Gets information from url
    url_request = urllib.request.urlopen(url)
    lines = [line.decode('utf-8') for line in url_request.readlines()]
    csv_reader = csv.reader(lines)

    congestion_list = []
    for line in csv_reader:
        # Generates a list containing the atributes
        atributes = str(line)[2:-2].split('#')
        congestion = Congestion(int(atributes[0]), int(atributes[2]))
        congestion_list.append(congestion)

    congestion_list.sort()
    return congestion_list


def plot_congestions(highway_list, congestion_list, fileName='congestions.png', size=500):
    '''Creates/modifies a png file with a map of barcelona
    and with the highways on the highway_list drawn with
    colors varying depending on the congestion.'''
    colors = ['green', 'yellow', 'orange', 'purple', 'red', 'grey', 'black']
    map = StaticMap(size, size)
    for i in range(len(highway_list)):
        highway_transit = congestion_list[i].transit
        highway = Line(highway_list[i].coordinates, colors[highway_transit], 2)
        map.add_line(highway)
    image = map.render()
    image.save(fileName)


def add_congestions(graph, highway_list, congestion_list):
    '''Adds the congestions from the list to the graph.'''

    # Adds/modifies variable congestion to all the edges in the graph,
    # sets it at 0
    nx.set_edge_attributes(graph, 0, 'congestion')
    for highway in range(len(highway_list)):

        congestion = congestion_list[highway].transit
        x_coordinates = [coordinate[0] for coordinate in highway_list[highway].coordinates]
        y_coordinates = [coordinate[1] for coordinate in highway_list[highway].coordinates]

        # Makes a list with the nodes nearest to each coordinate in the highway
        graph_nodes = ox.distance.nearest_nodes(graph, x_coordinates, y_coordinates)

        # Iterates in twos through the graph finding the shortest
        # path between the nodes and setting attribute congestion
        # in each edge to that of the highway
        for src, dst in zip(graph_nodes[:-1], graph_nodes[1:]):
            path = ox.distance.shortest_path(graph, src, dst)

            # Iterates through the path changing
            # the congestion attribute in each edge
            if path is not None:
                for src1, dst1 in zip(path[:-1], path[1:]):
                    graph.edges[src1, dst1]['congestion'] = congestion


def calculate_itime(congestion, speed, length):
    '''Calculates itime from the three attributes given.
    Congestion is a value from 0 to 6.'''
    if isinstance(speed, str) or isinstance(speed, int):
        avg_speed = int(speed)
    else:
        avg_speed = sum([int(item) for item in speed]) / len(speed)

    # List for each factor between all 6 types of congestions
    factor = [1.2, 1, 1.05, 1.2, 1.4, 1.7, 1e6]

    # Length is in meters so needs to be changed to km
    return length / 1e3 / avg_speed * factor[congestion]


def add_itime(graph):
    '''Adds itime attribute to all edges.'''
    nx.set_edge_attributes(graph, 1e6, 'itime')
    for edge in graph.edges:
        e = graph.edges[edge[0], edge[1]]
        congestion = e['congestion']
        # If no maxspeed can be found, sets it at 20 by default
        # happens mostly in residential areas
        try:
            speed = e['maxspeed']
        except:
            speed = 20
        length = e['length']
        e['itime'] = calculate_itime(congestion, speed, length)


def build_igraph(graph, highway_list, congestion_list):
    '''Builds the intelligent version of a given graph
    adding congestions and itime.'''
    add_congestions(graph, highway_list, congestion_list)
    add_itime(graph)
    return graph


def get_shortest_path_with_ispeeds(graph, origin, destination):
    '''Finds the shortest path between two given nodes
    comparing the itime attribute.'''

    # If the node is a string it tranforms it to the corresponding coordinates
    origin = coordinates(origin)
    destination = coordinates(destination)

    x_coordinates = [origin[1], destination[1]]
    y_coordinates = [origin[0], destination[0]]
    nodes = ox.distance.nearest_nodes(graph, x_coordinates, y_coordinates)
    path = ox.distance.shortest_path(graph, nodes[0], nodes[1], weight='itime')
    return path


def plot_path(graph, path, fileName='path.png', size=800):
    '''Creates/modifies a png file with a map of
    barcelona and the steet paths in red.'''
    map = StaticMap(size, size)
    coordinates = []
    for node in path:
        coordinate = (graph.nodes[node]['x'], graph.nodes[node]['y'])
        coordinates.append(coordinate)
    route = Line(coordinates, 'red', 3)
    map.add_line(route)

    image = map.render()
    image.save(fileName)


def create_igraph():
    '''Creates igraph from scratch.'''

    print('Creating Barcelona graph.')
    graph = download_graph(PLACE)

    print('Downloading highways and congestions.')
    highways = download_highways(HIGHWAYS_URL)
    congestions = download_congestions(CONGESTIONS_URL)
    print('Building igraph, this may take a while.')
    igraph = build_igraph(graph, highways, congestions)

    print('Igraph is built and saved.')
    return highways, igraph


def update_igraph_file(igraph, highways):
    '''Updates igraph given the highways.'''
    print('Updating igraph, this may take a while.')
    congestions = download_congestions(CONGESTIONS_URL)
    igraph = build_igraph(igraph, highways, congestions)
    print('Igraph is updated.')


def coordinates(location):
    '''Accepts either coordinates or a place and returns the
    corresponding coordinates. Returns None if place was not found.'''

    if not isinstance(location, str):
        return location
    try:
        tuple(map(float, text.split(' ')))
    except:
        try:
            return ox.geocoder.geocode(location + ', Barcelona')
        except:
            return None
