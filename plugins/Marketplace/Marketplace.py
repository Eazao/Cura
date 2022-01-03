# Copyright (c) 2022 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import os.path
from PyQt5.QtCore import pyqtProperty, pyqtSignal, pyqtSlot, QObject
from typing import Optional

from cura.CuraApplication import CuraApplication  # Creating QML objects and managing packages.

from UM.Extension import Extension  # We are implementing the main object of an extension here.
from UM.PluginRegistry import PluginRegistry  # To find out where we are stored (the proper way).

from .RemotePackageList import RemotePackageList  # To register this type with QML.
from .LocalPackageList import LocalPackageList  # To register this type with QML.


class Marketplace(Extension, QObject):
    """
    The main managing object for the Marketplace plug-in.
    """
    def __init__(self, parent: Optional[QObject] = None) -> None:
        QObject.__init__(self, parent)
        Extension.__init__(self)
        self._window: Optional["QObject"] = None  # If the window has been loaded yet, it'll be cached in here.
        self._plugin_registry: Optional[PluginRegistry] = None
        self._package_manager = CuraApplication.getInstance().getPackageManager()

        self._material_package_list: Optional[RemotePackageList] = None
        self._plugin_package_list: Optional[RemotePackageList] = None

        # Not entirely the cleanest code, since the localPackage list also checks the server if there are updates
        # Since that in turn will trigger notifications to be shown, we do need to construct it here and make sure
        # that it checks for updates...
        self._local_package_list = LocalPackageList(self)
        self._local_package_list.checkForUpdates(self._package_manager.local_packages)

        self._package_manager.installedPackagesChanged.connect(self.checkIfRestartNeeded)

        self._tab_shown: int = 0
        self._restart_needed = False

    def getTabShown(self) -> int:
        return self._tab_shown

    def setTabShown(self, tab_shown: int) -> None:
        if tab_shown != self._tab_shown:
            self._tab_shown = tab_shown
            self.tabShownChanged.emit()

    tabShownChanged = pyqtSignal()
    tabShown = pyqtProperty(int, fget=getTabShown, fset=setTabShown, notify=tabShownChanged)

    @pyqtProperty(QObject, constant=True)
    def MaterialPackageList(self):
        if self._material_package_list is None:
            self._material_package_list = RemotePackageList()
            self._material_package_list.packageTypeFilter = "material"

        return self._material_package_list

    @pyqtProperty(QObject, constant=True)
    def PluginPackageList(self):
        if self._plugin_package_list is None:
            self._plugin_package_list = RemotePackageList()
            self._plugin_package_list.packageTypeFilter = "plugin"
        return self._plugin_package_list

    @pyqtProperty(QObject, constant=True)
    def LocalPackageList(self):
        return self._local_package_list

    @pyqtSlot()
    def show(self) -> None:
        """
        Opens the window of the Marketplace.

        If the window hadn't been loaded yet into Qt, it will be created lazily.
        """
        if self._window is None:
            self._plugin_registry = PluginRegistry.getInstance()
            self._plugin_registry.pluginsEnabledOrDisabledChanged.connect(self.checkIfRestartNeeded)
            plugin_path = PluginRegistry.getInstance().getPluginPath(self.getPluginId())
            if plugin_path is None:
                plugin_path = os.path.dirname(__file__)
            path = os.path.join(plugin_path, "resources", "qml", "Marketplace.qml")
            self._window = CuraApplication.getInstance().createQmlComponent(path, {"manager": self})
        if self._window is None:  # Still None? Failed to load the QML then.
            return
        self.setTabShown(0)
        self._window.show()
        self._window.requestActivate()  # Bring window into focus, if it was already open in the background.

    @pyqtSlot()
    def setVisibleTabToMaterials(self) -> None:
        """
        Set the tab shown to the remote materials one.
        Not implemented in a more generic way because it needs the ability to be called with 'callExtensionMethod'.
        """
        self.setTabShown(1)

    def checkIfRestartNeeded(self) -> None:
        if self._package_manager.hasPackagesToRemoveOrInstall or len(
                self._plugin_registry.getCurrentSessionActivationChangedPlugins()) > 0:
            self._restart_needed = True
        else:
            self._restart_needed = False
        self.showRestartNotificationChanged.emit()

    showRestartNotificationChanged = pyqtSignal()

    @pyqtProperty(bool, notify=showRestartNotificationChanged)
    def showRestartNotification(self) -> bool:
        return self._restart_needed
