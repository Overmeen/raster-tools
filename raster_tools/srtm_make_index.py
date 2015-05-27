# -*- coding: utf-8 -*-
# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
""" Create index for rasterdata processing.

Currently only implemented for SRTM data. """

from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division

import argparse
import logging
import os
import sys

import ogr
import osr

ogr.UseExceptions()
osr.UseExceptions()

logger = logging.getLogger(__name__)


def create_filter_geometry(filter_path):
    multi_polygons = {ogr.wkbMultiPolygon, ogr.wkbMultiPolygon25D}
    multi_polygon = ogr.Geometry(ogr.wkbMultiPolygon)
    datasource = ogr.Open(filter_path)
    layer = datasource[0]
    for feature in layer:
        geometry = feature.geometry()
        geometry_type = geometry.GetGeometryType()
        if geometry_type in multi_polygons:
            polygons = geometry
        else:
            polygons = geometry,
        for polygon in polygons:
            multi_polygon.AddGeometry(polygon)
    return multi_polygon.UnionCascaded()


def make_index(index_path, filter_path):
    driver = ogr.GetDriverByName(b'esri shapefile')
    data_source = driver.CreateDataSource(index_path)
    layer_name = os.path.basename(index_path)
    sr = osr.SpatialReference(osr.GetUserInputAsWKT(b'epsg:4326'))
    layer = data_source.CreateLayer(layer_name, sr)
    layer.CreateField(ogr.FieldDefn(b'BLADNR', ogr.OFTString))
    layer_defn = layer.GetLayerDefn()

    if filter_path is None:
        filter_geometry = None
    else:
        filter_geometry = create_filter_geometry(filter_path)

    yrange = xrange(-56, 60)
    total = len(yrange)
    ogr.TermProgress_nocb(0)
    for count, y in enumerate(yrange, 1):
        for x in range(-180, 180):
            x1, y1, x2, y2 = x, y, x + 1, y + 1
            lat = 'S{:02}'.format(-y) if y < 0 else 'N{:02}'.format(y)
            lon = 'W{:03}'.format(-x) if x < 0 else 'E{:03}'.format(x)
            feature = ogr.Feature(layer_defn)
            feature[b'BLADNR'] = '{}{}'.format(lat, lon)
            ring = ogr.Geometry(ogr.wkbLinearRing)
            ring.AddPoint_2D(x1, y1)
            ring.AddPoint_2D(x2, y1)
            ring.AddPoint_2D(x2, y2)
            ring.AddPoint_2D(x1, y2)
            ring.AddPoint_2D(x1, y1)
            geometry = ogr.Geometry(ogr.wkbPolygon)
            geometry.AddGeometry(ring)
            if filter_geometry is not None:
                if not geometry.Intersects(filter_geometry):
                    continue
            geometry.AssignSpatialReference(sr)
            feature.SetGeometry(geometry)
            layer.CreateFeature(feature)
        ogr.TermProgress_nocb(count / total)

    data_source.ExecuteSQL(b'CREATE SPATIAL INDEX ON {}'.format(layer_name))


def get_parser():
    """ Return argument parser. """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('index_path', metavar='INDEX')
    parser.add_argument('-f', '--filter', dest='filter_path')
    return parser


def main():
    """ Call command with args from parser. """
    kwargs = vars(get_parser().parse_args())

    logging.basicConfig(stream=sys.stderr,
                        level=logging.DEBUG,
                        format='%(message)s')

    try:
        make_index(**kwargs)
        return 0
    except:
        logger.exception('An exception has occurred.')
        return 1
