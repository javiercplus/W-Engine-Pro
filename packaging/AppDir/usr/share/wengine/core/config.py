import subprocess
import shutil


class HardwareDetector:
    """Detecta el hardware gráfico y recomienda configuraciones óptimas."""

    def __init__(self):
        self.gpu_vendor = self._detect_gpu()

    def _detect_gpu(self):
        try:
            if shutil.which("lspci"):
                output = (
                    subprocess.check_output("lspci | grep -i vga", shell=True)
                    .decode()
                    .lower()
                )
                if "nvidia" in output:
                    return "nvidia"
                elif "amd" in output or "advanced micro devices" in output:
                    return "amd"
                elif "intel" in output:
                    return "intel"

            if shutil.which("glxinfo"):
                output = (
                    subprocess.check_output(
                        "glxinfo | grep 'OpenGL vendor'", shell=True
                    )
                    .decode()
                    .lower()
                )
                if "nvidia" in output:
                    return "nvidia"
                elif "amd" in output or "ati" in output:
                    return "amd"
                elif "intel" in output:
                    return "intel"

        except Exception as e:
            print(f"[HardwareDetector] Error detectando GPU: {e}")

        return "unknown"

    def get_optimal_settings(self):
        """Retorna un diccionario con api y hwdec recomendados."""
        settings = {"api": "opengl", "hwdec": "auto"}

        if self.gpu_vendor == "nvidia":
            settings["api"] = "vulkan"
            settings["hwdec"] = "nvdec"
        elif self.gpu_vendor == "amd":
            settings["api"] = "vulkan"
            settings["hwdec"] = "vaapi"
        elif self.gpu_vendor == "intel":
            settings["api"] = "opengl"
            settings["hwdec"] = "vaapi"

        return settings
