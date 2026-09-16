def classFactory(iface):
    from .plugin import GeoFlowGuidePlugin
    return GeoFlowGuidePlugin(iface)
