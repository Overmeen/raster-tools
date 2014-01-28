# -*- coding: utf-8 -*-
# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.

from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division

import argparse
import json
import logging
import os
import sys
import urllib

from osgeo import gdal
from osgeo import ogr
from osgeo import osr

logger = logging.getLogger(__name__)
operations = {}

DRIVER_OGR_MEMORY = ogr.GetDriverByName(b'Memory')
DRIVER_GDAL_GTIFF = gdal.GetDriverByName(b'gtiff')
POLYGON = 'POLYGON (({x1} {y1},{x2} {y1},{x2} {y2},{x1} {y2},{x1} {y1}))'


class Index(object):
    """ Base class for index """

class RemoteIndex(object):
    def __init__(self, server, layer, polygon):
        """ Call strategy and transform it into an index. """
        parameters = dict(
            layers=','.join(layers),
            request='getstrategy',
            polygon=polygon.ExportToWkt(),
            projection=projection,
        )
        self.url = '{}?{}'.format(
            server,
            urllib.urlencode(parameters)
        )
        strategy = json.load(urllib.urlopen(urlfile))


class Operation(object):
    """
    Base class for operations.
    """
    def __init__(self, **kwargs):
        """ An init that accepts kwargs. """

class Elevation(Operation):
    """ Just store the elevation. """
    name = 'elevation'
    
    layers = dict(elevation=['elevation'])
    no_data_value = 3.4028235e+38
    data_type = 6
    
    def calculate(block):
        block[self.layers['elevation']].ReadAsArray().tostring()


def get_remote_index(server, layer, feature, projection):
    """
localhost:5000/data?request=getstrategy&layers=elevation&polygon=POLYGON((0.1%200.1,255.9%200.1,%20255.9%20255.9,%200.1%20255.9,0.1%200.1))&projection=epsg:28992&width=256&height=256
    """
    """
    Return ogr memory datasource
    """
    polygon = layer.GetExtent()
    # build the strayegy request url
    get_parameters = dict(
        request='getstrategy',
        layers=layers,
        polygon=None,
    )
    remote = urllib.urlopen(url)
    strategy = None
    ogr_driver = ogr.GetDriverByName('Memory')
    return json.load(remote)

def create_gdal_dataset(strategy, target_dir, name):
    """ Create the big tiff dataset. """
    gdal_driver = gdal.GetDriverByName('gtiff')
    gdal_driver.Create()


def get_dataset(layer, block):
    pass

class Chunk():
    """ 
    Represents a remote chunk of data.
    
    Ideally maps exactly to a remote storage chunk.
    """
    def __init__(self, width, height, layers, server, polygon, projection):
        """ Prepare url. """
        parameters = dict(
            width=str(width),
            height=str(width),
            layers=','.join(layers),
            request='getgeotiff',
            compress='deflate',
            polygon=polygon.ExportToWkt(),
            projection=projection,
        )
        self.url = '{}?{}'.format(
            server,
            urllib.urlencode(parameters)
        )

    def load(self):
        """ Load dataset from server. """
        url_file = urllib.urlopen(self.url)
        vsi_file = gdal.VSIFOpenL('myfile', 'w')
        vsi_file.write(url_file.read())
        vsi_file.close()
        # now what?
        self.dataset = None

class Block(object):
    """ Self saving local chunk of data. """
    def __init__(self, polygon):
        pass

class Target(object):
    """
    """
    def __init__(self, path, operation, **kwargs):
        pass
   
    def __iter__(self):
        for i in []:
            yield Block()
        

def extract(ogr_feature, target_dir, **kwargs):
    """ Extract for a single feature. """
    target = Target(path=target_path,
                    operation=target_operation)
    for block in target:  # target knows what has been done.
        for layer in operation.layers:
            # get some chunk
            for chunks in get_chunks:
                gdal.ReprojectImage(chunk, block['layer'])
        block.excute()  # no execute if no data!

class Preparation(object):
    """ Preparation. """
    # transform geometry
    # determine target path
    # get or create local index
    # get or create target tif
    # fail if existing tif does not match
    def __init__(self, path, feature, **kwargs):
        """ Prepare a lot. """
        attribute = kwargs.pop('attribute')
        self.path = self._make_path(path, feature, attribute)
        self.server = kwargs.pop('server')
        self.cellsize = kwargs.pop('cellsize')
        self.projection = kwargs.pop('projection')
        self.operation = operations[kwargs.pop('operation')](**kwargs)
        self.geometry = self._prepare_geometry(feature)
        self.dataset = self._get_or_create_dataset()
        self.index = self._create_index()

    def _make_path(self, path, feature, attribute):
        """ Prepare a path from feature attribute or id. """
        if attribute:
            name = feature[attribute] + '.tif'
        else:
            name = str(feature.GetFID()) + '.tif'
        return os.path.join(path, name)

    def _prepare_geometry(self, feature):
        """ Transform geometry if necessary. """
        geometry = feature.geometry()
        sr = geometry.GetSpatialReference()
        if sr:
            wkt = osr.GetUserInputAsWKT(str(self.projection))
            ct = osr.CoordinateTransformation(
                sr, osr.SpatialReference(wkt),
            )
            geometry.Transform(ct)
        return geometry


    def _create_index(self):
        """ 
        Create index dataset.
        """
        index = DRIVER_OGR_MEMORY.CreateDataSource('')

        # create layer
        wkt = osr.GetUserInputAsWKT(str(self.projection))
        layer = index.CreateLayer(b'index', osr.SpatialReference(wkt))
        layer.CreateField(ogr.FieldDefn(b'p1', ogr.OFTInteger))
        layer.CreateField(ogr.FieldDefn(b'q1', ogr.OFTInteger))
        layer.CreateField(ogr.FieldDefn(b'p2', ogr.OFTInteger))
        layer.CreateField(ogr.FieldDefn(b'q2', ogr.OFTInteger))
        layer_defn = layer.GetLayerDefn()

        # add the polygons
        p, a, b, q, c, d = self.dataset.GetGeoTransform()
        u, v = self.dataset.GetRasterBand(1).GetBlockSize()
        U, V = self.dataset.RasterXSize, self.dataset.RasterYSize

        # add features
        for j in range(1 + (V - 1) // v):
            for i in range(1 + (U - 1) // u):
                # pixel indices and coordinates
                p1 = i * u
                q1 = j * v
                p2 = min(p1 + u, U)
                q2 = min(q1 + v, V)
                
                # polygon
                x1, y2 = p + a * p1 + b * q1, q + c * p1 + d * q1
                x2, y1 = p + a * p2 + b * q2, q + c * p2 + d * q2
                polygon = ogr.CreateGeometryFromWkt(
                    POLYGON.format(x1=x1, y1=y1, x2=x2, y2=y2),
                )
                if not polygon.Intersects(self.geometry):
                    continue
                
                # feature
                feature = ogr.Feature(layer_defn)
                feature[b'p1'] = p1
                feature[b'q1'] = q1
                feature[b'p2'] = p2
                feature[b'q2'] = q2
                feature.SetGeometry(polygon)
                layer.CreateFeature(feature)
        DRIVER_OGR_SHAPE = ogr.GetDriverByName(b'ESRI Shapefile')
        DRIVER_OGR_SHAPE.CopyDataSource(index, 'tmp')
        exit()


    def _get_or_create_dataset(self):
        """ Create a tif and check against operation and index. """
        if os.path.exists(self.path):
            return gdal.Open(self.path, gdal.GA_Update)
        
        # dir
        try:
            os.makedirs(os.path.dirname(self.path))
        except OSError:
            pass

        # properties
        a, b, c, d = self.cellsize[0], 0.0, 0.0, -self.cellsize[1]
        x1, x2, y1, y2 = self.geometry.GetEnvelope()
        p, q = a * (x1 // a), d * (y2 // d)
        
        width = -int((p - x2) // a)
        height = -int((q - y1) // d)
        import ipdb
        ipdb.set_trace() 
        geo_transform = p, a, b, q, c, d
        projection = osr.GetUserInputAsWKT(str(self.projection))

        # create
        dataset = DRIVER_GDAL_GTIFF.Create(
            self.path, width, height, 1, self.operation.data_type,
            ['TILED=YES', 'BIGTIFF=YES', 'SPARSE_OK=TRUE', 'COMPRESS=DEFLATE'],
        )
        dataset.SetProjection(projection)
        dataset.SetGeoTransform(geo_transform) 
        dataset.GetRasterBand(1).SetNoDataValue(self.operation.no_data_value)
    
    def _create_dataset(self):
        """ Create bigtiff dataset. """
        # Arguments
        datatype = gdal.GDT_Byte
        options = ['BIGTIFF=YES',
                   'TILED=YES',
                   'SPARSE_OK=YES',
                   'BLOCKXSIZE={}'.format(self.tilesize[0]),
                   'BLOCKYSIZE={}'.format(self.tilesize[1]),
                   'COMPRESS=DEFLATE']

        # Create
        driver = gdal.GetDriverByName(b'gtiff')
        dataset = driver.Create(path, width, height, 1, datatype, options)

        # Tweak
        dataset.SetGeoTransform((x1, cellwidth, 0, y2, 0, -cellheight))
        band = dataset.GetRasterBand(1)
        nodatavalue = 255
        band.SetNoDataValue(nodatavalue)

        return dataset


def command(shape_path, target_dir, **kwargs):
    """
    Prepare and extract for each feature.
    """
    datasource = ogr.Open(shape_path)
    layer = datasource[0]
    for feature in layer:
        preparation = Preparation(feature=feature, path=target_dir, **kwargs)
        extract(preparation)


def get_parser():
    """ Return argument parser. """
    parser = argparse.ArgumentParser(
        description="",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    # main
    parser.add_argument('shape_path',
                        metavar='SHAPE')
    parser.add_argument('target_dir',
                        metavar='GTIFF')
    # options
    parser.add_argument('-s', '--server',
                        default='https://raster.lizard.net')
    parser.add_argument('-o', '--operation',
                        default='elevation',
                        help='Operation')
    parser.add_argument('-a', '--attribute',
                        help='Attribute for tif filename.')
    parser.add_argument('-f', '--floor',
                        default=0.15,
                        help='Floor elevation above ground level')
    parser.add_argument('-c', '--cellsize',
                        default=[0.5, 0.5],
                        type=float,
                        nargs=2,
                        help='Cellsize for output file')
    parser.add_argument('-p', '--projection',
                        default='epsg:28992',
                        help='Spatial reference system for output file.')
    return parser


def main():
    """ Call command with args from parser. """
    operations.update({cls.name: cls
                       for cls in Operation.__subclasses__()})
    logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
    return command(**vars(get_parser().parse_args()))
