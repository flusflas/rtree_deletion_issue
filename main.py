import json
import os
import random
import uuid

from rtree.index import Index, Property
from shapely.geometry import shape, Point, MultiPolygon, Polygon


def gen_random_point(number, polygon, seed=None):
    """ Returns a `number` of random points inside the given `polygon`. """
    random.seed(seed)
    list_of_points = []
    minx, miny, maxx, maxy = polygon.bounds
    counter = 0
    while counter < number:
        pnt = Point(random.uniform(minx, maxx), random.uniform(miny, maxy))
        if polygon.contains(pnt):
            list_of_points.append(pnt)
            counter += 1
    return list_of_points


def get_polygons(geometry):
    if isinstance(geometry, MultiPolygon):
        for polygon in geometry.geoms:
            yield polygon
    elif isinstance(geometry, Polygon):
        yield geometry


def get_countries():
    """
    Returns a generator to iterate through a set of countries data.

    :return: Returns a 2-elements tuple with the country name and its geometry.
    """
    countries = []
    path = os.path.join(os.path.dirname(__file__), "countries.geo.json")

    with open(path, 'rb') as file:
        geojson = file.read()
        geojson = json.loads(geojson)

    for feature in geojson['features']:
        country_name = feature['properties']['name']
        geometry = shape(feature['geometry'])
        countries.append((country_name, geometry))

    return countries


def demo_delete():
    seed = 1    # Seed for random points

    countries = get_countries()

    country_id_to_remove = 170      # United States of America
    country_uuids_to_remove = []    # Polygons' ids to remove from the index

    properties = Property()
    # properties.writethrough = True
    # properties.leaf_capacity = 1000
    # properties.fill_factor = 0.5
    index = Index(properties=properties)

    points_per_polygon = 1
    points = []

    # Inserts countries data to the index
    for i, (country_name, geometry) in enumerate(countries):
        for polygon in get_polygons(geometry):
            temp_uuid = uuid.uuid1().int
            index.insert(temp_uuid, polygon.bounds, country_name)

            if i == country_id_to_remove:
                # Saves index ids of the polygon to be removed later
                country_uuids_to_remove.append(temp_uuid)

            # Generates random points in every polygon and saves them
            random_points = gen_random_point(points_per_polygon, polygon, seed)
            points.append((country_name, random_points))

    # Checks every generated point has matches
    for (country_name, country_points) in points:
        for point in country_points:
            hits = list(index.intersection(point.bounds, objects=True))
            assert any(hit.object == country_name for hit in hits)

    # Remove geometry
    geometry = shape(countries[country_id_to_remove][1])
    for i, polygon in enumerate(get_polygons(geometry)):
        index.delete(country_uuids_to_remove[i], polygon.bounds)

    points_missing = []

    # Checks (again) if every generated point has matches
    for (country_name, country_points) in points:
        for point in country_points:
            hits = list(index.intersection(point.bounds, objects=True))
            # Save any point without matches
            if not any(hit.object == country_name for hit in hits):
                points_missing.append(str(point) + " - " + country_name)

    # Print missing points
    for point in points_missing:
        print(point)


if __name__ == '__main__':
    demo_delete()
