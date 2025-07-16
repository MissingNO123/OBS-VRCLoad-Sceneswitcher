# OBS Scene Switcher for VRChat Loading Screens
# vrcload-sceneswitcher.py
# Automatically switches OBS scenes when on the VRChat loading screen.
# Monitors the VRChat log file for specific events to determine when to switch scenes.
# (c) 2025 MissingNO123

import obspython as S # type: ignore
import os
import psutil


class SceneSwitcher:
    def __init__(self, loading_scene=None, default_scene=None, enabled=True):
        self.loading_scene = loading_scene
        self.default_scene = default_scene
        self.last_scene = None
        self.enabled = enabled

    def _set_current_scene(self, scene_name=None):
        if not self.enabled:
            print("Scene switching is disabled.")
            return
        scenes = S.obs_frontend_get_scenes()
        for scene in scenes:
            name = S.obs_source_get_name(scene)
            if name == scene_name:
                S.obs_frontend_set_current_scene(scene)
                break
        else:
            print(f"Scene '{scene_name}' not found.")
        S.source_list_release(scenes)
    
    def switch_to_loading_scene(self):
        self.last_scene = S.obs_frontend_get_current_scene()
        if self.loading_scene:
            print(f"Switching to loading scene: {self.loading_scene}")
            self._set_current_scene(self.loading_scene)
        else:
            print("No loading scene set.")
    
    def switch_to_default_scene(self):
        if self.default_scene:
            if self.default_scene == "Last Scene":
                if (self.last_scene is None):
                    print("No last scene to switch to.")
                    return
                print("Switching to last scene.")
                self._set_current_scene(S.obs_source_get_name(self.last_scene))
            else:
                print(f"Switching to default scene: {self.default_scene}")
                self._set_current_scene(self.default_scene)
        else:
            print("No default scene set.")


class LogWatcher: 
    def __init__(self, log_folder, update_interval_ms=1000):
        self.log_folder = log_folder
        self.update_interval_ms = update_interval_ms
        self.log_file = None
        self._refresh_log_file_path()
        self.last_position = 0
        self.first_run = True
        self.vrchat_running = False
        if not self.log_file:
            print("Log file not found. Please check the log folder path.")

    # read new lines from log file since the last position
    def _read(self):
        with open(self.log_file, 'r', encoding='utf-8') as file:
            file.seek(self.last_position)
            new_lines = file.readlines()
            self.last_position = file.tell()
            return new_lines

    # determine most recently modified log file
    def _refresh_log_file_path(self):
        log_files = [f for f in os.listdir(self.log_folder) if f.startswith("output_log")]
        log_files.sort(key=lambda x: os.path.getmtime(os.path.join(self.log_folder, x)), reverse=True)
        if log_files:
            log_file = os.path.join(self.log_folder, log_files[0])
            if self.log_file != log_file:
                self.log_file = log_file
                self.last_position = 0
    
    # determine if we're about to enter or leave a loading screen based on certain behaviour events
    # "Destination requested" is used as other events fire too late, 
    # now that worlds instantly start loading in the background on first click.
    # might honestly change this to an even earlier one if needed
    def _check_for_world_transition(self):
        if not self.vrchat_running:
            return
        self._refresh_log_file_path()
        if not self.log_file:
            return
        new_lines = self._read()
        if self.first_run:
            self.first_run = False
            if new_lines:
                print(f"Initial log file read: {self.log_file}")
            return
        if new_lines:
            for line in new_lines:
                if "[Behaviour] Finished entering world." in line:
                    print(f"World Entered")
                    ss.switch_to_default_scene()
                elif "[Behaviour] Destination requested: " in line:
                    print(f"World Left")
                    ss.switch_to_loading_scene()
    
    # watch the log file for changes periodically
    def watch(self):
        if not self.log_file:
            print("Log file not found. Please check the log folder path.")
            return

        print(f"Watching log file: {self.log_file}")
        
        S.timer_remove(check_for_world_transition)
        S.timer_add(check_for_world_transition, self.update_interval_ms) 
        # calls a module-level function, as OBS crashes if we try to call an instance method from a timer


ss = None
log_watcher = None


# Module-level functions for timers
def check_for_world_transition():
    if log_watcher:
        log_watcher._check_for_world_transition()


def check_vrchat_running():
    if log_watcher:
        for proc in psutil.process_iter(['pid', 'name']):
            if proc.info['name'].lower() == 'vrchat.exe':
                log_watcher.vrchat_running = True
                return True
        log_watcher.vrchat_running = False
        return False


def script_load(settings):
    global ss, log_watcher
    ss = SceneSwitcher(
        S.obs_data_get_string(settings, "scene"),
        S.obs_data_get_string(settings, "default_scene"),
        S.obs_data_get_bool(settings, "enabled")
    )
    log_watcher = LogWatcher(S.obs_data_get_string(settings, "log_folder"))
    log_watcher.update_interval_ms = S.obs_data_get_int(settings, "update_interval_ms")
    log_watcher.watch()
    S.timer_add(check_vrchat_running, 5000)


def script_defaults(settings):
    if os.getenv("OS") == "Windows_NT":  # Windows path
        log_folder = f"{os.getenv('LOCALAPPDATA')}Low\\VRChat\\VRChat\\"
    else:  # Linux path (Proton)
        log_folder = f"{os.getenv('HOME')}/.local/share/Steam/steamapps/compatdata/438100/pfx/drive_c/users/steamuser/AppData/LocalLow/VRChat/VRChat/"
    S.obs_data_set_default_string(settings, "log_folder", log_folder)
    S.obs_data_set_default_int(settings, "update_interval_ms", 1500)
    S.obs_data_set_default_bool(settings, "enabled", True)


def script_update(settings):
    ss.loading_scene = S.obs_data_get_string(settings, "scene")
    ss.default_scene = S.obs_data_get_string(settings, "default_scene")
    ss.enabled = S.obs_data_get_bool(settings, "enabled")
    log_watcher.log_folder = S.obs_data_get_string(settings, "log_folder")
    log_watcher.update_interval_ms = S.obs_data_get_int(settings, "update_interval_ms")
    S.timer_remove(check_for_world_transition)
    S.timer_add(check_for_world_transition, log_watcher.update_interval_ms)


def script_unload():
    global log_watcher, ss
    S.timer_remove(check_for_world_transition)
    S.timer_remove(check_vrchat_running)
    log_watcher = None
    ss = None


def script_properties():  # ui
    props = S.obs_properties_create()
    loading_scene_selector = S.obs_properties_add_list(
        props,
        "scene",
        "Loading Scene",
        S.OBS_COMBO_TYPE_EDITABLE,
        S.OBS_COMBO_FORMAT_STRING,
    )

    default_scene_selector = S.obs_properties_add_list(
        props,
        "default_scene",
        "Default Scene",
        S.OBS_COMBO_TYPE_EDITABLE,
        S.OBS_COMBO_FORMAT_STRING,
    )

    log_folder_prop = S.obs_properties_add_text(
        props, "log_folder", "Log Folder Path", S.OBS_TEXT_DEFAULT
    )

    update_interval_ms_prop = S.obs_properties_add_int(
        props, "update_interval_ms", "Update Interval (ms)", 500, 10000, 100
    )

    enabled_prop = S.obs_properties_add_bool(
        props, "enabled", "Enable Scene Switcher"
    )

    S.obs_property_list_add_string(default_scene_selector, "Last Scene", "Last Scene")

    scenes = S.obs_frontend_get_scenes()
    for scene in scenes:
        name = S.obs_source_get_name(scene)
        S.obs_property_list_add_string(loading_scene_selector, name, name)
        S.obs_property_list_add_string(default_scene_selector, name, name)
    S.source_list_release(scenes)

    return props

def script_description():
    return "Automatically switches scenes when entering a loading screen in VRChat, and switches back when done.\nThe script will monitor the VRChat log file for events, so make sure logging is enabled."