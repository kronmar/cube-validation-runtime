import argparse
import random
import os
from rdflib import BNode, Graph, Literal, Namespace, RDF, SH, URIRef, XSD
from rdflib.collection import Collection

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

cube = Namespace("https://cube.link/")
schema = Namespace("http://schema.org/")
qudt = Namespace("http://qudt.org/schema/qudt/")


def generate_cube(graph: Graph, cube_url: str, dims: int, obs: int):
    graph.add((URIRef(cube_url), RDF.type, cube.Cube))
    graph.add((URIRef(cube_url), RDF.type, schema.Dataset))
    graph.add((URIRef(cube_url), schema.name, Literal(f"Cube mit {dims} Dimensionen, {obs} Observations")))
    graph.add((URIRef(cube_url), schema.description, Literal(f"Cube mit {dims} Dimensionen, {obs} Observations")))
    graph.add((URIRef(cube_url), cube.observationSet, URIRef(cube_url + "observationSet/")))
    graph.add((URIRef(cube_url), cube.observationConstraint, URIRef(cube_url + "shape/")))


def generate_observations(graph: Graph, obs: int, dims: int, cube_url: str):
    graph.add((URIRef(cube_url + "observationSet"), RDF.type, cube.ObservationSet))

    for obs in range(obs):
        obs_url = cube_url + f"observations/obs-{obs}"
        graph.add((URIRef(cube_url + "observationSet"), cube.observation, URIRef(obs_url)))
        graph.add((URIRef(obs_url), RDF.type, cube.Observation))

        for dim in range(dims):
            dim_path = cube_url + f"dimensions/dim-{dim}"
            graph.add((URIRef(obs_url), URIRef(dim_path), Literal(random.uniform(0, 1), datatype=XSD.decimal)))


def generate_shape(graph: Graph, cube_url: str, dims: int):
    graph.add((URIRef(cube_url + "shape/"), RDF.type, SH.NodeShape))
    graph.add((URIRef(cube_url + "shape/"), RDF.type, cube.Constraint))
    graph.add((URIRef(cube_url + "shape/"), SH.closed, Literal(True, datatype=XSD.boolean)))

    # Constraint for "sh.path rdf.type"
    type_node = BNode()
    graph.add((URIRef(cube_url + "shape/"), SH.property, type_node))
    graph.add((type_node, SH.path, RDF.type))
    graph.add((type_node, SH.nodeKind, SH.IRI))
    possible_type_nodes = BNode()
    graph.add((type_node, SH + "in", possible_type_nodes))
    Collection(graph, possible_type_nodes, [cube.Observation])

    for dim in range(dims):
        dim_path = cube_url + f"dimensions/dim-{dim}"
        bnode = BNode()
        graph.add((URIRef(cube_url + "shape/"), SH.property, bnode))
        graph.add((bnode, SH.path, URIRef(dim_path)))
        graph.add((bnode, SH.minCount, Literal(1)))
        graph.add((bnode, SH.maxCount, Literal(1)))
        graph.add((bnode, qudt.scaleType, qudt.IntervalScale))

        # datatype: either cube:undefined or xsd:decimal with maxInclusive and minInclusive
        or_node = BNode()
        graph.add((bnode, SH + "or", or_node))

        undefined_node = BNode()
        graph.add((undefined_node, SH.datatype, cube.Undefined))

        defined_node = BNode()
        graph.add((defined_node, SH.maxInclusive, Literal(1)))
        graph.add((defined_node, SH.minInclusive, Literal(0)))
        graph.add((defined_node, SH.datatype, XSD.decimal))

        Collection(graph, or_node, [undefined_node, defined_node])


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('dims', type=int, help='Number of dimensions')
    parser.add_argument('obs', type=int, help='Number of observations')

    args = parser.parse_args()

    base_url = f"https://test.ld.admin.ch/test/{args.dims}-{args.obs}/"
    cube_url = base_url + "cube/"

    graph = Graph()
    graph.bind("cube", cube)
    graph.bind("schema", schema)
    graph.bind("test", Namespace("https://environment.ld.admin.ch/foen/nfi/test/"))
    graph.bind("qudt", qudt)

    generate_cube(graph=graph, cube_url=cube_url, dims=args.dims, obs=args.obs)

    generate_observations(graph=graph, dims=args.dims, obs=args.obs, cube_url=cube_url)

    generate_shape(graph=graph, cube_url=cube_url, dims=args.dims)
    print(ROOT_DIR + f"/examples/{args.dims}-{args.obs}.ttl")
    graph.serialize(destination=ROOT_DIR + f"/examples/{args.dims}-{args.obs}.ttl", format="turtle")


if __name__ == "__main__":
    main()
