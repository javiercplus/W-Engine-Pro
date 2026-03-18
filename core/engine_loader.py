import importlib
import logging

class EngineLoader:
    """
    Carga dinámicamente los motores desde el paquete 'core.engines'.
    """
    
    @staticmethod
    def load_engine(engine_name: str, config, surface_manager, monitor_id):
        """
        Carga e instancia un motor por su nombre.
        
        :param engine_name: El nombre del motor (ej: "mpv", "web"). Coincide con el nombre de la carpeta.
        :param config: Instancia de ConfigManager.
        :param surface_manager: Instancia de SurfaceManager para el motor.
        :param monitor_id: ID del monitor.
        :return: Una instancia del motor o None si falla.
        """
        try:
            if engine_name == "mpv":
                module_path = "core.engine"
                class_name = "MpvEngine"
            else:
                module_path = f"core.engines.{engine_name}_engine.engine"
                class_name = f"{engine_name.capitalize()}Engine"
            

            module = importlib.import_module(module_path)
            engine_class = getattr(module, class_name)
            
            return engine_class(config, surface_manager, monitor_id)
            
        except (ImportError, AttributeError) as e:
            logging.error(f"Fallo al cargar el motor '{engine_name}': {e}")
            return None
