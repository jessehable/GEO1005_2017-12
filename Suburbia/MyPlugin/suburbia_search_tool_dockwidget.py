# -*- coding: utf-8 -*-
"""
/***************************************************************************
 MyPluginDockWidget
                                 A QGIS plugin
 Green Housing Search
                             -------------------
        begin                : 2018-01-09
        git sha              : $Format:%H$
        copyright            : (C) 2018 by Elias Vetter
        email                : vetterelias@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""



import os
from PyQt4.QtCore import pyqtSignal,pyqtSlot
from PyQt4 import QtGui, QtCore, uic
from qgis.core import *
from qgis.networkanalysis import *
from qgis.gui import *
from qgis.gui import QgsMapToolEmitPoint
from PyQt4.QtGui import QColor
from qgis.gui import QgsHighlight
import os.path

# matplotlib for the charts
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import resources
import webbrowser

import os
import os.path
import random
import csv
import time

from . import utility_functions as uf


FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'suburbia_search_tool_dockwidget_base.ui'))


class MyPluginDockWidget(QtGui.QDockWidget, FORM_CLASS):

    closingPlugin = pyqtSignal()

    updateAttribute = QtCore.pyqtSignal(str)


    def __init__(self, iface, parent=None):
        """Constructor."""
        super(MyPluginDockWidget, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
        self.Tabs.setCurrentIndex(0)
        self.TabPreferences.setEnabled(False)
        self.TabMetrics.setEnabled(False)

        # define globals
        self.iface = iface
        self.pref =[0,0,0,0]
        self.plugin_dir = os.path.dirname(__file__)
        self.canvas = self.iface.mapCanvas()
        self.userdata = []
        self.h_list = []



        #data
        self.loadDataRotterdam()
        self.layers = self.iface.legendInterface().layers()

        #setup GUI features
        self.SuburbiaLogo.setPixmap(QtGui.QPixmap(self.plugin_dir + '/graphics/SuburbiaLogo.png'))
        self.LogoPreferences.setPixmap(QtGui.QPixmap(self.plugin_dir + '/graphics/002-settings.png'))
        self.LogoTerms.setPixmap(QtGui.QPixmap(self.plugin_dir + '/graphics/003-success.png'))
        self.LogoMetrics.setPixmap(QtGui.QPixmap(self.plugin_dir + '/graphics/001-chart.png'))
        self.InfoTerms.setIcon(QtGui.QIcon(self.plugin_dir + '/graphics/info.png'))
        self.InfoPreferences.setIcon(QtGui.QIcon(self.plugin_dir + '/graphics/info.png'))
        self.InfoMetrics.setIcon(QtGui.QIcon(self.plugin_dir + '/graphics/info.png'))
        self.ButtonPrivacyStatement.setIcon(QtGui.QIcon(self.plugin_dir + '/graphics/info.png'))

        self.FieldGender.addItems([
            self.tr('...'),
            self.tr('Male'),
            self.tr('Female'),
            self.tr('Other'), ])

        self.FieldEducation.addItems([
            self.tr('...'),
            self.tr('High School'),
            self.tr('College'),
            self.tr('University'), ])

        self.SelectionNeighborhood.addItems(sorted(uf.getFieldValues(
            (uf.getLegendLayerByName(self.iface, "Rotterdam_Selection")), "BU_NAAM")[0]))

        ### setup GUI signals
        #Registration
        self.ButtonConfirm.setEnabled(False)
        self.FieldName.textChanged.connect(self.EnableButtonConfirm)
        self.FieldAge.valueChanged.connect(self.EnableButtonConfirm)
        self.FieldGender.activated.connect(self.EnableButtonConfirm)
        self.FieldEducation.activated.connect(self.EnableButtonConfirm)
        self.ButtonAgree.clicked.connect(self.EnableButtonConfirm)
        self.ButtonConfirm.clicked.connect(self.Confirm)
        self.InfoTerms.clicked.connect(self.OpenInfoTerms)
        self.ButtonPrivacyStatement.clicked.connect(self.OpenInfoPrivacyStatement)

        #Preferences
        self.SliderPeople.valueChanged.connect(self.setPrioritynumbers)
        self.SliderChild.valueChanged.connect(self.setPrioritynumbers)
        self.SliderAccess.valueChanged.connect(self.setPrioritynumbers)
        self.SliderAfford.valueChanged.connect(self.setPrioritynumbers)
        self.InfoPreferences.clicked.connect(self.OpenInfoPreferences)


        self.ButtonExplore.clicked.connect(self.Explore)
        self.ButtonLocate.clicked.connect(self.Locate)

        #Metrics
        self.Legend.setPixmap(QtGui.QPixmap(self.plugin_dir + '/graphics/Match_icon.png'))
        self.ButtonAdjustPreferences.clicked.connect(self.Confirm)
        self.InfoMetrics.clicked.connect(self.OpenInfoMetrics)
        self.ButtonFavorite.clicked.connect(self.AddFavorite)
        self.ButtonFavorite.clicked.connect(self.UpdateLogMunicipality)
        self.ButtonSaveUserInfo.clicked.connect(self.ExportFavoritesCSV)

        #Explore

        self.pointTool = QgsMapToolEmitPoint(self.canvas)

        self.pointTool.canvasClicked.connect(self.display_point)

        self.canvas.setMapTool(self.pointTool)


    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()

    def NewUser(self):
        self.TabTerms.setEnabled(True)
        self.Tabs.setCurrentIndex(0)
        self.TabPreferences.setEnabled(False)
        self.TabMetrics.setEnabled(False)

#######
#    Vizualisation
#######

#   adding links to the information icons.
    def OpenInfoPrivacyStatement(self):
        webbrowser.open('https://github.com/jessehable/GEO1005_2017_G12_Suburbia/wiki/8.-Privacy-Statement', new=2)

    def OpenInfoPreferences(self):
        webbrowser.open('https://github.com/jessehable/GEO1005_2017_G12_Suburbia/wiki/4.-SDSS-Concept', new=2)

    def OpenInfoMetrics(self):
        webbrowser.open('https://github.com/jessehable/GEO1005_2017_G12_Suburbia/wiki/3.-Data-component', new=2)

    def OpenInfoTerms(self):
        webbrowser.open('https://github.com/jessehable/GEO1005_2017_G12_Suburbia/wiki/1.-Quick-Start-Guide', new=2)

    def setPrioritynumbers(self):
        self.PriorityPeople.setNum(self.SliderPeople.value())
        self.PriorityChild.setNum(self.SliderChild.value())
        self.PriorityAccess.setNum(self.SliderAccess.value())
        self.PriorityAfford.setNum(self.SliderAfford.value())

    def displayContinuousStyle(self,layer_ui,attribute_ui):
        # ramp
        display_settings = {}
        # define the interval type and number of intervals
        # EqualInterval = 0; Quantile  = 1; Jenks = 2; StdDev = 3; Pretty = 4;
        display_settings['interval_type'] = 1
        display_settings['intervals'] = 20
        # define the line width
        display_settings['line_width'] = 0.5
        ramp = QgsVectorGradientColorRampV2(QtGui.QColor(255, 0, 0, 255), QtGui.QColor(0, 255, 0, 255), False)
        # any other stops for intermediate colours for greater control. can be edited or skipped
        ramp.setStops([QgsGradientStop(0.25, QtGui.QColor(255, 0,0, 255)),
                       QgsGradientStop(0.5, QtGui.QColor(255, 255, 0, 255)),
                       QgsGradientStop(0.75, QtGui.QColor(0, 255, 0, 255))])
        display_settings['ramp'] = ramp

        # call the update renderer function
        renderer = uf.updateRenderer(layer_ui, attribute_ui, display_settings)
        # update the canvas
        if renderer:
            layer_ui.setRendererV2(renderer)
            layer_ui.triggerRepaint()
            self.iface.legendInterface().refreshLayerSymbology(layer_ui)
            self.canvas.refresh()

    def showresults(self, feature):


        if feature[9] + feature[8] == 0.0:
            per_een = 0.0
        else:
            per_een = (feature[14] / ((float(feature[9]) + float(feature[8])) / 2))

        per_twee = ((1 - feature[15]) / (((feature[11])+ ( feature[12])) / 2))
        per_drie = ((1 - feature[16]) / (feature[13]))
        if (feature[10]) == 0:
            per_vier = 0
        else:
            per_vier = ((1 - feature[17]) / (feature[10]))

        percentage = (per_een + per_twee + per_drie + per_vier)/ 100
        progres = (feature[18] / percentage)
        self.progressBar.setValue(progres)

        self.DisplayNeighborhoodName.setText(str(feature[1]))
        self.ValuePeople.setNum(feature[8] * 100)
        self.ValueChild.setNum((feature[6] * 1000))
        self.ValueAccess.setNum((feature[7] * 1000))
        self.ValueAfford.setNum((feature[4] * 1000))







#######
#    Analysis functions
#######
    def EnableButtonConfirm(self):
        if self.ButtonAgree.isChecked() == True:
            if self.FieldName.isModified() == True:
                if self.FieldAge.value() != 0:
                    if self.FieldGender.currentIndex() != 0:
                        if self.FieldEducation.currentIndex() != 0:
                            self.ButtonConfirm.setEnabled(True)
        else:
            self.ButtonConfirm.setEnabled(False)

    def Confirm(self):
        self.TabTerms.setEnabled(False)
        self.TabPreferences.setEnabled(True)
        self.Tabs.setCurrentIndex(1)
        # Whenever user confirms, the header off the later exported savefavorites csv is added.
        header = ['Neighborhood',
                  'Similar People (%)',
                  'average distance to child care (m)',
                  'average distance to trainstation (m)',
                  'average housing price (euro)']
        self.userdata.append(header)

    def Explore(self):


        self.pref[0] = self.SliderPeople.value()
        self.pref[1] = self.SliderChild.value()
        self.pref[2] = self.SliderAccess.value()
        self.pref[3] = self.SliderAfford.value()
        self.TabPreferences.setEnabled(False)
        self.TabMetrics.setEnabled(True)
        self.Tabs.setCurrentIndex(2)

        layer_explore = uf.getLegendLayerByName(self.iface, "Rotterdam_Selection")

        uf.updateField(layer_explore, 'B1', self.SliderPeople.value())
        uf.updateField(layer_explore, 'B2', self.SliderChild.value())
        uf.updateField(layer_explore, 'B3', self.SliderAccess.value())
        uf.updateField(layer_explore, 'B4', self.SliderAfford.value())

        self.determineScore(layer_explore)
        self.displayContinuousStyle(layer_explore, 'Score')

    def Locate(self):

        self.pref[0] = self.SliderPeople.value()
        self.pref[1] = self.SliderChild.value()
        self.pref[2] = self.SliderAccess.value()
        self.pref[3] = self.SliderAfford.value()
        self.TabPreferences.setEnabled(False)
        self.TabMetrics.setEnabled(True)
        self.Tabs.setCurrentIndex(2)

        subburbe = self.SelectionNeighborhood.currentText()
        layer_explore = uf.getLegendLayerByName(self.iface, "Rotterdam_Selection")

        uf.updateField(layer_explore, 'B1', self.SliderPeople.value())
        uf.updateField(layer_explore, 'B2', self.SliderChild.value())
        uf.updateField(layer_explore, 'B3', self.SliderAccess.value())
        uf.updateField(layer_explore, 'B4', self.SliderAfford.value())

        self.determineScore(layer_explore)
        self.displayContinuousStyle(layer_explore, 'Score')

        feat = uf.selectFeaturesByListValues(layer_explore, "BU_NAAM", subburbe)
        att = feat.attributes()

        self.showresults(att)

    def determineScore(self, layer):
        res = False
        if layer:
            provider = layer.dataProvider()
            caps = provider.capabilities()
            if caps & QgsVectorDataProvider.AddAttributes:
                layer.startEditing()
                for feature in layer.getFeatures():
                    feature['B1'] = feature['B1'] * ((feature['25_44_Norm'] + feature['HH_MK_NORM']) / 2)
                    if feature['KDV_NORM'] != 0.0 and feature['BSO_NORM'] != 0.0:
                        feature['B2'] = feature['B2'] * (
                                (((1 - feature['KDV_NORM'])) + ((1 - feature['BSO_NORM']))) / 2)
                    else:
                        if feature['KDV_NORM'] != 0.0 and feature['BSO_NORM'] == 0.0:
                            feature['B2'] = feature['B2'] * (((1 - feature['KDV_NORM'])))
                        else:
                            if feature['KDV_NORM'] == 0 and feature['BSO_NORM'] != 0.0:
                                feature['B2'] = feature['B2'] * (((1 - feature['BSO_NORM'])))
                            else:
                                feature['B2'] = 0

                    if feature['TREIN_NORM'] != 0:
                        feature['B3'] = feature['B3'] * (1 - feature['TREIN_NORM'])
                    else:
                        feature['B3'] = 0

                    if feature['WOZ_NORM'] != 0:
                        feature['B4'] = feature['B4'] * (1 - feature['WOZ_NORM'])
                    else:
                        feature['B4'] = 0

                    feature['Score'] = feature['B1'] + feature['B2'] + feature['B3'] + feature['B4']
                    layer.updateFeature(feature)


                layer.commitChanges()
            res = True
        return res

    def display_point(self,point):

        coords = "Map Coordinates: {:.4f}, {:.4f}".format(point.x(), point.y())

        print coords

        closestFeatureId = 0

        layer = uf.getLegendLayerByName(self.iface, "Rotterdam_Selection")
        coords = QgsPoint(point.x(), point.y())
        if str(layer) != "None":
            pPnt = QgsGeometry.fromPoint(coords)
            feats = [feat for feat in layer.getFeatures()]
            for feat in feats:
                if pPnt.within(feat.geometry()):
                    closestFeatureId = feat.id()
                    break

            testlength = str(closestFeatureId)

        if testlength > 0:
            fid = closestFeatureId
            iterator = layer.getFeatures(QgsFeatureRequest().setFilterFid(fid))
            featuree = next(iterator)
            attrs = featuree.attributes()
            self.showresults(attrs)

        else:
            parishName = None

#######
#   Data functions
#######

    def loadDataRotterdam(self, filename=""):
        scenario_open = False
        scenario_file = os.path.join(os.path.dirname(__file__), 'sampledata', '2018-01-16_Suburbia_2016_v8.qgs')
        # check if file exists
        if os.path.isfile(scenario_file):
            self.iface.addProject(scenario_file)
            scenario_open = True
        else:
            last_dir = uf.getLastDir("SDSS")
            new_file = QtGui.QFileDialog.getOpenFileName(self, "", last_dir, "(*.qgs)")
            if new_file:
                self.iface.addProject(unicode(new_file))
                scenario_open = True

########
#   Urban planning functions for the user.
    def AddFavorite(self):
        # define variables to add to the favorite list
        a = self.DisplayNeighborhoodName.text()
        b = self.ValuePeople.text()
        c = self.ValueChild.text()
        d = self.ValueAccess.text()
        e = self.ValueAfford.text()
        to_add = [a,b,c,d,e]
        # check wether selection has not been saved as favorite yet.
        if to_add not in self.userdata:
            self.userdata.append(to_add)
        else:
            self.AlreayAddedPopup()

    def AlreayAddedPopup(self):
        msgBox = QtGui.QMessageBox()
        msgBox.setText("Neighborhood already added!")
        msgBox.setStandardButtons(QtGui.QMessageBox.Close)
        msgBox.exec_()

    def ExportFavoritesCSV(self):
        path_csv = QtGui.QFileDialog.getSaveFileName(self, 'Save File', '', 'CSV(*.csv)')
        # create csv with favotires
        if path_csv:
            with open(unicode(path_csv), 'wb') as stream:
                # open csv file for writing
                writer = csv.writer(stream)
                for i in self.userdata:
                    writer.writerow(i)

#   Urban planning function for urban planner.

    def UpdateLogMunicipality(self):
        with open(self.plugin_dir + '/municipality/log_municipality.csv', 'a') as fd:
            writer = csv.writer(fd)
            # Determine values of the row to be added
            age = self.FieldAge.text()
            gender = self.FieldGender.currentText()
            education = self.FieldEducation.currentText()
            pref_people = self.SliderPeople.value()
            pref_child = self.SliderChild.value()
            pref_access = self.SliderAccess.value()
            pref_afford = self.SliderAfford.value()
            neighborhood = self.DisplayNeighborhoodName.text()
            people = self.ValuePeople.text()
            child = self.ValueChild.text()
            access = self.ValueAccess.text()
            afford = self.ValueAfford.text()
            munic_new_row = [age,
                       gender,
                       education,
                       pref_people,
                       pref_child,
                       pref_access,
                       pref_afford,
                       neighborhood,
                       people,child,access,afford]
            # Ten add the row to the municipality.log
            writer.writerow(munic_new_row)





