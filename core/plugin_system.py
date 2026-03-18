import logging

class PluginSystem:
    """
    Registry for engines and plugins.
    Allows for dynamic discovery of new engine types.
    """
    
    ENGINE_REGISTRY = {}

    @classmethod
    def register_engine(cls, name, engine_class):
        """
        Registers an engine class in the system.
        name: unique str identifier.
        engine_class: class inheriting from WallpaperEngineInterface.
        """
        if name in cls.ENGINE_REGISTRY:
            logging.warning(f"Engine '{name}' is already registered and will be overwritten.")
        
        cls.ENGINE_REGISTRY[name] = engine_class
        logging.info(f"Engine '{name}' successfully registered.")

    @classmethod
    def get_engine(cls, name):
        """Returns the registered class for the engine name."""
        return cls.ENGINE_REGISTRY.get(name)

    @classmethod
    def list_engines(cls):
        """Returns the list of registered engine names."""
        return list(cls.ENGINE_REGISTRY.keys())
