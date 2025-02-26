from psychopy import visual, logging, monitors
import win32api

class Screen:
    width:int
    height:int
    refresh_rate:int
    idx:int
    _device:object

    def __init__(self, idx:int, device_name:str):
        self.name = device_name
        device = win32api.EnumDisplaySettings(device_name, -1)
        self.width = device.PelsWidth
        self.height = device.PelsHeight
        self.refresh_rate = device.DisplayFrequency
        self._device = device
        self.idx = idx

    @property    
    def size(self) -> tuple[int, int]:
        return (self.width, self.height)

    def __repr__(self) -> str:
        info = f"Screen[{self.idx}]: {self.name}\n"
        for attr in dir(self._device):
            if(attr.startswith("__") == False):
                value = getattr(self._device, attr)
                info += f"  - {attr}={value}\n"
        return info
    
    def __str__(self) -> str:
        return self.__repr__()


class SystemScreen:
    screen_no:int
    def __init__(self):
        self.screen_no = len(win32api.EnumDisplayMonitors())
        self.screens:list[Screen] = []
        for idx, (handler,_,_) in enumerate(win32api.EnumDisplayMonitors()):
            info = win32api.GetMonitorInfo(handler)
            device_name = info['Device']
            screen = Screen(idx=idx, device_name=device_name)
            self.screens.append(screen)

    def get_screen(self, idx:int=0) -> Screen:
        screen = self.screens[idx]
        print(screen)
        return screen

class WindowBuilder:
    window: visual.Window
    def __init__(self, size:tuple[int,int]=None, refresh_rate:int=None, screen:Screen=None):
        window = None
        color = (1,1,1)
        if( isinstance(size, type(None)) == False):
            window = visual.Window(size=size, screen=0, units="pix", color=color)
            window.refreshThreshold = 1/refresh_rate
            
        elif( isinstance(screen, type(None)) == False):
            window = visual.Window(size=screen.size, screen=screen.idx, fullscr=True, units='pix', color=color)
            window.refreshThreshold = 1/screen.refresh_rate
        # This enable `drop frame` report
        # https://psychopy.org/general/timing/detectingFrameDrops.html#detectdroppedframes
        window.recordFrameIntervals = True
        self.window = window
        logging.console.setLevel(logging.WARNING)

    def get_window(self) -> visual.window:
        return self.window

    def report(self):
        print('Overall, %i frames were dropped.' % self.window.nDroppedFrames)



# # build monitors
# mon = monitors.Monitor("Gigabyte")
# mon.save()

if __name__ == "__main__":
    # pass
    # ### Method 1: Create window with Screen object
    # # Helper class that detect your screen
    # sys_screen = SystemScreen()
    # # Create window object with helper class
    # win_builder = WindowBuilder(screen=sys_screen.get_screen(0))

    ### Method 2: create window manually
    win_builder = WindowBuilder(size=(400,400), refresh_rate=60)
    window = win_builder.get_window()
    win_builder.report()
