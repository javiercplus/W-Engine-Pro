import Shell from 'gi://Shell';
import Meta from 'gi://Meta';
import * as Main from 'resource:///org/gnome/shell/ui/main.js';
import { Extension } from 'resource:///org/gnome/shell/extensions/extension.js';

export default class WEngineHelper extends Extension {
    enable() {
        this._windowCreatedId = global.display.connect('window-created', (display, window) => {
            this._setupWindow(window);
        });

        // 1. MONITOR OVERVIEW (Activities)
        this._overviewShowingId = Main.overview.connect('showing', () => this._onStateChanged());
        this._overviewHidingId = Main.overview.connect('hiding', () => this._onStateChanged());

        // 2. MONITOR MAXIMIZED WINDOWS
        this._windowMaximizedId = global.window_manager.connect('size-change', (wm, actor) => {
            this._onStateChanged();
        });

        // Scan existing windows
        this._scanWindows();
    }

    _scanWindows() {
        global.get_window_actors().forEach(actor => {
            if (actor && actor.meta_window) {
                this._setupWindow(actor.meta_window);
            }
        });
    }

    disable() {
        if (this._windowCreatedId) {
            global.display.disconnect(this._windowCreatedId);
            this._windowCreatedId = null;
        }
        if (this._overviewShowingId) Main.overview.disconnect(this._overviewShowingId);
        if (this._overviewHidingId) Main.overview.disconnect(this._overviewHidingId);
        if (this._windowMaximizedId) global.window_manager.disconnect(this._windowMaximizedId);
    }

    _onStateChanged() {
        // Here we could emit a DBus signal if we had a registered object,
        // but a simpler way is to update a property on the wallpaper window
        // that our Python code can poll via IPC if needed, or better:
        // For now, let's just ensure the wallpaper stays at the bottom.
        this._scanWindows();
    }

    _setupWindow(window) {
        if (!window) return;
        
        let title = window.get_title();
        if (title && title.includes('W-Engine-Gnome-Wallpaper')) {
            // 1. HIDE FROM TASKBAR AND ALT+TAB
            window.set_skip_taskbar(true);
            
            // 2. MOVE TO BACKGROUND LAYER
            Meta.later_add(Meta.LaterType.BEFORE_REDRAW, () => {
                window.make_below();
                
                let actor = window.get_compositor_private();
                if (actor) {
                    actor.set_layer(Shell.WindowLayer.BACKGROUND);
                }
            });
        }
    }
}
