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
from requests import ReadTimeout
from urllib3.exceptions import ReadTimeoutError

TEMP_QGS_PATH = r'C:\Users\klaud\OneDrive\Dokumenty\geoinformatyka\III_rok\praca_inz\new_env_qgis'
TEMP_QGS_FILE_NAME = 'temp2.qgs'
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
    groups_dict = {}
    layers_in_groups_dict = {}

    def __init__(self, json_dict, arcgis_map_name):
        self.json_dict = json_dict.get(arcgis_map_name)
        project = self.create_new_project()
        map_crs = self._get_properties_from_aprx('map_crs')
        self._set_crs_for_project(project, map_crs)
        self._set_extent_for_project(project, map_crs)
        map_layers = self._get_properties_from_aprx('map_layers')
        self._clear_text_file()
        self._add_layers_to_project(project, map_layers)
        self.qgis_file_name, ext = TEMP_QGS_FILE_NAME.split('.')
        self._save_project(project, f'{TEMP_QGS_PATH}\\{self.qgis_file_name}_{arcgis_map_name}.{ext}')

    def create_new_project(self) -> QgsProject:
        project = QgsProject.instance()
        return project

    def _get_properties_from_aprx(self, aprx_property: str) -> List[Union[str, str]]:
        return self.json_dict.get(aprx_property)

    def _set_crs_for_project(self, project: QgsProject, map_crs: List[str]):
        project.setCrs(QgsCoordinateReferenceSystem(f"EPSG:{map_crs}"))

    def _set_extent_for_project(self, project: QgsProject, map_crs: List[str]):
        view_settings = project.viewSettings()
        referenced_rect = QgsReferencedRectangle()
        referenced_rect.setCrs(QgsCoordinateReferenceSystem(f"EPSG:{map_crs}"))
        referenced_rect.setXMinimum(self._get_properties_from_aprx('extent_xmin'))
        referenced_rect.setXMaximum(self._get_properties_from_aprx('extent_xmax'))
        referenced_rect.setYMinimum(self._get_properties_from_aprx('extent_ymin'))
        referenced_rect.setYMaximum(self._get_properties_from_aprx('extent_ymax'))
        view_settings.setDefaultViewExtent(referenced_rect)

    def _add_group_to_project(self, group_name: str, value: dict) -> QgsLayerTreeGroup:
        root = QgsProject.instance().layerTreeRoot()
        if value.get('supergroup_id'):
            supergroup = self.groups_dict.get(value.get('supergroup_id'))
            group = supergroup.addGroup(group_name)
            # self.groups_dict[value.get('id')] = group
            return group
        group = root.addGroup(group_name)
        return group

    def _add_layers_to_project(self, project: QgsProject, map_layers: list):
        list_of_layers = []
        for map_layer in map_layers:
            for key, value in map_layer.items():
                if key in 'GroupLayer':
                    group_name = value.get('name')
                    group = self._add_group_to_project(group_name, value)
                    self.groups_dict[value.get('id')] = group
                    # list_of_layers.append(group)
                    # group.setCustomProperty('id', value.get('id'))
                    group.setItemVisibilityChecked(value.get('visible'))
                    continue
                if bool(value.get('supergroup_id')):
                    self._add_layer_to_group(self.groups_dict.get(value.get('supergroup_id')), value, key)
                    continue
                    # return
                    # self.layers_in_groups_dict[]
                    # group = self.groups_dict.get(value.get('supergroup_id'))
                    # self._add_layer_to_project(value, key, 'group.addLayer(layer)', project, group)
                self._add_layer_to_project(value, key, 'QgsProject.instance().addMapLayer(layer)', project)
        QgsProject.instance().addMapLayers(list_of_layers)

    def _add_layer_to_group(self, group, value, key):
        # groupName = "test group"
        # root = QgsProject.instance().layerTreeRoot()
        # group = root.addGroup(groupName)
        # vlayer = QgsVectorLayer("C:/Temp/myShp.shp", "shpName", "ogr")
        source = value.get('source')
        name = value.get('name')
        crs = value.get('crs')
        transparency = value.get('transparency')
        visible = value.get('visible')
        if key in self.web_layers_dict.keys():
            vlayer = self._create_web_layer(source, name, crs, key, *self.web_layers_dict.get(key))
        else:
            layer_type = self.layers_dict.get(key)
            vlayer = layer_type(source, name, 'ogr')
            vlayer.setCrs(QgsCoordinateReferenceSystem(f'EPSG:{crs}'))
        if vlayer is None:
            self._write_errors_to_text_file(f'{key}, {name}')
            return
        # group.addLayer(vlayer)
        QgsProject.instance().addMapLayer(vlayer, False)
        renderer = ''
        if vlayer.type() == 1:
            renderer = '.renderer()'

        root = QgsProject.instance().layerTreeRoot()
        # layer = root.findLayer(vlayer.id())
        # clone = layer.clone()
        group.addLayer(vlayer)
        eval(f'vlayer{renderer}.setOpacity({transparency} / 100.0)')
        QgsProject.instance().layerTreeRoot().findLayer(vlayer.id()).setItemVisibilityChecked(visible)
        # root.removeChildNode(layer)

    def _add_layer_to_project(self, value, key, func_add, project, group=None):
        source = value.get('source')
        name = value.get('name')
        crs = value.get('crs')
        transparency = value.get('transparency')
        visible = value.get('visible')
        if key in self.web_layers_dict.keys():
            layer = self._create_web_layer(source, name, crs, key, *self.web_layers_dict.get(key))
        else:
            layer_type = self.layers_dict.get(key)
            if layer_type == 'Shape File':
                layer = layer_type(source, name, 'ogr')
            else:
                layer = layer_type(source, name)
            layer.setCrs(QgsCoordinateReferenceSystem(f'EPSG:{crs}'))
        if layer is None:
            self._write_errors_to_text_file(f'{key}, {name}')
            return
            # print()
        eval(func_add)
        renderer = ''
        if layer.type() == 1:
            renderer = '.renderer()'
        eval(f'layer{renderer}.setOpacity({transparency} / 100.0)')
        project.layerTreeRoot().findLayer(layer.id()).setItemVisibilityChecked(visible)

    def _create_web_layer(self, source, name, crs, key, web_service, version, correct_link, layer_type, data_provider,
                          crs_str):
        try:
            web_layer_service = web_service(source, version=version)
            for service in list(web_layer_service.contents):
                if web_layer_service.contents[service].title == name:
                    service_id = web_layer_service.contents[service].id
                    correct_url_str = f"correct_link.format_map({{{crs_str}'layer': service_id, 'url': source}})"
                    correct_url = eval(correct_url_str)
                    layer = layer_type(correct_url, name, data_provider)
                    layer.setCrs(QgsCoordinateReferenceSystem(f'EPSG:{crs}'))
                    return layer
        except:
            self._write_errors_to_text_file(f'{key}, {name}')

    def _save_project(self, project, file_path):
        project.write(file_path)

    def _write_errors_to_text_file(self, message):
        with open(f'{TEMP_QGS_PATH}\\errors.txt', 'a') as errors_file:
            errors_file.write(f'Uwaga! Do projektu nie udało się zapisać warstwy: {message}\n')

    def _clear_text_file(self):
        with open(f'{TEMP_QGS_PATH}\\errors.txt', 'w'):
            pass


def main():
    qgs = QApplication(sys.argv)
    QgsApplication.setPrefixPath(r"C:/PROGRA~1/QGIS3~1.16/apps/qgis-ltr", True)
    QgsApplication.initQgis()
    json_dict = read_aprx_project_properties(JSON_PATH)
    for arcgis_map_name in json_dict.keys():
        NewQgsProjectBasedOnAprx(json_dict=json_dict, arcgis_map_name=arcgis_map_name)


if __name__ == '__main__':
    main()
