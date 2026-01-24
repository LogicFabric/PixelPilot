import platform
import subprocess
import shutil
import tempfile
import os
import mss
import logging
from abc import ABC, abstractmethod
from typing import Tuple, Optional, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VisionStrategy(ABC):
    @abstractmethod
    def get_pixel(self, x: int, y: int) -> Optional[Tuple[int, int, int]]:
        """Get RGB color of a pixel at (x, y)."""
        pass

    @abstractmethod
    def search_color(self, region: Tuple[int, int, int, int], target_rgb: Tuple[int, int, int], tolerance: int = 10) -> Optional[Tuple[int, int]]:
        """
        Search for a color in a region (x, y, w, h). 
        Returns (x, y) if found, else None.
        """
        pass

class MSSStrategy(VisionStrategy):
    """Uses the `mss` library. Fast and cross-platform (X11/Win/Mac)."""
    def __init__(self):
        self.sct = mss.mss()
        logger.info("Initialized MSS Strategy")

    def get_pixel(self, x: int, y: int) -> Optional[Tuple[int, int, int]]:
        try:
            # bbox is {'top': y, 'left': x, 'width': 1, 'height': 1}
            monitor = {"top": y, "left": x, "width": 1, "height": 1}
            sct_img = self.sct.grab(monitor)
            # MSS returns BGRA, we want RGB.
            # pixel(0,0) returns (r, g, b) tuple depending on usage, but raw is B G R
            # sct_img.pixel(x, y) gets the pixel value. 
            # Note: grab() makes a new image relative to monitor, so 0,0 is correct for sct_img
            return sct_img.pixel(0, 0)
        except Exception as e:
            logger.error(f"MSS get_pixel failed: {e}")
            return None

    def search_color(self, region: Tuple[int, int, int, int], target_rgb: Tuple[int, int, int], tolerance: int = 10) -> Optional[Tuple[int, int]]:
        # This is expensive in python without optimization (numpy/opencv), 
        # but required by the interface.
        x, y, w, h = region
        monitor = {"top": y, "left": x, "width": w, "height": h}
        try:
            sct_img = self.sct.grab(monitor)
            # Naive iteration
            for py in range(h):
                for px in range(w):
                    p = sct_img.pixel(px, py)
                    if self._color_match(p, target_rgb, tolerance):
                        return (x + px, y + py)
        except Exception as e:
            logger.error(f"MSS search_color failed: {e}")
            return None
        return None

    def _color_match(self, c1, c2, tolerance):
        return sum(abs(c1[i] - c2[i]) for i in range(3)) <= tolerance

class CLIStrategy(VisionStrategy):
    """Fallback for systems like KDE Wayland where mss fails."""
    def __init__(self):
        self.cmd = self._detect_command()
        if not self.cmd:
            raise RuntimeError("No compatible CLI screenshot tool found (spectacle, grim, scrot).")
        logger.info(f"Initialized CLI Strategy using {self.cmd}")
        self.tmp_file = os.path.join(tempfile.gettempdir(), "pixelpilot_shot.png")

    def _detect_command(self):
        if shutil.which("spectacle"): return "spectacle"
        if shutil.which("grim"): return "grim"
        if shutil.which("scrot"): return "scrot"
        return None

    def _take_screenshot(self, region=None):
        """
        Take a screenshot and save to tmp_file. 
        Region is (x, y, w, h). If None, full screen (not implemented efficiently here).
        """
        # Delete old file
        if os.path.exists(self.tmp_file):
            os.remove(self.tmp_file)

        # Build command based on tool
        if self.cmd == "spectacle":
            # spectacle -b (background) -n (non-notify) -r (region) -o file
            if region:
                x, y, w, h = region
                # rect format: x,y,w,h
                cmd = ["spectacle", "-b", "-n", "-r", "-R", f"{x},{y},{w},{h}", "-o", self.tmp_file]
            else:
                cmd = ["spectacle", "-b", "-n", "-o", self.tmp_file]
        
        elif self.cmd == "grim":
            # grim -g "x,y wxh" file
            if region:
                x, y, w, h = region
                cmd = ["grim", "-g", f"{x},{y} {w}x{h}", self.tmp_file]
            else:
                cmd = ["grim", self.tmp_file]
        
        elif self.cmd == "scrot":
             # scrot -a x,y,w,h file
            if region:
                 x, y, w, h = region
                 cmd = ["scrot", "-a", f"{x},{y},{w},{h}", "--overwrite", self.tmp_file]
            else:
                 cmd = ["scrot", "--overwrite", self.tmp_file]
        
        try:
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except subprocess.CalledProcessError:
            return False

    def get_pixel(self, x: int, y: int) -> Optional[Tuple[int, int, int]]:
        # Take 1x1 screenshot
        if self._take_screenshot((x, y, 1, 1)):
            return self._read_color_from_file()
        return None

    def search_color(self, region: Tuple[int, int, int, int], target_rgb: Tuple[int, int, int], tolerance: int = 10) -> Optional[Tuple[int, int]]:
        if self._take_screenshot(region):
             return self._search_in_file(region, target_rgb, tolerance)
        return None

    def _read_color_from_file(self):
        from PIL import Image
        try:
            img = Image.open(self.tmp_file).convert('RGB')
            return img.getpixel((0, 0))
        except Exception as e:
            logger.error(f"Failed to read image: {e}")
            return None

    def _search_in_file(self, region, target_rgb, tolerance):
        from PIL import Image
        try:
            img = Image.open(self.tmp_file).convert('RGB')
            width, height = img.size
            pixels = img.load()
            for y in range(height):
                for x in range(width):
                    r, g, b = pixels[x, y]
                    if sum([abs(r - target_rgb[0]), abs(g - target_rgb[1]), abs(b - target_rgb[2])]) <= tolerance:
                        return (region[0] + x, region[1] + y)
        except Exception:
            pass
        return None

class VisionManager:
    """Auto-detects and manages the best vision strategy."""
    def __init__(self):
        self.strategy: Optional[VisionStrategy] = None
        self._init_strategy()

    def _init_strategy(self):
        # 1. Try MSS
        try:
            self.strategy = MSSStrategy()
            # Validating if MSS actually works (some Wayland setups don't error but return black)
            # For now, assume if no exception it's "okay" or user forced override.
            # Real robust check would be grabbing a pixel.
        except Exception:
            logger.warning("MSS failed, trying CLI strategy...")
            self.strategy = None

        if not self.strategy:
            try:
                self.strategy = CLIStrategy()
            except Exception as e:
                logger.error(f"All vision strategies failed: {e}")
                self.strategy = None

    def get_pixel(self, x: int, y: int) -> Optional[Tuple[int, int, int]]:
        if self.strategy:
            return self.strategy.get_pixel(x, y)
        return None
    
    def search_color(self, region, target, tolerance=10):
        if self.strategy:
            return self.strategy.search_color(region, target, tolerance)
        return None
