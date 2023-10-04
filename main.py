#todo: koniecznosc zainstalowania OWSLib do wfs
#todo: utworzenie grup w qgisie
#todo: utworzenie takiej liczby projektow, ile jest map w arcgisie

import json
import sys
from typing import List, Union

from PyQt5.QtWidgets import QApplication
from owslib.wfs import WebFeatureService
from owslib.wms import WebMapService
from owslib.wmts import WebMapTileService
from qgis.core import *

TEMP_FILE_QGS_PATH = r'C:\Users\klaud\OneDrive\Dokumenty\geoinformatyka\III_rok\praca_inz\new_env_qgis\temp2.qgs'
JSON_PATH = r'C:\Users\klaud\OneDrive\Dokumenty\geoinformatyka\III_rok\praca_inz\arcpy_env\aprx_data2.json'
WMS_CORRECT_LINK = 'contextualWMSLegend=0&crs=EPSG:{crs}&dpiMode=7&featureCount=10&format=image/png8&layers={layer}' \
                   '&styles&url={url}'
WMTS_CORRECT_LINK = 'contextualWMSLegend=0&dpiMode=7&featureCount=10&format=image/png8&layers={layer}&styles' \
                    '&tileMatrixSet={crs}&crs={crs}&url={url}?SERVICE%3DWMTS%26REQUEST%3DGetCapabilities'
WFS_CORRECT_LINK = '{url}?typename={layer}'


def read_aprx_project_properties(json_path: str) -> dict:
    with open(json_path, 'r') as f:
        data = json.load(f)
    return data


class NewQgsProjectBasedOnAprx:
    layers_dict = {
        'Shape File': QgsVectorLayer,
        'Raster': QgsRasterLayer
    }
    web_layers_dict = {
        'WMS': (WebMapService, '1.3.0', WMS_CORRECT_LINK, QgsRasterLayer, 'wms', "'crs': crs, "),
        'WMTS': (WebMapTileService, '1.0.0', WMTS_CORRECT_LINK, QgsRasterLayer, 'wms',
                 "'crs': list(web_layer_service.tilematrixsets.keys())[0], "),
        'WFS': (WebFeatureService, '2.0.0', WFS_CORRECT_LINK, QgsVectorLayer, 'wfs', '')
    }

    def __init__(self, json_dict, arcgis_map_name):
        self.json_dict = json_dict.get(arcgis_map_name)
        project = self.create_new_project()
        map_crs = self.get_properties_from_aprx('map_crs')
        self.set_crs_for_project(project, map_crs)
        self.set_extent_for_project(project, map_crs)
        map_layers = self.get_properties_from_aprx('map_layers')
        self.add_layers_to_project(project, map_layers)
        self.save_project(project, TEMP_FILE_QGS_PATH)

    def create_new_project(self) -> QgsProject:
        project = QgsProject.instance()
        return project

    def get_properties_from_aprx(self, aprx_property: str) -> List[Union[str, str]]:
        return self.json_dict.get(aprx_property)

    def set_crs_for_project(self, project: QgsProject, map_crs: List[str]):
        project.setCrs(QgsCoordinateReferenceSystem(f"EPSG:{map_crs}"))

    def set_extent_for_project(self, project: QgsProject, map_crs: List[str]):
        view_settings = project.viewSettings()
        referenced_rect = QgsReferencedRectangle()
        referenced_rect.setCrs(QgsCoordinateReferenceSystem(f"EPSG:{map_crs}"))
        referenced_rect.setXMinimum(self.get_properties_from_aprx('extent_xmin'))
        referenced_rect.setXMaximum(self.get_properties_from_aprx('extent_xmax'))
        referenced_rect.setYMinimum(self.get_properties_from_aprx('extent_ymin'))
        referenced_rect.setYMaximum(self.get_properties_from_aprx('extent_ymax'))
        view_settings.setDefaultViewExtent(referenced_rect)

    def add_group_to_project(self, group_name: str) -> QgsLayerTreeGroup:
        root = QgsProject.instance().layerTreeRoot()
        # group = QgsLayerTreeGroup(group_name)
        group = root.insertGroup(0, group_name)
        return group

    def add_layers_to_project(self, project: QgsProject, map_layers: list):
        for map_layer in list(reversed(map_layers)):
            for key, value in map_layer.items():
                if key in 'GroupLayer':
                    group_name = value.get('name')
                    group = self.add_group_to_project(group_name)
                    for group_layer in value.get('layers'):
                        if group_layer:
                            source = value.get('layers').get(group_layer).get('source')
                            name = value.get('layers').get(group_layer).get('name')
                            crs = value.get('layers').get(group_layer).get('crs')
                            transparency = value.get('layers').get(group_layer).get('transparency')
                            visible = value.get('layers').get(group_layer).get('visible')
                            if group_layer in self.web_layers_dict.keys():
                                layer = self.create_web_layer(source, name, crs, *self.web_layers_dict.get(group_layer))
                            else:
                                layer_type = self.layers_dict.get(group_layer)
                                layer = layer_type(source, name)
                                if layer:
                                    layer.setCrs(QgsCoordinateReferenceSystem(f'EPSG:{crs}'))
                            if layer:
                                group.addLayer(layer)
                                renderer = ''
                                if layer.type() == 1:
                                    renderer = '.renderer()'
                                eval(f'layer{renderer}.setOpacity({transparency} / 100.0)')
                                project.layerTreeRoot().findLayer(layer.id()).setItemVisibilityChecked(visible)
                    continue
                source = value.get('source')
                name = value.get('name')
                crs = value.get('crs')
                transparency = value.get('transparency')
                visible = value.get('visible')
                if key in self.web_layers_dict.keys():
                    layer = self.create_web_layer(source, name, crs, *self.web_layers_dict.get(key))
                else:
                    layer_type = self.layers_dict.get(key)
                    layer = layer_type(source, name)
                    if layer:
                        layer.setCrs(QgsCoordinateReferenceSystem(f'EPSG:{crs}'))
                if layer:
                    project.addMapLayer(layer)
                    renderer = ''
                    if layer.type() == 1:
                        renderer = '.renderer()'
                    eval(f'layer{renderer}.setOpacity({transparency} / 100.0)')
                    project.layerTreeRoot().findLayer(layer.id()).setItemVisibilityChecked(visible)

    def create_web_layer(self, source, name, crs, web_service, version, correct_link, layer_type, data_provider,
                         crs_str):
        web_layer_service = web_service(source, version=version)
        for service in list(web_layer_service.contents):
            if web_layer_service.contents[service].title == name:
                service_id = web_layer_service.contents[service].id
                correct_url_str = f"correct_link.format_map({{{crs_str}'layer': service_id, 'url': source}})"
                correct_url = eval(correct_url_str)
                layer = layer_type(correct_url, name, data_provider)
                layer.setCrs(QgsCoordinateReferenceSystem(f'EPSG:{crs}'))
                return layer

    def save_project(self, project, file_path):
        project.write(file_path)


def main():
    qgs = QApplication(sys.argv)
    QgsApplication.setPrefixPath(r"C:/PROGRA~1/QGIS3~1.16/apps/qgis-ltr", True)
    QgsApplication.initQgis()
    json_dict = read_aprx_project_properties(JSON_PATH)
    for arcgis_map_name in json_dict.keys():
        NewQgsProjectBasedOnAprx(json_dict=json_dict, arcgis_map_name=arcgis_map_name)


if __name__ == '__main__':
    main()
