import json
import os
import sys
sys.path.append(r'C:\Program Files\QGIS 3.16\apps\qgis-ltr\python\qgis')
from typing import List, Union

from PyQt5.QtWidgets import QApplication
from owslib.wfs import WebFeatureService
from owslib.wms import WebMapService
from owslib.wmts import WebMapTileService
from qgis.core import *

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
        'Raster': QgsRasterLayer,
        'unknown_layer': None
    }
    web_layers_dict = {
        'WMS': (WebMapService, '1.3.0', WMS_CORRECT_LINK, QgsRasterLayer, 'wms', "'crs': crs, "),
        'WMTS': (WebMapTileService, '1.0.0', WMTS_CORRECT_LINK, QgsRasterLayer, 'wms',
                 "'crs': list(web_layer_service.tilematrixsets.keys())[0], "),
        'WFS': (WebFeatureService, '2.0.0', WFS_CORRECT_LINK, QgsVectorLayer, 'wfs', '')
    }
    groups_dict = {}
    layers_in_groups_dict = {}

    def __init__(self, json_dict, arcgis_map_name, qgis_folder_path, qgis_file_name):
        self.created_files_list = []
        self.arcgis_map_name = arcgis_map_name
        self.qgis_folder_path = qgis_folder_path
        self.qgis_file_name = qgis_file_name
        self.json_dict = json_dict.get(arcgis_map_name)
        project = self.create_new_project()
        map_crs = self._get_properties_from_aprx('map_crs')
        self._set_crs_for_project(project, map_crs)
        self._set_extent_for_project(project, map_crs)
        map_layers = self._get_properties_from_aprx('map_layers')
        self._clear_text_file()
        self._add_layers_to_project(project, map_layers)
        self._save_project(project, f'{qgis_folder_path}\\{self.qgis_file_name}_{arcgis_map_name}.qgs',
                           f'{self.qgis_file_name}_{arcgis_map_name}.qgs')
        self._save_created_files(set(self.created_files_list))

    def create_new_project(self) -> QgsProject:
        project = QgsProject.instance()
        project.clear()
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
        if not bool(value.get('supergroup_id')):
            root = QgsProject.instance().layerTreeRoot()
            group = root.insertGroup(0, group_name)
            return group

    def _add_layers_to_project(self, project: QgsProject, map_layers: list):
        self.list_of_layers = []
        for map_layer in reversed(map_layers):
            for key, value in map_layer.items():
                if key in 'GroupLayer':
                    group_name = value.get('name')
                    group = self._add_group_to_project(group_name, value)
                    if bool(group):
                        self.groups_dict[value.get('id')] = group
                        group.setItemVisibilityChecked(value.get('visible'))
                    continue
                if bool(value.get('supergroup_id')):
                    continue
                self._add_layer_to_project(key, value, True, project, None)
        for map_layer in map_layers:
            for key, value in map_layer.items():
                if bool(value.get('supergroup_id')) and key in 'GroupLayer':
                    group_name = value.get('name')
                    supergroup = self.groups_dict.get(value.get('supergroup_id'))
                    group = supergroup.addGroup(group_name)
                    self.groups_dict[value.get('id')] = group
                if bool(value.get('supergroup_id')) and key not in 'GroupLayer':
                    group = self.groups_dict.get(value.get('supergroup_id'))
                    self._add_layer_to_project(key, value, False, project, group)

    def _add_layer_to_project(self, key, value, add_to_legend, project, group):
        if key not in 'unknown_layer':
            source = value.get('source')
            name = value.get('name')
            crs = value.get('crs')
            transparency = value.get('transparency')
            visible = value.get('visible')
        if key in self.web_layers_dict.keys():
            layer = self._create_web_layer(source, name, crs, key, *self.web_layers_dict.get(key))
            if layer is True:
                return
        else:
            layer_type = self.layers_dict.get(key)
            if key == 'unknown_layer':
                if value.get('name'):
                    self._write_errors_to_text_file(f'Nieznany typ warstwy, {value.get("name")}')
                    return
            layer = layer_type(source, name)
            layer.setCrs(QgsCoordinateReferenceSystem(f'EPSG:{crs}'))
        if layer is None:
            self._write_errors_to_text_file(f'{key}, {name}')
            return
        QgsProject.instance().addMapLayer(layer, addToLegend=add_to_legend)
        if not bool(add_to_legend):
            group.addLayer(layer)
        if layer.type() == 1:
            layer.renderer().setOpacity((100.0 - float(transparency)) / 100.0)
        else:
            layer.setOpacity((100.0 - float(transparency)) / 100.0)
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
            return True

    def _save_project(self, project, file_path, file_name):
        project.write(file_path)
        self.created_files_list.append(file_name)

    def _clear_text_file(self):
        if os.path.isfile(f'{self.qgis_folder_path}\\errors_{self.qgis_file_name}_{self.arcgis_map_name}.txt'):
            with open(f'{self.qgis_folder_path}\\errors_{self.qgis_file_name}_{self.arcgis_map_name}.txt', 'w'):
                pass

    def _write_errors_to_text_file(self, message):
        with open(f'{self.qgis_folder_path}\\errors_{self.qgis_file_name}_{self.arcgis_map_name}.txt', 'a') \
                as errors_file:
            errors_file.write(f'Uwaga! Do projektu nie udało się zapisać warstwy: {message}\n')
            self.created_files_list.append(f'errors_{self.qgis_file_name}_{self.arcgis_map_name}.txt')

    def _save_created_files(self, files_list):
        with open(f'{os.getcwd()}\\saved_files.txt', 'a') as saved_files:
            saved_files.write('\n'.join(files_list))
            saved_files.write('\n')


def main(qgis_folder_path, qgis_file_name, qgis_instance_dir):
    qgs = QApplication(sys.argv)
    QgsApplication.setPrefixPath(f'{qgis_instance_dir}\\apps\\qgis-ltr', True)
    QgsApplication.initQgis()
    json_dict = read_aprx_project_properties(f'{arcgis_project_dir}\\arcgis_project_properties.json')
    for arcgis_map_name in json_dict.keys():
        NewQgsProjectBasedOnAprx(json_dict, arcgis_map_name, qgis_folder_path, qgis_file_name)


if __name__ == '__main__':
    arcgis_project_dir = os.getcwd()
    properties_for_qgis_project_dict = read_aprx_project_properties(
        f'{arcgis_project_dir}\\properties_for_qgis_project.json')
    _, qgis_folder_path, qgis_file_name, qgis_instance_dir = properties_for_qgis_project_dict.values()
    main(qgis_folder_path, qgis_file_name, qgis_instance_dir)
    os.remove(f'{arcgis_project_dir}\\properties_for_qgis_project.json')
    os.remove(f'{arcgis_project_dir}\\arcgis_project_properties.json')
